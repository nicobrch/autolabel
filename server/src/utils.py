import os
import json
import subprocess
import numpy as np
import pickle
import cv2
import logging
import shutil
import datetime  # Add this import
import yaml  # Add this import for YAML handling
import tempfile  # Add this import for temporary directory
import zipfile   # Add this import for ZIP creation
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from sqlalchemy.orm import Session
from sqlalchemy import exists
from db import get_db
from models import Object, Point, Frame, Mask, Video, VideoInference

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


def public_videos_dir_with_video_name(video_name: str) -> Path:
    return Path(f"public/videos/{video_name}")


def public_frames_base_dir_with_video_name(video_name: str) -> Path:
    return Path(f"public/videos/{video_name}/base")


def public_frames_inference_dir_with_video_name(video_name: str) -> Path:
    return Path(f"public/videos/{video_name}/inference")


def public_video_thumbnail_dir_with_video_name(video_name: str) -> Path:
    return Path(f"public/videos/{video_name}/thumbnail")


def public_coco_dir_with_video_name(video_name: str) -> Path:
    return Path(f"public/videos/{video_name}/coco")


def public_cvat_dir_with_video_name(video_name: str) -> Path:
    return Path(f"public/videos/{video_name}/cvat")


def public_yolo_dir_with_video_name(video_name: str) -> Path:
    return Path(f"public/videos/{video_name}/yolo")


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


