import os
import json
import subprocess
import numpy as np
import pickle
import cv2
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from sqlalchemy.orm import Session
from db import get_db
from models import Object, Point, Frame, Mask, Video

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('../server.log')
    ]
)
logger = logging.getLogger(__name__)


def time_to_seconds(time_str: str) -> float:
    """
    Convert time string in format "HH:MM:SS.MS" to seconds (float).

    Args:
        time_str: Time string in format "HH:MM:SS.MS"

    Returns:
        Time in seconds as float

    Raises:
        ValueError: If time format is invalid
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


def extract_video_metadata(video_path: str) -> Dict[str, Union[int, float]]:
    """
    Extract metadata from a video file using ffprobe.

    Args:
        video_path: Path to the video file

    Returns:
        Dict containing width, height, fps, duration, and file_size
    """
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

        logger.info(
            f"Extracted metadata from {video_path}: {width}x{height}, {fps} fps, {duration} seconds")

    except (subprocess.SubprocessError, json.JSONDecodeError, ValueError, KeyError) as e:
        logger.error(f"Error extracting video metadata: {e}")
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


def get_frames_list(frames_dir: Union[str, Path]) -> List[Path]:
    """
    Get a list of frames from the specified directory.

    Args:
        frames_dir: Path to the directory containing frames

    Returns:
        List of frame file paths
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

    logger.debug(f"Found {len(frames)} frames in {frames_dir}")
    return frames


