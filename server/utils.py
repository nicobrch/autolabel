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
from models import Object, Point
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


def extract_frames_at_frame_step(video_path: str, frame_step: int):
    """"
    "Extract frames from a video at a specified frame step using ffmpeg."
    Args:
        video_path (str): Path to the video file.
        frame_step (int): Step size for frame extraction. For example, if
                          frame_step is 5, every 5th frame will be extracted.
    """
    # Create base frames directory if it doesn't exist
    base_frames_dir = Path("frames")
    base_frames_dir.mkdir(exist_ok=True)

    # Create video frames directory if it doesn't exist
    video_name = Path(video_path).stem
    video_frames_dir = base_frames_dir / video_name
    video_frames_dir.mkdir(exist_ok=True)

    try:
        # Prepare ffmpeg command to extract frames
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vsync", "vfr",
            "-vf", f"select='not(mod(n,{frame_step}))'",
            str(video_frames_dir / "%04d.jpg"),
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

        # Check if frames were extracted
        if not any(video_frames_dir.glob("*.jpg")):
            raise ValueError(
                f"No frames were extracted from video '{video_path}'.")

        return video_frames_dir
    except (subprocess.SubprocessError, ValueError, KeyError) as e:
        print(f"Error extracting frames: {e}", file=sys.stderr)


def create_object(clip_id: int, name: str):
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
        clip_id=clip_id,
        name=name,
        color=color,  # Default color, can be changed later
        mask=None
    )

    db = next(get_db())
    db.add(new_object)
    db.commit()
    db.refresh(new_object)

    return new_object


def get_frames_list(video_path: str) -> list:
    # Check if the frames directory exists
    base_frames_dir = Path("frames")
    if not base_frames_dir.exists():
        raise FileNotFoundError(
            f"Frames directory '{base_frames_dir}' does not exist.")

    # Check if frames directory exists
    video_name = Path(video_path).stem
    video_frames_dir = base_frames_dir / video_name
    if not video_frames_dir.exists():
        raise FileNotFoundError(
            f"Frames directory '{video_frames_dir}' does not exist.")

    # Get the list of frames
    frames = sorted(video_frames_dir.glob("*.jpg"))
    if not frames:
        raise FileNotFoundError(
            f"No frames found in directory '{video_frames_dir}'.")
    return frames


def initialize_sam_predictor(checkpoint):
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


def serialize_mask(mask):
    return pickle.dumps(mask)


def deserialize_mask(mask_blob):
    return pickle.loads(mask_blob)


def add_point_and_segment(x: int, y: int, positive: int, object_id: int, frames_dir: str, sam_predictor, db: Session = next(get_db())):
    # Get object from DB
    current_object = db.query(Object).filter_by(id=object_id).first()
    if not current_object:
        raise ValueError(f"Object with ID {object_id} not found in database.")

    # SAM2 state
    inference_state = sam_predictor.init_state(frames_dir)
    sam_predictor.reset_state(inference_state)

    # Append the new point to the existing points
    new_point = Point(
        object_id=object_id,
        x=x,
        y=y,
        label=positive
    )
    db.add(new_point)
    db.commit()
    db.refresh(new_point)

    # Then retrieve all existing points of the object
    existing_points = db.query(Point).filter_by(object_id=object_id).all()

    # Prepare data for SAM2
    points = np.array([[p.x, p.y] for p in existing_points], dtype=np.float32)
    labels = np.array([p.label for p in existing_points], dtype=np.int32)

    print(f"Points: {points}")
    print(f"Labels: {labels}")

    # Perform segmentation
    _, _, out_mask_logits = sam_predictor.add_new_points_or_box(
        inference_state=inference_state,
        frame_idx=0,    # Assuming we always work with the first frame
        obj_id=object_id,
        points=points,
        labels=labels,
    )

    # Save the mask to the database as a binary blob
    mask = (out_mask_logits[0] > 0.0).cpu().numpy().squeeze()

    mask_blob = serialize_mask(mask)
    current_object.mask = mask_blob
    db.commit()
    db.refresh(current_object)


def draw_objects_masks(frame_path: str, object_ids: list, output_dir: str, db: Session = next(get_db())):
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
        if not obj or not obj.mask:
            continue

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
        cv2.addWeighted(color_mask, 0.5, overlay, 0.8, 0, overlay)

    frame_path_obj = Path(frame_path)
    output_path = f"{output_dir}/{frame_path_obj.stem}_masked{frame_path_obj.suffix}"

    # Save the result
    cv2.imwrite(output_path, overlay)

    return output_path


if __name__ == "__main__":
    # Create objects
    db = next(get_db())
    frames_dir = "frames/footage_kdxonm"
    draw_objects_masks(
        "frames/footage_kdxonm/0001.jpg", [1, 2], "frames/footage_kdxonm_masked")
    # create_tables()