def extract_frames_at_fps(
    video_path: str,
    db: Session = next(get_db())
) -> Optional[Path]:
    """
    Extract frames from a video using the fps stored in the database.
    Saves all frames to the filesystem but only adds the first frame to the database.

    Args:
        video_path: Path to the video file
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

    video_name = Path(video.file_name).stem

    # Create base frames directory if it doesn't exist
    base_frames_dir = public_frames_base_dir_with_video_name(
        video_name=video_name)
    base_frames_dir.mkdir(exist_ok=True)

    thumbnail_dir = public_video_thumbnail_dir_with_video_name(
        video_name=video_name)
    thumbnail_dir.mkdir(parents=True, exist_ok=True)

    # Remove existing frames in the directory
    for file in base_frames_dir.glob("*.jpg"):
        file.unlink()

    # Remove existing frames from the database, if any
    db.query(Frame).filter(Frame.video_id == video.id).delete()
    db.commit()
    db.refresh(video)

    try:
        # Use the fps stored in the video object from the database
        original_fps = video.fps
        if original_fps <= 0:
            logger.warning(
                f"Invalid original FPS {original_fps}, defaulting to 15")
            original_fps = 15

        # Log extraction info
        extraction_msg = f"Extracting frames from '{video_path_str}' at FPS {original_fps}"
        logger.info(extraction_msg)

        cmd = [
            "ffmpeg",
            "-i", video_path_str,  # Use the string version here
            "-vf", f"fps={original_fps}",
            str(base_frames_dir / "%05d.jpg"),
            "-loglevel", "error",
            "-hide_banner",
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

        # Check if frames were extracted
        if not any(base_frames_dir.glob("*.jpg")):
            logger.error(
                f"No frames were extracted from video '{video_path_str}'")
            raise ValueError(
                f"No frames were extracted from video '{video_path_str}'.")

        # Get all extracted frames
        frames = get_frames_list(base_frames_dir)

        # Store only the first frame in the database
        if frames:
            first_frame = frames[0]
            # Create a new Frame object for just the first frame
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
            inference_frame_path = thumbnail_dir / "inference.jpg"
            base_thumbnail_path = thumbnail_dir / "thumbnail.jpg"
            shutil.copy(str(first_frame_inference), str(inference_frame_path))
            shutil.copy(str(first_frame_inference), str(base_thumbnail_path))
            logger.info(
                f"Copied first frame to inference directory: {inference_frame_path} and {base_thumbnail_path}")

        # Log completion info with FPS information
        completion_msg = f"Extracted {len(frames)} frames from '{video_path_str}' to '{base_frames_dir}' (FPS: {original_fps})"
        logger.info(completion_msg)

        return base_frames_dir

    except (subprocess.SubprocessError, ValueError, KeyError) as e:
        logger.error(f"Error extracting frames: {e}")
        return None


def construct_video_from_inference_frames(video_id: int, model_name: str, db: Session = next(get_db())) -> Optional[str]:
    """
    Construct a video from the inference frames stored in the database.

    Args:
        video_id: ID of the video to construct
        db: Database session

    Returns:
        Path to the constructed video file, or None if failed
    """
    # Get the video object
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        logger.error(f"Video with ID {video_id} not found")
        return None

    # Get all inference frames for this video
    video_name = Path(video.file_name).stem
    inference_frames_dir = public_frames_inference_dir_with_video_name(
        video_name=video_name)
    inference_frames = get_frames_list(inference_frames_dir)
    if not inference_frames:
        logger.error(
            f"No inference frames found for video ID {video_id} in {inference_frames_dir}")
        return None

    # Construct the video using ffmpeg
    output_video_path = inference_frames_dir / f"{video_name}_inference.mp4"

    output_video_path = output_video_path.resolve()
    if output_video_path.exists():
        output_video_path.unlink()

    logger.info(f"Constructing video at {output_video_path}")

    # Prepare ffmpeg command
    # Use the same FPS as the original video
    fps = video.fps if video.fps > 0 else 24
    cmd = [
        "ffmpeg",
        "-framerate", str(fps),
        "-i", str(inference_frames_dir / "%05d.jpg"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_video_path)
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
        logger.info(f"Constructed video at {output_video_path}")

        # Get a fresh DB session
        db = next(get_db())

        # Check if a video with this file path already exists
        existing_video = db.query(Video).filter(
            Video.file_path == str(output_video_path)).first()

        if existing_video:
            # Update the existing video entry
            existing_video.file_size = os.path.getsize(output_video_path)
            existing_video.updated_at = datetime.datetime.utcnow()
            db.commit()
            inference_video_id = existing_video.id
            logger.info(
                f"Updated existing inference video with ID {inference_video_id}")
        else:
            # Create a new video entry in the database
            new_video = Video(
                project_id=video.project_id,
                file_path=str(output_video_path),
                file_name=output_video_path.name,
                file_size=os.path.getsize(output_video_path),
                width=video.width,
                height=video.height,
                fps=video.fps,
                duration=video.duration,
                type="inference"
            )
            db.add(new_video)
            db.commit()
            db.refresh(new_video)
            inference_video_id = new_video.id
            logger.info(
                f"Created new inference video with ID {inference_video_id}")

        # Check if a VideoInference entry already exists
        existing_inference = db.query(VideoInference).filter(
            VideoInference.base_video_id == video.id
        ).first()

        if existing_inference:
            # Update the existing VideoInference entry
            existing_inference.inference_video_id = inference_video_id
            existing_inference.model_name = model_name
            db.commit()
            logger.info(
                f"Updated existing VideoInference entry for video ID {video.id}")
        else:
            # Create a new VideoInference entry
            video_inference = VideoInference(
                base_video_id=video.id,
                inference_video_id=inference_video_id,
                model_name=model_name
            )
            db.add(video_inference)
            db.commit()
            logger.info(
                f"Created new VideoInference entry for video ID {video.id}")

        return str(output_video_path)
    except subprocess.SubprocessError as e:
        logger.error(f"Error constructing video: {e}")
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
    video_id: int,
    db: Session = next(get_db())
) -> str:
    """
    Draw all object masks and points for the given video frame.

    Args:
        video_id: ID of the video
        db: Database session

    Returns:
        Path to the inference image with masks and points
    """
    # Check if video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise ValueError(f"Video with ID {video_id} not found")

    # Get all objects for this video that have masks
    # Fix: Use SQLAlchemy's exists() function properly
    objects_with_masks = db.query(Object).filter(
        Object.video_id == video_id,
        exists().where(Mask.object_id == Object.id)  # Correct way to use exists()
    ).all()

    if not objects_with_masks:
        raise ValueError(
            f"No objects with masks found for video ID {video_id}")

    # Get the frame for this video
    frame = db.query(Frame).filter(Frame.video_id == video_id).first()
    if not frame:
        raise ValueError(f"No frame found for video ID {video_id}")

    # Construct paths
    frame_path = Path(frame.file_path)
    if not frame_path.exists():
        raise FileNotFoundError(f"Frame file '{frame_path}' not found")

    video_name = Path(video.file_name).stem
    thumbnail_dir = public_video_thumbnail_dir_with_video_name(
        video_name=video_name)

    # Load the first frame
    frame_img = cv2.imread(str(frame_path))
    if frame_img is None:
        raise ValueError(f"Could not read frame at {frame_path}")

    # Create a copy for overlay
    overlay = frame_img.copy()

    # For each object, get its mask and draw it
    for obj in objects_with_masks:
        mask_data = db.query(Mask).filter(Mask.object_id == obj.id).first()
        if not mask_data:
            continue

        # Deserialize mask
        mask = deserialize_mask(mask_data.mask)

        # Convert hex color to BGR (for OpenCV)
        try:
            r, g, b = hex_to_rgb(obj.color)
            color = (b, g, r)  # BGR format for OpenCV
        except ValueError:
            color = (0, 255, 0)  # Default green if invalid color

        # Create color mask
        color_mask = np.zeros_like(frame_img)
        if mask.shape[:2] != frame_img.shape[:2]:
            # Resize mask if dimensions don't match
            mask = cv2.resize(mask.astype(np.uint8), (frame_img.shape[1], frame_img.shape[0]),
                              interpolation=cv2.INTER_NEAREST)
            mask = mask.astype(bool)

        color_mask[mask] = color

        # Overlay with transparency
        cv2.addWeighted(color_mask, 0.5, overlay, 1, 0, overlay)

        # Get all points for this object
        points = db.query(Point).filter(Point.object_id == obj.id).all()

        # Draw points on the overlay
        for point in points:
            # Green for positive points (label=1), Red for negative points (label=0)
            point_color = (0, 255, 0) if point.label == 1 else (0, 0, 255)

            # Draw a filled circle for each point
            cv2.circle(overlay, (point.x, point.y), 2, point_color, -1)

    # Save the inference image
    inference_path = thumbnail_dir / "inference.jpg"
    cv2.imwrite(str(inference_path), overlay)
    logger.info(
        f"Saved inference image with masks and points at {inference_path}")

    return str(inference_path)


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


def mask_to_yolo_bbox(mask: np.ndarray, image_width: int, image_height: int) -> tuple:
    """
    Convert a binary mask to YOLO format bounding box (normalized coordinates).

    Args:
        mask: Binary mask as numpy array
        image_width: Width of the original image
        image_height: Height of the original image

    Returns:
        Tuple of (x_center, y_center, width, height) in normalized coordinates
    """
    # Get the bounding box coordinates (x_min, y_min, x_max, y_max)
    try:
        x_min, y_min, x_max, y_max = create_bounding_box_on_mask(mask)

        # Calculate width and height
        width = x_max - x_min
        height = y_max - y_min

        # Calculate center coordinates
        x_center = x_min + width / 2
        y_center = y_min + height / 2

        # Normalize coordinates (0-1)
        x_center_norm = x_center / image_width
        y_center_norm = y_center / image_height
        width_norm = width / image_width
        height_norm = height / image_height

        return (x_center_norm, y_center_norm, width_norm, height_norm)
    except (IndexError, ValueError):
        # Return zeros if mask is empty or has issues
        logger.warning(
            "Empty or invalid mask encountered when creating YOLO bbox")
        return (0, 0, 0, 0)


def save_yolo_annotations(frame_path: Path, objects_data: list, output_dir: Path) -> None:
    """
    Save YOLO format annotations to a text file.

    Args:
        frame_path: Path to the original frame (used to derive the output filename)
        objects_data: List of tuples (class_id, x_center, y_center, width, height)
        output_dir: Directory to save the annotation file
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create output filename (same as frame but with .txt extension)
    output_file = output_dir / f"{frame_path.stem}.txt"

    # Write annotations to file
    with open(output_file, 'w') as f:
        for obj_data in objects_data:
            class_id, x_center, y_center, width, height = obj_data
            # YOLO format: <object-class> <x_center> <y_center> <width> <height>
            f.write(
                f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

    logger.info(f"Saved YOLO annotations to {output_file}")


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


# Function to create a random color in hex format using numpy
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


def create_yolo_data_yaml(object_names: Union[list, List[str]], output_dir: Path) -> None:
    """
    Create a data.yml file for YOLO training that maps class IDs to names.

    Args:
        object_names: List of unique object names or Object instances
        output_dir: Directory to save the YAML file
    """
    try:
        # Handle both list of strings and list of Object instances for backward compatibility
        if object_names and hasattr(object_names[0], 'name'):
            # If it's a list of Object instances, extract unique names
            unique_names = list(set(obj.name for obj in object_names))
            unique_names.sort()  # Sort for consistent ordering
        else:
            # If it's already a list of strings, use as is
            unique_names = sorted(list(set(object_names)))

        # Create mapping of class index to object name
        names = {idx: name for idx, name in enumerate(unique_names)}

        # Create YAML content
        yaml_content = {
            'classes': len(names),  # number of classes
            'names': names,    # class names
        }

        # Save to file
        yaml_file = output_dir / "data.yml"

        with open(yaml_file, 'w') as f:
            yaml.dump(yaml_content, f,
                      default_flow_style=False, sort_keys=False)

        logger.info(
            f"Created YOLO data.yml file at {yaml_file} with {len(names)} unique classes")
    except Exception as e:
        logger.error(f"Error creating YOLO data.yml file: {e}")


def create_yolo_dataset_zip(video_id: int, db: Session = next(get_db())) -> Optional[str]:
    """
    Create a ZIP archive containing YOLO-formatted dataset for a video.

    The ZIP contains:
    - images/: All base frames with video_name prepended
    - labels/: All YOLO annotations with video_name prepended
    - data.yml: Class mapping file

    Args:
        video_id: ID of the video
        db: Database session

    Returns:
        Path to the created ZIP file or None if failed
    """
    try:
        # Get the video from database
        video = db.query(Video).filter_by(id=video_id).first()
        if not video:
            logger.error(f"Video with ID {video_id} not found in database")
            return None

        video_name = Path(video.file_path).stem

        # Get paths to directories
        base_frames_dir = public_frames_base_dir_with_video_name(video_name)
        yolo_dir = public_yolo_dir_with_video_name(video_name)

        # Check if directories exist
        if not base_frames_dir.exists() or not yolo_dir.exists():
            logger.error(
                f"Required directories not found for video {video_name}")
            return None

        # Create a temporary directory for preparing the ZIP contents
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            # Create subdirectories
            images_dir = temp_dir_path / "images"
            labels_dir = temp_dir_path / "labels"
            images_dir.mkdir()
            labels_dir.mkdir()

            # Copy and rename image files
            base_frames = get_frames_list(base_frames_dir)
            for frame in base_frames:
                new_name = f"{video_name}_{frame.name}"
                shutil.copy(frame, images_dir / new_name)

            # Copy and rename label files
            for txt_file in yolo_dir.glob("*.txt"):
                # Skip data.yml
                if txt_file.name == "data.yml":
                    continue
                new_name = f"{video_name}_{txt_file.name}"
                shutil.copy(txt_file, labels_dir / new_name)

            # Copy data.yml to the root of the temp directory
            data_yml_path = yolo_dir / "data.yml"
            if data_yml_path.exists():
                shutil.copy(data_yml_path, temp_dir_path)
            else:
                logger.warning(
                    f"data.yml not found in {yolo_dir}, creating a default one")
                # If data.yml doesn't exist, try to create one based on the objects
                objects = db.query(Object).filter_by(video_id=video_id).all()
                create_yolo_data_yaml(objects, temp_dir_path)

            # Create ZIP file
            zip_path = yolo_dir / f"{video_name}_yolo.zip"

            # Remove existing ZIP if it exists
            if zip_path.exists():
                zip_path.unlink()

            # Use zipfile to create the archive
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files from temp directory to the ZIP
                for root, _, files in os.walk(temp_dir_path):
                    for file in files:
                        file_path = Path(root) / file
                        # Get relative path to maintain directory structure
                        rel_path = file_path.relative_to(temp_dir_path)
                        zipf.write(file_path, rel_path)

            logger.info(f"Created YOLO dataset ZIP at {zip_path}")
            return str(zip_path)

    except Exception as e:
        logger.error(f"Error creating YOLO dataset ZIP: {e}")
        return None


def mask_to_coco_bbox(mask: np.ndarray) -> tuple:
    """
    Convert a binary mask to COCO format bounding box (x, y, width, height).

    Args:
        mask: Binary mask as numpy array

    Returns:
        Tuple of (x, y, width, height) in absolute coordinates
    """
    try:
        x_min, y_min, x_max, y_max = create_bounding_box_on_mask(mask)

        # Calculate width and height
        width = x_max - x_min
        height = y_max - y_min

        # COCO format: [x, y, width, height] where (x, y) is top-left corner
        return (x_min, y_min, width, height)
    except (IndexError, ValueError):
        # Return zeros if mask is empty or has issues
        logger.warning(
            "Empty or invalid mask encountered when creating COCO bbox")
        return (0, 0, 0, 0)


def create_coco_annotations_structure(objects: list, base_frames: List[Path]) -> dict:
    """
    Create the basic COCO annotations data structure.

    Args:
        objects: List of Object instances
        base_frames: List of base frame paths

    Returns:
        COCO format dictionary with images, annotations, and categories
    """
    # Create unique categories based on object names (merge objects with same name)
    unique_names = list(set(obj.name for obj in objects))
    categories = []
    for idx, name in enumerate(sorted(unique_names)):
        categories.append({
            'id': idx + 1,  # COCO uses 1-based indexing
            'name': name,
            'supercategory': 'object'
        })

    # Create images metadata
    images = []
    for idx, frame_path in enumerate(base_frames):
        # Get image dimensions
        img = cv2.imread(str(frame_path))
        if img is not None:
            height, width = img.shape[:2]
        else:
            # Default dimensions if image can't be read
            width, height = 1920, 1080
            logger.warning(
                f"Could not read image {frame_path}, using default dimensions")

        images.append({
            'id': idx + 1,  # COCO uses 1-based indexing
            'file_name': frame_path.name,
            'width': width,
            'height': height
        })

    return {
        'info': {
            'description': 'SAM2 Generated Annotations',
            'version': '1.0',
            'year': datetime.datetime.now().year,
            'contributor': 'AutoLabel Tool',
            'date_created': datetime.datetime.now().isoformat()
        },
        'licenses': [],
        'images': images,
        'annotations': [],
        'categories': categories
    }


def get_category_id_by_name(object_name: str, categories: list) -> int:
    """
    Get category ID by object name from COCO categories list.

    Args:
        object_name: Name of the object
        categories: List of COCO category dictionaries

    Returns:
        Category ID (1-based)
    """
    for category in categories:
        if category['name'] == object_name:
            return category['id']

    # If not found, return 1 as default
    logger.warning(
        f"Category not found for object name: {object_name}, using default ID 1")
    return 1


def save_coco_annotations(coco_data: dict, output_dir: Path, video_name: str) -> None:
    """
    Save COCO format annotations to a JSON file.

    Args:
        coco_data: COCO format dictionary
        output_dir: Directory to save the JSON file
        video_name: Name of the video (used in filename)
    """
    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Add unique annotation IDs and convert NumPy types to Python types
        for idx, annotation in enumerate(coco_data['annotations']):
            annotation['id'] = idx + 1  # COCO uses 1-based indexing
            # Convert NumPy types to Python native types for JSON serialization
            annotation['image_id'] = int(annotation['image_id'])
            annotation['category_id'] = int(annotation['category_id'])
            annotation['area'] = float(annotation['area'])
            annotation['iscrowd'] = int(annotation['iscrowd'])
            # Convert bbox values to Python native types
            annotation['bbox'] = [float(x) for x in annotation['bbox']]

        # Convert image dimensions to Python native types
        for image in coco_data['images']:
            image['id'] = int(image['id'])
            image['width'] = int(image['width'])
            image['height'] = int(image['height'])

        # Convert category IDs to Python native types
        for category in coco_data['categories']:
            category['id'] = int(category['id'])

        # Create output filename
        output_file = output_dir / f"{video_name}_coco.json"

        # Write annotations to JSON file
        with open(output_file, 'w') as f:
            json.dump(coco_data, f, indent=2)

        logger.info(f"Saved COCO annotations to {output_file}")
        logger.info(f"COCO dataset contains {len(coco_data['images'])} images, "
                    f"{len(coco_data['annotations'])} annotations, "
                    f"{len(coco_data['categories'])} categories")

    except Exception as e:
        logger.error(f"Error saving COCO annotations: {e}")


def create_coco_dataset_zip(video_id: int, db: Session = next(get_db())) -> Optional[str]:
    """
    Create a ZIP archive containing COCO-formatted dataset for a video.

    The ZIP contains:
    - images/: All base frames with video_name prepended
    - annotations/: COCO JSON annotation file

    Args:
        video_id: ID of the video
        db: Database session

    Returns:
        Path to the created ZIP file or None if failed
    """
    try:
        # Get the video from database
        video = db.query(Video).filter_by(id=video_id).first()
        if not video:
            logger.error(f"Video with ID {video_id} not found in database")
            return None

        video_name = Path(video.file_path).stem

        # Get paths to directories
        base_frames_dir = public_frames_base_dir_with_video_name(video_name)
        coco_dir = public_coco_dir_with_video_name(video_name)

        # Check if directories exist
        if not base_frames_dir.exists() or not coco_dir.exists():
            logger.error(
                f"Required directories not found for video {video_name}")
            return None

        # Check if COCO JSON file exists
        coco_json_path = coco_dir / f"{video_name}_coco.json"
        if not coco_json_path.exists():
            logger.error(f"COCO annotations file not found: {coco_json_path}")
            return None

        # Create a temporary directory for preparing the ZIP contents
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            # Create subdirectories
            images_dir = temp_dir_path / "images"
            annotations_dir = temp_dir_path / "annotations"
            images_dir.mkdir()
            annotations_dir.mkdir()

            # Copy and rename image files
            base_frames = get_frames_list(base_frames_dir)
            for frame in base_frames:
                new_name = f"{video_name}_{frame.name}"
                shutil.copy(frame, images_dir / new_name)

            # Copy COCO JSON file
            shutil.copy(coco_json_path, annotations_dir /
                        f"{video_name}_coco.json")

            # Create ZIP file
            zip_path = coco_dir / f"{video_name}_coco.zip"

            # Remove existing ZIP if it exists
            if zip_path.exists():
                zip_path.unlink()

            # Use zipfile to create the archive
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files from temp directory to the ZIP
                for root, _, files in os.walk(temp_dir_path):
                    for file in files:
                        file_path = Path(root) / file
                        # Get relative path to maintain directory structure
                        rel_path = file_path.relative_to(temp_dir_path)
                        zipf.write(file_path, rel_path)

            logger.info(f"Created COCO dataset ZIP at {zip_path}")
            return str(zip_path)

    except Exception as e:
        logger.error(f"Error creating COCO dataset ZIP: {e}")
        return None
