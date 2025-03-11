import os
import sys
import json
import subprocess
import torch
import numpy as np
from pathlib import Path
from sam2.sam2.build_sam import build_sam2_video_predictor


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
            str(video_frames_dir / "_%04d.jpg"),
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
