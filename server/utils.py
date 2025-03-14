import os
import sys
import json
import subprocess
import torch
import numpy as np
import pickle
import cv2
from pathlib import Path
from sqlalchemy.orm import Session
from db import get_db, create_tables
from models import Object, Point, Frame, Mask
from sam2.build_sam import build_sam2_video_predictor


def time_to_seconds(time_str: str) -> float:
    """
    Convert time string in format "HH:MM:SS.MS" to seconds (float).
    Returns seconds as float or raises ValueError for invalid format.
    """
    try:
        # Split by colons to get hours, minutes, seconds
        parts = time_str.split(":")

        if len(parts) != 3:
            raise ValueError("Time format must be HH:MM:SS.MS")

        hours = int(parts[0])
        minutes = int(parts[1])

        # Handle seconds which may contain milliseconds
        seconds = float(parts[2])

        # Calculate total seconds
        total_seconds = hours * 3600 + minutes * 60 + seconds

        if total_seconds < 0:
            raise ValueError("Time cannot be negative")

        return total_seconds

    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid time format. Must be HH:MM:SS.MS: {e}")


def extract_video_metadata(video_path: str):
    # Get video metadata using ffprobe
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,duration",
            "-of", "json",
            str(video_path)
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)

        # Extract metadata
        stream = metadata.get("streams", [{}])[0]
        width = int(stream.get("width", 0))
        height = int(stream.get("height", 0))

        # Parse framerate (usually in the form "24/1")
        fps = 0
        if "r_frame_rate" in stream:
            rate_parts = stream["r_frame_rate"].split("/")
            if len(rate_parts) == 2 and int(rate_parts[1]) != 0:
                fps = float(int(rate_parts[0]) / int(rate_parts[1]))

        # Get duration
        duration = float(stream.get("duration", 0))

        # Get file size
        file_size = os.path.getsize(video_path)

    except (subprocess.SubprocessError, json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Error extracting video metadata: {e}", file=sys.stderr)
        width, height, fps, duration = 0, 0, 0, 0
        file_size = os.path.getsize(
            video_path) if os.path.exists(video_path) else 0

    return {
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
        "file_size": file_size
    }


def get_frames_list(frames_dir: str) -> list:
    """
    Get a list of frames from the specified directory.
    Args:
        frames_dir (str): Path to the directory containing frames.
    Returns:
        List of frame file paths.
    """
    # Convert to Path object
    frames_dir = Path(frames_dir)

    # Check if the directory exists
    if not frames_dir.exists():
        raise FileNotFoundError(
            f"Frames directory '{frames_dir}' does not exist.")

    # Get the list of frames
    frames = sorted(frames_dir.glob("*.jpg"))
    if not frames:
        raise FileNotFoundError(
            f"No frames found in directory '{frames_dir}'.")
    return frames


def extract_frames_at_frame_step(video_path: str, frame_step: int, db: Session = next(get_db())):
    """"
    "Extract frames from a video at a specified frame step using ffmpeg."
    Args:
        video_path (str): Path to the video file.
        frame_step (int): Step size for frame extraction. For example, if
                          frame_step is 5, every 5th frame will be extracted.
    """
    # Check if the video file exists
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file '{video_path}' not found.")

    # Check if the video exists on the database
    video = db.query(Object).filter_by(file_path=video_path).first()
    if not video:
        raise ValueError(f"Video '{video_path}' not found in database.")

    # Create base frames directory if it doesn't exist
    base_frames_dir = Path("data/frames")
    base_frames_dir.mkdir(exist_ok=True)

    # Create video frames directory if it doesn't exist
    video_name = Path(video_path).stem
    frames_dir = base_frames_dir / video_name / \
        "original"  # e.g. "data/frames/video_name/original"
    frames_dir.mkdir(exist_ok=True)

    # Remove existing frames in the directory
    for file in frames_dir.glob("*.jpg"):
        file.unlink()

    # Remove existing frames from the database, if any
    db.query(Frame).filter_by(video_id=video.id).delete()
    db.commit()
    db.refresh(video)

    try:
        # Prepare ffmpeg command to extract frames
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vsync", "vfr",
            "-vf", f"select='not(mod(n,{frame_step}))'",
            str(frames_dir / "%04d.jpg"),
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

        # Check if frames were extracted
        if not any(frames_dir.glob("*.jpg")):
            raise ValueError(
                f"No frames were extracted from video '{video_path}'.")

        # Store frame data in the database
        frames = get_frames_list(frames_dir)
        for frame in frames:
            # Create a new Frame object
            new_frame = Frame(
                video_id=video.id,
                frame_number=int(frame.stem),
                file_path=str(frame)
            )
            db.add(new_frame)
            db.commit()
            db.refresh(new_frame)

        print(
            f"Extracted {len(frames)} frames from '{video_path}' to '{frames_dir}'.")

        return frames_dir
    except (subprocess.SubprocessError, ValueError, KeyError) as e:
        print(f"Error extracting frames: {e}", file=sys.stderr)


def create_object(video_id: int, name: str):
    """
    Create a new object in the database.

    Args:
        clip_id (int): ID of the clip to which the object belongs.
        name (str): Name of the object.

    Returns:
        Object: The created object instance.
    """

    # Generate a random color in RGB format
    r = np.random.randint(0, 255)
    g = np.random.randint(0, 255)
    b = np.random.randint(0, 255)
    # Convert to hex string format (#RRGGBB)
    color = f"#{r:02x}{g:02x}{b:02x}"

    new_object = Object(
        video_id=video_id,
        name=name,
        color=color,  # Default color, can be changed later
        mask=None
    )

    db = next(get_db())
    db.add(new_object)
    db.commit()
    db.refresh(new_object)

    return new_object


def build_sam_predictor(checkpoint: str):
    model_map = {
        "tiny": ("../sam2/checkpoints/sam2.1_hiera_tiny.pt", "//home/nico/autolabel/sam2/sam2/configs/sam2.1/sam2.1_hiera_t.yaml"),
        "small": ("../sam2/checkpoints/sam2.1_hiera_small.pt", "/home/nico/autolabel/sam2/sam2/configs/sam2.1/sam2.1_hiera_s.yaml"),
        "base-plus": ("../sam2/checkpoints/sam2.1_hiera_base_plus.pt", "//home/nico/autolabel/sam2/sam2/configs/sam2.1/sam2.1_hiera_b+.yaml"),
        "large": ("../sam2/checkpoints/sam2.1_hiera_large.pt", "//home/nico/autolabel/sam2/sam2/configs/sam2.1/sam2.1_hiera_l.yaml"),
    }

    if checkpoint not in model_map:
        raise ValueError(
            f"Invalid checkpoint name: {checkpoint}. Available options are: {', '.join(model_map.keys())}")
    checkpoint_path, config_path = model_map[checkpoint]

    if not torch.cuda.is_available():
        device = torch.device("cpu")
        return build_sam2_video_predictor(
            config_path, checkpoint_path, device=device)
    else:
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        device = torch.device("cuda")
        torch.autocast("cuda", dtype=torch.bfloat16).__enter__()
        return build_sam2_video_predictor(
            config_path, checkpoint_path, device=device)


def initialize_sam_predictor_state(frames_dir: str, sam_predictor):
    """
    Initialize the SAM2 predictor state with the frames.

    Args:
        frames_dir (str): Path to the directory containing frames.
        sam_predictor: SAM2 predictor instance.
    """
    # Check if the directory exists
    frames_dir = Path(frames_dir)
    if not frames_dir.exists():
        raise FileNotFoundError(
            f"Frames directory '{frames_dir}' does not exist.")

    # Initialize SAM2 predictor state
    inference_state = sam_predictor.init_state(video_path=str(frames_dir))
    sam_predictor.reset_state(inference_state)


def serialize_mask(mask):
    return pickle.dumps(mask)


def deserialize_mask(mask_blob):
    return pickle.loads(mask_blob)


def segmentate_object(object_id: int, frame_idx: int, sam_predictor, inference_state, db: Session = next(get_db())):
    """
    Segmentate an object using SAM2 and save the mask to the database.

    Args:
        object_id (int): ID of the object to segment.
        sam_predictor: SAM2 predictor instance.
        db (Session, optional): Database session. If None, gets a new session.
    """
    # Get object from DB
    current_object = db.query(Object).filter_by(id=object_id).first()
    if not current_object:
        raise ValueError(f"Object with ID {object_id} not found in database.")

    # Get all points for this object
    points = db.query(Point).filter_by(object_id=object_id).all()
    if not points:
        raise ValueError(f"No points found for object ID {object_id}.")

    # Check if the frame exists on the database
    current_frame = db.query(Frame).filter_by(
        video_id=current_object.video_id, frame_number=frame_idx).first()
    if not current_frame:
        raise ValueError(f"Frame with ID {frame_idx} not found in database.")

    # Prepare data for SAM2
    points_array = np.array([[p.x, p.y] for p in points], dtype=np.float32)
    labels_array = np.array([p.label for p in points], dtype=np.int32)

    # Perform segmentation
    _, _, out_mask_logits = sam_predictor.add_new_points_or_box(
        inference_state=inference_state,
        frame_idx=frame_idx,
        obj_id=object_id,
        points=points_array,
        labels=labels_array,
    )

    # Save the mask to the database as a binary blob
    mask = (out_mask_logits[0] > 0.0).cpu().numpy().squeeze()
    mask_blob = serialize_mask(mask)
    new_mask = Mask(
        object_id=object_id,
        frame_id=current_frame.id,
        mask=mask_blob
    )
    db.add(new_mask)
    db.commit()
    db.refresh(new_mask)
    return mask


def create_point(x: int, y: int, positive: int, object_id: int, db: Session = next(get_db())):
    # Get object from DB
    current_object = db.query(Object).filter_by(id=object_id).first()
    if not current_object:
        raise ValueError(f"Object with ID {object_id} not found in database.")

    # Append the new point to the existing points
    new_point = Point(
        object_id=object_id,
        x=x,    # X coordinate of the point
        y=y,    # Y Coordinate of the point
        label=positive  # 1 for positive, 0 for negative
    )
    db.add(new_point)
    db.commit()
    db.refresh(new_point)


def remove_point(point_id: int, db: Session = next(get_db())):
    # Get point from DB
    point = db.query(Point).filter_by(id=point_id).first()
    if not point:
        raise ValueError(f"Point with ID {point_id} not found in database.")

    # Delete the point
    db.delete(point)
    db.commit()
    db.refresh(point)


def draw_objects_masks_on_frame(frame_path: str, object_ids: list, output_dir: str, db: Session = next(get_db())):
    """
    Draw object masks onto a frame and save as new image.

    Args:
        frame_path (str): Path to the frame image
        object_ids (list): List of object IDs to draw masks for
        output_dir (str): Directory path to save the output image.
        db (Session, optional): Database session. If None, gets a new session.

    Returns:
        str: Path to the saved masked image
    """

    # Check if the output directory exists, if not create it
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Read the frame
    frame = cv2.imread(str(frame_path))
    if frame is None:
        raise FileNotFoundError(f"Could not read frame from {frame_path}")

    # Create a copy for overlay
    overlay = frame.copy()

    # For each object ID
    for obj_id in object_ids:
        # Get object from database
        obj = db.query(Object).filter_by(id=obj_id).first()
        if not obj:
            continue

        # Get all points for this object
        points = db.query(Point).filter_by(object_id=obj_id).all()

        # Draw mask if available
        if obj.mask:
            # Deserialize the mask
            mask = deserialize_mask(obj.mask)

            # Parse the color from hex string (format: "#RRGGBB")
            if obj.color and obj.color.startswith('#') and len(obj.color) == 7:
                # Convert hex to BGR (OpenCV uses BGR format)
                r = int(obj.color[1:3], 16)
                g = int(obj.color[3:5], 16)
                b = int(obj.color[5:7], 16)
                color = (b, g, r)  # BGR format for OpenCV
            else:
                # Fallback to a default color if the stored color is invalid
                color = (0, 255, 0)  # Green in BGR

            # Apply mask with color
            color_mask = np.zeros_like(frame)
            color_mask[mask] = color

            # Overlay with transparency
            cv2.addWeighted(color_mask, 0.25, overlay, 0.75, 0, overlay)

        # Draw all points for this object
        for point in points:
            # Green for positive points (label=1), Red for negative points (label=0)
            point_color = (0, 255, 0) if point.label == 1 else (
                0, 0, 255)  # BGR format

            # Draw the point as a circle
            cv2.circle(overlay, (point.x, point.y), 5,
                       point_color, -1)  # -1 means filled circle

            # Draw a small border around the circle to improve visibility
            cv2.circle(overlay, (point.x, point.y), 5, (255, 255, 255), 1)

    frame_path_obj = Path(frame_path)
    output_path = f"{output_dir}/{frame_path_obj.stem}{frame_path_obj.suffix}"

    # Save the result
    cv2.imwrite(output_path, overlay)

    return output_path