def extract_frames_at_frame_step(
    video_path: str,
    frame_step: int,
    db: Session = next(get_db())
) -> Optional[Path]:
    """
    Extract frames from a video at a specified frame step using ffmpeg.
    Saves all frames to the filesystem but only adds the first frame to the database.

    Args:
        video_path: Path to the video file
        frame_step: Step size for frame extraction
        db: Database session

    Returns:
        Path to the directory containing extracted frames
    """
    # Convert video_path to string if it's a Path object
    video_path_str = str(video_path) if isinstance(
        video_path, Path) else video_path

    # Check if the video file exists
    if not os.path.exists(video_path_str):
        logger.error(f"Video file '{video_path_str}' not found")
        raise FileNotFoundError(f"Video file '{video_path_str}' not found.")

    # Check if the video exists in the database - ensure we use a string for the query
    video = db.query(Video).filter(Video.file_path == video_path_str).first()
    if not video:
        logger.error(f"Video '{video_path_str}' not found in database")
        raise ValueError(f"Video '{video_path_str}' not found in database.")

    # Create base frames directory if it doesn't exist
    base_frames_dir = Path("data/frames")
    base_frames_dir.mkdir(exist_ok=True)

    # Create video frames directory if it doesn't exist
    video_name = Path(video_path_str).stem
    frames_dir = base_frames_dir / video_name / \
        "original"  # e.g. "data/frames/video_name/original"
    frames_dir.mkdir(parents=True, exist_ok=True)

    inference_frames_dir = base_frames_dir / video_name / \
        "inference"  # e.g. "data/frames/video_name/inference"
    inference_frames_dir.mkdir(parents=True, exist_ok=True)

    # Remove existing frames in the directory
    for file in frames_dir.glob("*.jpg"):
        file.unlink()

    # Remove existing frames from the database, if any
    db.query(Frame).filter(Frame.video_id == video.id).delete()
    db.commit()
    db.refresh(video)

    try:
        # Log extraction info
        extraction_msg = f"Extracting frames from '{video_path_str}' with step {frame_step}"
        logger.info(extraction_msg)

        # Prepare ffmpeg command to extract frames
        vf_option = f"select='not(mod(n,{frame_step}))'"

        cmd = [
            "ffmpeg",
            "-i", video_path_str,  # Use the string version here
            "-vsync", "vfr",
            "-vf", vf_option,
            str(frames_dir / "%04d.jpg"),
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

        # Check if frames were extracted
        if not any(frames_dir.glob("*.jpg")):
            logger.error(
                f"No frames were extracted from video '{video_path_str}'")
            raise ValueError(
                f"No frames were extracted from video '{video_path_str}'.")

        # Get all extracted frames
        frames = get_frames_list(frames_dir)

        # Store only the first frame in the database
        if frames:
            first_frame = frames[0]
            # Create a new Frame object for just the first frame - without frame_number parameter
            new_frame = Frame(
                video_id=video.id,
                file_path=str(first_frame)
            )
            db.add(new_frame)
            db.commit()
            logger.info(
                f"Added first frame ({first_frame.name}) to database for video ID {video.id}")

        # Copy the first frame to the inference directory using shutil
        if frames:
            first_frame_inference = frames[0]
            inference_frame_path = inference_frames_dir / \
                first_frame_inference.name
            shutil.copy(str(first_frame_inference), str(inference_frame_path))
            logger.info(
                f"Copied first frame to inference directory: {inference_frame_path}")

        # Log completion info
        completion_msg = f"Extracted {len(frames)} frames from '{video_path_str}' to '{frames_dir}' (only first frame stored in DB)"
        logger.info(completion_msg)

        return frames_dir

    except (subprocess.SubprocessError, ValueError, KeyError) as e:
        logger.error(f"Error extracting frames: {e}")
        return None


def create_object(video_id: int, name: str) -> Object:
    """
    Create a new object in the database.

    Args:
        video_id: ID of the video to which the object belongs
        name: Name of the object

    Returns:
        The created object instance
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
        color=color,
        mask=None
    )

    db = next(get_db())
    db.add(new_object)
    db.commit()
    db.refresh(new_object)

    logger.info(
        f"Created new object '{name}' with ID {new_object.id} for video {video_id}")
    return new_object


def serialize_mask(mask: np.ndarray) -> bytes:
    """Serialize a mask to bytes using pickle."""
    return pickle.dumps(mask)


def deserialize_mask(mask_blob: bytes) -> np.ndarray:
    """Deserialize a mask from bytes using pickle."""
    return pickle.loads(mask_blob)


def create_point(x: int, y: int, positive: int, object_id: int, db: Session = next(get_db())) -> Point:
    """
    Create a new point for an object.

    Args:
        x: X coordinate
        y: Y coordinate
        positive: 1 for positive point, 0 for negative point
        object_id: ID of the object this point belongs to
        db: Database session

    Returns:
        The created point
    """
    # Get object from DB
    current_object = db.query(Object).filter_by(id=object_id).first()
    if not current_object:
        logger.error(f"Object with ID {object_id} not found in database")
        raise ValueError(f"Object with ID {object_id} not found in database.")

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

    logger.info(
        f"Created new {'positive' if positive else 'negative'} point at ({x}, {y}) for object {object_id}")
    return new_point


def remove_point(point_id: int, db: Session = next(get_db())) -> None:
    """
    Remove a point from the database.

    Args:
        point_id: ID of the point to remove
        db: Database session
    """
    # Get point from DB
    point = db.query(Point).filter_by(id=point_id).first()
    if not point:
        logger.error(f"Point with ID {point_id} not found in database")
        raise ValueError(f"Point with ID {point_id} not found in database.")

    # Delete the point
    db.delete(point)
    db.commit()
    logger.info(f"Removed point with ID {point_id}")


def draw_objects_masks_on_frame(
    frame_path: str,
    object_ids: List[int],
    output_dir: str,
    db: Session = next(get_db())
) -> str:
    """
    Draw object masks onto a frame and save as new image.

    Args:
        frame_path: Path to the frame image
        object_ids: List of object IDs to draw masks for
        output_dir: Directory path to save the output image
        db: Database session

    Returns:
        Path to the saved masked image
    """
    # Check if the output directory exists, if not create it
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Read the frame
    frame = cv2.imread(str(frame_path))
    if frame is None:
        logger.error(f"Could not read frame from {frame_path}")
        raise FileNotFoundError(f"Could not read frame from {frame_path}")

    # Create a copy for overlay
    overlay = frame.copy()

    # Get the frame from the database to reference its ID
    frame_record = db.query(Frame).filter_by(file_path=frame_path).first()
    if not frame_record:
        logger.error(f"Frame {frame_path} not found in database")
        raise ValueError(f"Frame {frame_path} not found in database")

    logger.info(
        f"Drawing masks for objects {object_ids} on frame {frame_path}")
    # For each object ID
    for obj_id in object_ids:
        # Get object from database
        obj = db.query(Object).filter_by(id=obj_id).first()
        if not obj:
            logger.warning(
                f"Object with ID {obj_id} not found in database, skipping")
            continue

        # Get all points for this object
        points = db.query(Point).filter_by(object_id=obj_id).all()

        # Get mask for this object and frame from the Mask table
        mask_record = db.query(Mask).filter_by(
            object_id=obj_id,
            frame_id=frame_record.id
        ).first()

        # Draw mask if available
        if mask_record and mask_record.mask:
            # Deserialize the mask
            mask = deserialize_mask(mask_record.mask)

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
    logger.info(f"Saved masked frame to {output_path}")

    return output_path


def create_bounding_box_on_mask(mask):
    """"
    Create a bounding box around the non-zero regions of the mask.

    Args:
        mask: Binary mask (numpy array)
    Returns:
        Tuple of (x_min, y_min, x_max, y_max) coordinates
    """
    # Deserialize the mask if it's in bytes
    if isinstance(mask, bytes):
        mask = deserialize_mask(mask)

    # Ensure mask is binary
    mask = (mask > 0).astype(np.uint8)

    # Find the bounding box coordinates
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)

    # Get the first and last indices of the rows and columns that contain non-zero values
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]

    # Ensure bounding box is tight
    return x_min, y_min, x_max + 1, y_max + 1


def sqlalchemy_to_dict(obj: Any) -> dict:
    """
    Convert SQLAlchemy model instance to a dictionary.

    Args:
        obj: SQLAlchemy model instance

    Returns:
        Dictionary representation of the model
    """
    if obj is None:
        return None

    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)

        # Handle special cases like binary data that shouldn't be returned directly
        if column.name == 'mask' and isinstance(value, bytes):
            # Don't include binary mask data in API responses
            result[column.name] = None
        else:
            result[column.name] = value

    return result


# Function to create a random color string in hex format using numpy
def random_color() -> str:
    """
    Generate a random color in hex format.

    Returns:
        Random color in hex format (e.g., "#RRGGBB")
    """
    r = np.random.randint(0, 255)
    g = np.random.randint(0, 255)
    b = np.random.randint(0, 255)
    return f"#{r:02x}{g:02x}{b:02x}"


# Function to obtain r,g,b values from hex color string
def hex_to_rgb(hex_color: str) -> tuple:
    """
    Convert a hex color string to an RGB tuple.

    Args:
        hex_color: Hex color string (e.g., "#RRGGBB")

    Returns:
        Tuple of (R, G, B) values
    """
    if hex_color.startswith('#') and len(hex_color) == 7:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return r, g, b
    else:
        raise ValueError("Invalid hex color format")
