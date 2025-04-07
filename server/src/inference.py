import torch
import numpy as np
from pathlib import Path
from typing import Union
from sqlalchemy.orm import Session
from db import get_db
from models import Object, Point, Frame, Mask
from utils import serialize_mask, logger
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
            "tiny": ("../sam2/checkpoints/sam2.1_hiera_tiny.pt",
                     "/home/nico/autolabel/sam2/sam2/configs/sam2.1/sam2.1_hiera_t.yaml"),
            "small": ("../sam2/checkpoints/sam2.1_hiera_small.pt",
                      "/home/nico/autolabel/sam2/sam2/configs/sam2.1/sam2.1_hiera_s.yaml"),
            "base-plus": ("../sam2/checkpoints/sam2.1_hiera_base_plus.pt",
                          "/home/nico/autolabel/sam2/sam2/configs/sam2.1/sam2.1_hiera_b+.yaml"),
            "large": ("../sam2/checkpoints/sam2.1_hiera_large.pt",
                      "/home/nico/autolabel/sam2/sam2/configs/sam2.1/sam2.1_hiera_l.yaml"),
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

    def segment_object(self, object_id: int, start_frame_idx: int, db: Session = next(get_db())) -> np.ndarray:
        """
        Segment an object using SAM2 and save the mask to the database.

        Args:
            object_id: ID of the object to segment
            start_frame_idx: Frame index to segment on
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

        # Check if the frame exists in the database
        current_frame = db.query(Frame).filter_by(
            video_id=current_object.video_id, frame_number=start_frame_idx).first()
        if not current_frame:
            raise ValueError(
                f"Frame with ID {start_frame_idx} not found in database.")

        # Prepare data for SAM2
        points_array = np.array([[p.x, p.y] for p in points], dtype=np.float32)
        labels_array = np.array([p.label for p in points], dtype=np.int32)

        logger.info(
            f"Performing segmentation for object {object_id} on frame {start_frame_idx}")
        # Perform segmentation
        _, _, out_mask_logits = self.predictor.add_new_points_or_box(
            inference_state=self.inference_state,
            start_frame_idx=start_frame_idx,
            obj_id=object_id,
            points=points_array,
            labels=labels_array,
        )

        # Create mask and save to database
        mask = (out_mask_logits[0] > 0.0).cpu().numpy().squeeze()
        mask_blob = serialize_mask(mask)

        # Check if mask already exists and update it, or create new one
        existing_mask = db.query(Mask).filter_by(
            object_id=object_id, frame_id=current_frame.id).first()

        if existing_mask:
            existing_mask.mask = mask_blob
            logger.info(
                f"Updated existing mask for object {object_id}, frame {start_frame_idx}")
        else:
            new_mask = Mask(
                object_id=object_id,
                frame_id=current_frame.id,
                mask=mask_blob
            )
            db.add(new_mask)
            logger.info(
                f"Created new mask for object {object_id}, frame {start_frame_idx}")

        db.commit()
        return mask

    def propagate_in_video(self, video_id: int, start_frame_idx: int, db: Session = next(get_db())) -> None:
        frames = db.query(Frame).filter_by(video_id=video_id).all()
        if not frames:
            raise ValueError(f"No frames found for video ID {video_id}.")

        # Get the video object from database using video_id
        video = db.query(Object).filter_by(id=video_id).first()
        if not video:
            logger.error(f"Video with ID {video_id} not found in database")
            raise ValueError(
                f"Video with ID {video_id} not found in database.")

        # Get frame with the start_frame_idx to find the frames directory
        start_frame = db.query(Frame).filter_by(
            video_id=video_id, frame_number=start_frame_idx).first()
        if not start_frame:
            raise ValueError(
                f"No frame with index {start_frame_idx} found for video ID {video_id}.")

        # Extract frames directory path from the start frame's file path
        # The file path is like "/path/to/frames_dir/0001.jpg", so we need the directory part
        frames_dir = Path(start_frame.file_path).parent

        # Initalize SAM2 state using frames directory
        self.initialize_state(frames_dir)

        # Get objects from database given the video_id
        objects = db.query(Object).filter_by(video_id=video_id).all()
        if not objects:
            raise ValueError(f"No objects found for video ID {video_id}.")

        for obj in objects:
            # Get all points for this object
            points = db.query(Point).filter_by(object_id=obj.id).all()
            if not points:
                raise ValueError(f"No points found for object ID {obj.id}.")

            # Prepare data for SAM2
            points_array = np.array([[p.x, p.y]
                                    for p in points], dtype=np.float32)
            labels_array = np.array([p.label for p in points], dtype=np.int32)
            self.predictor.add_new_points_or_box(
                inference_state=self.inference_state,
                start_frame_idx=start_frame_idx,
                obj_id=obj.id,
                points=points_array,
                labels=labels_array,
            )

        for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(
            inference_state=self.inference_state,
            start_frame_idx=start_frame_idx,
            max_frame_num_to_track=None,
            reverse=True
        ):
            for i, out_obj_id in enumerate(out_obj_ids):
                # Create mask and save to database
                mask = (out_mask_logits[i] > 0.0).cpu().numpy().squeeze()
                mask_blob = serialize_mask(mask)

                # Check if mask already exists and update it, or create new one
                existing_mask = db.query(Mask).filter_by(
                    object_id=out_obj_id, frame_id=out_frame_idx).first()

                if existing_mask:
                    existing_mask.mask = mask_blob
                    logger.info(
                        f"Updated existing mask for object {out_obj_id}, frame {out_frame_idx}")
                else:
                    new_mask = Mask(
                        object_id=out_obj_id,
                        frame_id=out_frame_idx,
                        mask=mask_blob
                    )
                    db.add(new_mask)
                    logger.info(
                        f"Created new mask for object {out_obj_id}, frame {out_frame_idx}")
