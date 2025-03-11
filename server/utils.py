import os
import sys
import json
import subprocess
import torch
import numpy as np
from pathlib import Path
from sqlalchemy.orm import Session
from db import get_db
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
    except (subprocess.SubprocessError, ValueError, KeyError) as e:
        print(f"Error extracting frames: {e}", file=sys.stderr)


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


def add_point_and_segment(db: Session, x: int, y: int, positive: int, object_id: int, frames_dir: str, sam_predictor):
    # Get object from DB
    current_object = db.query(Object).filter_by(id=object_id).first()
    if not current_object:
        raise ValueError(f"Object with ID {object_id} not found in database.")

    # Convert coords to numpy array
    points = np.array([[x, y]], dtype=np.float32)
    # Generate labels, where positive is 1 and negative is 0
    labels = np.array([positive], dtype=np.int32)

    # Initialize SAM2 state
    inference_state = sam_predictor.init_state(video_path=frames_dir)
    sam_predictor.reset_state(inference_state)

    # Add point and segment
    _, _, out_mask_logits = sam_predictor.add_new_points_or_box(
        inference_state=inference_state,
        frame_idx=0,    # Assuming we are working with the first frame
        obj_id=object_id,
        points=points,
        labels=labels,
    )

    # Save the mask to the database as a binary blob
    out_mask = (out_mask_logits[0] > 0.0).cpu().numpy().squeeze()
    mask_bytes = out_mask.tobytes()

    current_object.mask = mask_bytes
    db.commit()
    db.refresh(current_object)

    # Save the points to the database
    point = Point(
        object_id=object_id,
        x=x,
        y=y,
        label=positive
    )
    db.add(point)
    db.commit()
    db.refresh(point)

    return current_object


# if __name__ == "__main__":
#     video_path = "clips/footage_lxeqbo.mp4"
#     frame_step = 5
#     extract_frames_at_frame_step(video_path, frame_step)
#     frames = get_frames_list(video_path)
#     print(f"Extracted {len(frames)} frames from {video_path}")
#     sam_predictor = initialize_sam_predictor("tiny")
#     print(f"Initialized SAM2 predictor with checkpoint 'tiny'")
#     # Example usage of add_point_and_segment function
#     db = next(get_db())
#     # Create object
#     object_id = 1
#     object_name = "example_object"
#     object_color = "red"
#     new_object = Object(
#         clip_id=1,
#         name=object_name,
#         color=object_color,
#         mask=None
#     )
#     db.add(new_object)
#     db.commit()
#     db.refresh(new_object)
#     # Add point and segment
#     x, y = 100, 200
#     positive = 1
#     object_id = 1
#     frames_dir = "frames/footage_lxeqbo"
#     current_object = add_point_and_segment(
#         db, x, y, positive, object_id, frames_dir, sam_predictor)
#     print(f"Added point and segment for object ID {object_id} at ({x}, {y})")
