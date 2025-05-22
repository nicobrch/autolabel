import torch
import numpy as np
import cv2
import subprocess
import shutil  # Add this import for copying files
from pathlib import Path
from typing import Union
from sqlalchemy.orm import Session
from sqlalchemy import exists  # Add this import
from db import get_db
from models import Object, Point, Frame, Mask, Video
from utils import construct_video_from_inference_frames, get_frames_list, public_frames_base_dir_with_video_name, public_frames_inference_dir_with_video_name, serialize_mask, logger, hex_to_rgb
from sam2.build_sam import build_sam2_video_predictor


class InferenceAPI:
    """Class to handle the SAM2 predictor and inference state."""

    def __init__(self, checkpoint: str = "small"):
        """
        Initialize the InferenceAPI with a SAM2 model.

        Args:
            checkpoint: Model size to use ('tiny', 'small', 'base-plus', or 'large')
        """
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")
        self.predictor = None
        self.inference_state = None
        self.checkpoint = checkpoint
        self._initialize_predictor()

    def _initialize_predictor(self):
        """Initialize the SAM2 predictor with the specified checkpoint."""

        model_map = {
            "tiny": (r"C:\Users\Nico\Develop\sam2\checkpoints\sam2.1_hiera_tiny.pt",
                     r"C:\Users\Nico\Develop\sam2\sam2\configs\sam2.1\sam2.1_hiera_t.yaml"),
            "small": (r"C:\Users\Nico\Develop\sam2\checkpoints\sam2.1_hiera_small.pt",
                      r"C:\Users\Nico\Develop\sam2\sam2\configs\sam2.1\sam2.1_hiera_s.yaml"),
            "base-plus": (r"C:\Users\Nico\Develop\sam2\checkpoints\sam2.1_hiera_base_plus.pt",
                          r"C:\Users\Nico\Develop\sam2\sam2\configs\sam2.1\sam2.1_hiera_b+.yaml"),
            "large": (r"C:\Users\Nico\Develop\sam2\checkpoints\sam2.1_hiera_large.pt",
                      r"C:\Users\Nico\Develop\sam2\sam2\configs\sam2.1\sam2.1_hiera_l.yaml"),
        }

        if self.checkpoint not in model_map:
            valid_options = ', '.join(model_map.keys())
            raise ValueError(
                f"Invalid checkpoint name: {self.checkpoint}. Available options are: {valid_options}")

        checkpoint_path, config_path = model_map[self.checkpoint]
        logger.info(
            f"Initializing SAM2 predictor with {self.checkpoint} model on {self.device}")

        if self.device.type == "cpu":
            self.predictor = build_sam2_video_predictor(
                config_path, checkpoint_path, device=self.device)
        else:
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            with torch.autocast("cuda", dtype=torch.bfloat16):
                self.predictor = build_sam2_video_predictor(
                    config_path, checkpoint_path, device=self.device)

    def initialize_state(self, frames_dir: Union[str, Path]) -> None:
        """
        Initialize the SAM2 predictor state with frames.

        Args:
            frames_dir: Directory containing video frames
        """
        frames_dir = Path(frames_dir)
        if not frames_dir.exists():
            raise FileNotFoundError(
                f"Frames directory '{frames_dir}' does not exist.")

        logger.info(f"Initializing SAM2 state with frames from {frames_dir}")
        self.inference_state = self.predictor.init_state(
            video_path=str(frames_dir))
        self.predictor.reset_state(self.inference_state)

    def reset_state(self) -> None:
        """
        Reset the SAM2 predictor state.
        """
        if self.inference_state is not None:
            logger.info("Resetting SAM2 state")
            self.predictor.reset_state(self.inference_state)
            self.inference_state = None
        else:
            logger.warning("No inference state to reset.")

    def segment_object(self, object_id: int, db: Session = next(get_db())) -> np.ndarray:
        """
        Segment an object using SAM2 and save the mask to the database.
        Always uses the first frame of the video.

        Args:
            object_id: ID of the object to segment
            db: Database session

        Returns:
            Segmentation mask as numpy array
        """
        if self.inference_state is None:
            raise ValueError(
                "Inference state not initialized. Call initialize_state first.")

        # Get object from DB
        current_object = db.query(Object).filter_by(id=object_id).first()
        if not current_object:
            raise ValueError(
                f"Object with ID {object_id} not found in database.")

        # Get all points for this object
        points = db.query(Point).filter_by(object_id=object_id).all()
        if not points:
            raise ValueError(f"No points found for object ID {object_id}.")

        # Get the first frame for this video (we only store one frame)
        current_frame = db.query(Frame).filter_by(
            video_id=current_object.video_id).first()
        if not current_frame:
            raise ValueError(
                f"No frames found for video ID {current_object.video_id}.")

        # Prepare data for SAM2
        points_array = np.array([[p.x, p.y] for p in points], dtype=np.float32)
        labels_array = np.array([p.label for p in points], dtype=np.int32)

        # Always use frame index 0 since we're working with the first frame
        logger.info(
            f"Performing segmentation for object {object_id} on first frame")

        # Perform segmentation
        _, _, out_mask_logits = self.predictor.add_new_points_or_box(
            inference_state=self.inference_state,
            frame_idx=0,  # First frame
            obj_id=object_id,
            points=points_array,
            labels=labels_array,
        )

        # Create mask and save to database
        mask = (out_mask_logits[0] > 0.0).cpu().numpy().squeeze()
        mask_blob = serialize_mask(mask)

        # Check if mask already exists and update it, or create new one
        existing_mask = db.query(Mask).filter_by(
            object_id=object_id).first()

        if existing_mask:
            existing_mask.mask = mask_blob
            logger.info(
                f"Updated existing mask for object {object_id}, first frame")
        else:
            new_mask = Mask(
                object_id=object_id,
                mask=mask_blob
            )
            db.add(new_mask)
            logger.info(
                f"Created new mask for object {object_id}, first frame")

        db.commit()
        return mask

    def propagate_in_video(self, video_id: int, db: Session = next(get_db())) -> str:
        """
        Propagate masks for all objects through video frames.
        Instead of storing masks in database, directly draws them on frames
        and creates a video file.

        Args:
            video_id: ID of the video
            db: Database session

        Returns:
            Path to the created video file
        """
        # Get the video from database
        video = db.query(Video).filter_by(id=video_id).first()
        if not video:
            raise ValueError(
                f"Video with ID {video_id} not found in database.")

        # Get the first (and only) frame for this video
        frame = db.query(Frame).filter_by(video_id=video_id).first()
        if not frame:
            raise ValueError(f"No frames found for video ID {video_id}.")

        # Get all objects for this video that have points
        # Fix: Use SQLAlchemy's exists() function instead of db.exists()
        objects_with_points = db.query(Object).filter(
            Object.video_id == video_id,
            exists().where(Point.object_id == Object.id)
        ).all()

        if not objects_with_points:
            raise ValueError(
                f"No objects with points found for video ID {video_id}.")

        # Extract frames directory path from the frame's file path
        video_name = Path(video.file_path).stem
        base_frames_dir = public_frames_base_dir_with_video_name(video_name)
        inference_frames_dir = public_frames_inference_dir_with_video_name(
            video_name)

        # Ensure inference directory exists
        inference_frames_dir.mkdir(parents=True, exist_ok=True)

        # Clear any existing frames in the inference directory
        for file in inference_frames_dir.glob("*.jpg"):
            file.unlink()

        # Get list of all original frames
        base_frames = get_frames_list(base_frames_dir)

        # Initialize SAM2 state using base frames directory
        self.initialize_state(base_frames_dir)

        # Process each object, adding its points to the predictor
        for obj in objects_with_points:
            # Get all points for this object
            points = db.query(Point).filter_by(object_id=obj.id).all()
            if not points:
                logger.warning(
                    f"No points found for object ID {obj.id}, skipping")
                continue

            # Prepare data for SAM2
            points_array = np.array([[p.x, p.y]
                                    for p in points], dtype=np.float32)
            labels_array = np.array([p.label for p in points], dtype=np.int32)

            # Add points to the predictor
            self.predictor.add_new_points_or_box(
                inference_state=self.inference_state,
                frame_idx=0,  # First frame
                obj_id=obj.id,
                points=points_array,
                labels=labels_array,
            )

        # Propagate masks through video frames
        for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(
            inference_state=self.inference_state,
            max_frame_num_to_track=None,  # Process all frames
            reverse=False  # Forward direction
        ):
            # Get the corresponding original frame
            try:
                original_frame_path = base_frames[out_frame_idx]
            except IndexError:
                logger.warning(
                    f"Frame index {out_frame_idx} out of range, skipping")
                continue

            # Read the original frame
            frame_img = cv2.imread(str(original_frame_path))
            if frame_img is None:
                logger.warning(
                    f"Could not read frame {original_frame_path}, skipping")
                continue

            # Create a copy for overlay
            overlay = frame_img.copy()

            # Process each object's mask for this frame
            for i, obj_id in enumerate(out_obj_ids):
                # Convert mask logits to binary mask
                mask = (out_mask_logits[i] > 0.0).cpu().numpy().squeeze()

                # Get the object to retrieve its color
                obj = next(
                    (o for o in objects_with_points if o.id == obj_id), None)
                if not obj:
                    continue

                # Convert hex color to BGR (for OpenCV)
                try:
                    r, g, b = hex_to_rgb(obj.color)
                    color = (b, g, r)  # BGR format for OpenCV
                except ValueError:
                    # Use default green if color format is invalid
                    color = (0, 255, 0)

                # Create color mask
                color_mask = np.zeros_like(frame_img)
                color_mask[mask] = color

                # Overlay with transparency
                cv2.addWeighted(color_mask, 0.5, overlay, 1, 0, overlay)

            # Save the frame with masks to inference directory
            output_frame_path = inference_frames_dir / original_frame_path.name
            cv2.imwrite(str(output_frame_path), overlay)
            logger.info(f"Saved inference frame {output_frame_path}")

        # Create video from inference frames
        construct_video_from_inference_frames(
            video_id=video_id,
            model_name=self.checkpoint,
            db=db
        )

        # Reset the predictor state
        self.reset_state()
        logger.info("Reset SAM2 predictor state after video processing")
        return str(inference_frames_dir)
