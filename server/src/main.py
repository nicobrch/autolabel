import os
import shutil
from fastapi import FastAPI, Depends, HTTPException, status, Query, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from db import get_db
from models import Project, Video, Object, Point, VideoInference
from utils import create_yolo_dataset_zip, logger, extract_video_metadata, extract_frames_at_fps, sqlalchemy_to_dict, random_color, draw_objects_masks_on_frame, public_frames_base_dir_with_video_name, public_frames_inference_dir_with_video_name, public_video_thumbnail_dir_with_video_name, public_videos_dir_with_video_name
from inference import InferenceAPI
from fastapi import File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import subprocess
import uvicorn
from fastapi.staticfiles import StaticFiles
from os.path import abspath
from sqlalchemy import exists

app = FastAPI(
    title="AutoLabel API",
    description="API for video labeling with SAM2",
    version="1.0.0"
)

# CORS support for React

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure public directory exists
public_dir = Path(abspath("public"))
public_dir.mkdir(exist_ok=True, parents=True)
# Ensure public videos directory exists
public_videos_dir = Path(abspath("public/videos"))
public_videos_dir.mkdir(exist_ok=True, parents=True)

# Mount static files directories
app.mount("/public", StaticFiles(directory=abspath("public")), name="public")


@app.get("/api/v1/")
async def root():
    return {"message": "AutoLabel API running OK"}


@app.get("/api/v1/projects", response_model=List[dict])
async def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = db.query(Project).offset(skip).limit(limit).all()
    return [sqlalchemy_to_dict(project) for project in projects]


@app.get("/api/v1/projects/{project_id}", response_model=dict)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return sqlalchemy_to_dict(project)


@app.post("/api/v1/projects", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_project(name: str = Body(...), description: str = Body(None), db: Session = Depends(get_db)):
    existing_project = db.query(Project).filter(Project.name == name).first()
    if existing_project:
        raise HTTPException(
            status_code=400, detail="Project with this name already exists")

    new_project = Project(name=name, description=description)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return sqlalchemy_to_dict(new_project)


@app.delete("/api/v1/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    return None


@app.get("/api/v1/projects/{project_id}/videos", response_model=List[dict])
async def list_project_videos(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    videos = db.query(Video).filter(
        Video.project_id == project_id,
        Video.type == "base"
    ).all()
    return [sqlalchemy_to_dict(video) for video in videos]


# Get video by ID
@app.get("/api/v1/videos/{video_id}", response_model=dict)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return sqlalchemy_to_dict(video)


@app.post("/api/v1/videos/upload", response_model=dict)
async def upload_video(
    file: UploadFile = File(...),
    project_id: int = Query(...,
                            description="Project ID to associate with this video"),
    resolution: Optional[str] = Query(
        None, description="Resolution to resize the video, e.g., '1280x720'"),
    target_fps: Optional[float] = Query(
        None, description="Target frames per second for extraction"),
    db: Session = Depends(get_db)
):
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    video_name = file.filename.split(".")[0]

    single_video_dir = public_videos_dir_with_video_name(video_name)
    single_video_dir.mkdir(parents=True, exist_ok=True)
    base_frames_dir = public_frames_base_dir_with_video_name(video_name)
    base_frames_dir.mkdir(parents=True, exist_ok=True)
    inference_frames_dir = public_frames_inference_dir_with_video_name(
        video_name)
    inference_frames_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_dir = public_video_thumbnail_dir_with_video_name(video_name)
    thumbnail_dir.mkdir(parents=True, exist_ok=True)

    # Save the original file temporarily
    temp_file_path = thumbnail_dir / f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)
    except IOError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save video file: {e}")

    # Define the final file path
    video_path = base_frames_dir / file.filename

    try:
        # Base ffmpeg command
        cmd = [
            "ffmpeg",
            "-i", str(temp_file_path),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-an",  # Remove audio track to save disk space
        ]

        # Add resolution parameter if provided
        if resolution and resolution.lower() != "original":
            import re
            if not re.match(r'^\d+x\d+$', resolution):
                # Clean up temp file
                if temp_file_path.exists():
                    temp_file_path.unlink()
                raise HTTPException(
                    status_code=400, detail=f"Invalid resolution format: {resolution}. Must be 'WIDTHxHEIGHT'")
            cmd.extend(["-vf", f"scale={resolution}"])

        # Add fps parameter if provided
        if target_fps:
            cmd.extend(["-r", str(target_fps)])

        # Output file
        cmd.append(str(video_path))

        # Execute ffmpeg command
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

        # Delete temporary file after successful processing
        if temp_file_path.exists():
            temp_file_path.unlink()

    except subprocess.SubprocessError as e:
        # Clean up temp file if processing fails
        if temp_file_path.exists():
            temp_file_path.unlink()
        raise HTTPException(
            status_code=500, detail=f"Failed to process video: {e}")

    # Extract metadata from the final video file
    metadata = extract_video_metadata(video_path)
    if not metadata:
        # Clean up the saved file if metadata extraction fails
        if video_path.exists():
            video_path.unlink()
        raise HTTPException(
            status_code=500, detail="Failed to extract video metadata")

    width = metadata.get("width")
    height = metadata.get("height")
    fps = target_fps if target_fps else metadata.get("fps")
    duration = metadata.get("duration")
    file_size = metadata.get("file_size")

    # Create a new video entry in the database with metadata
    new_video = Video(
        project_id=project_id,
        file_path=str(video_path),  # Changed from video_path to file_path
        file_name=file.filename,
        file_size=file_size,
        width=width,
        height=height,
        fps=fps,
        duration=duration,
        type="base"
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)
    logger.info(f"Video {file.filename} uploaded and metadata extracted.")

    # Extract frames at the specified target FPS
    try:
        extract_frames_at_fps(video_path, db)
    except Exception as e:
        # Clean up the saved video file if frame extraction fails
        if video_path.exists():
            video_path.unlink()
        db.delete(new_video)
        db.commit()
        raise HTTPException(
            status_code=500, detail=f"Failed to extract frames: {e}")

    return sqlalchemy_to_dict(new_video)


# Get the number of frames in a video, if already extracted and available
@app.get("/api/v1/videos/{video_id}/frames/count", response_model=dict)
async def get_frame_count(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Extract the file name without extension
    name = Path(video.file_path).stem

    # Check if frames are already extracted
    frames_dir = public_frames_base_dir_with_video_name(name)
    print(f"Frames directory: {frames_dir}")
    if not frames_dir.exists():
        raise HTTPException(
            status_code=404, detail=f"Frames not extracted for this video {frames_dir}")

    frame_count = len(list(frames_dir.glob("*.jpg")))
    return {"frame_count": frame_count}


# Create a new object for a given video
@app.post("/api/v1/videos/{video_id}/objects", response_model=dict)
async def create_object(
    video_id: int,
    name: str = Body(...),
    color: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    # Check if video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Check if object with same name already exists for this video
    existing_object = db.query(Object).filter(
        Object.video_id == video_id, Object.name == name).first()

    if existing_object:
        raise HTTPException(
            status_code=400, detail="Object with this name already exists for this video")

    # If no color provided, generate a random one
    if not color:
        color = random_color()
    # Validate color format if provided
    elif not color.startswith('#') or len(color) != 7 or not all(c in '0123456789ABCDEFabcdef' for c in color[1:]):
        raise HTTPException(
            status_code=400, detail="Color must be in hex format #RRGGBB")

    # Create new object with color
    new_object = Object(name=name, video_id=video_id, color=color)
    db.add(new_object)
    db.commit()
    db.refresh(new_object)

    return sqlalchemy_to_dict(new_object)


# Get all objects for a given video
@app.get("/api/v1/videos/{video_id}/objects", response_model=List[dict])
async def list_objects(video_id: int, db: Session = Depends(get_db)):
    # Check if video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Get all objects for this video
    objects = db.query(Object).filter(Object.video_id == video_id).all()
    return [sqlalchemy_to_dict(obj) for obj in objects]


# Update an object
@app.put("/api/v1/videos/{video_id}/objects/{object_id}", response_model=dict)
async def update_object(
    video_id: int,
    object_id: int,
    name: str = Body(...),
    color: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    # Check if video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Check if object exists
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    # Check if object belongs to this video
    if obj.video_id != video_id:
        raise HTTPException(
            status_code=400, detail="Object does not belong to this video")

    # Update object name and color
    obj.name = name
    if color:
        obj.color = color

    db.commit()
    db.refresh(obj)

    return sqlalchemy_to_dict(obj)


# Endpoint to segment objects in a video frame using SAM2
@app.post("/api/v1/videos/{video_id}/label_frame", response_model=dict)
async def label_frame(
    video_id: int,
    object_id: int = Body(..., description="Object ID to create a point for"),
    x: int = Body(..., description="X coordinate of the point"),
    y: int = Body(..., description="Y coordinate of the point"),
    label: int = Body(...,
                      description="Point label (1 for positive, 0 for negative)"),
    checkpoint: str = Body(
        "small", description="SAM2 model checkpoint to use (tiny, small, base-plus, large)"),
    db: Session = Depends(get_db)
):
    # Check if video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Check if object exists
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    # Validate that object belongs to this video
    if obj.video_id != video_id:
        raise HTTPException(
            status_code=400, detail="Object does not belong to this video")

    # Create a new point for the object
    try:
        new_point = Point(
            object_id=object_id,
            x=x,
            y=y,
            label=label
        )
        db.add(new_point)
        db.commit()
        db.refresh(new_point)
        logger.info(
            f"Created new point for object {object_id}: x={x}, y={y}, label={label}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create point: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create point: {str(e)}")

    # Validate frames directory
    video_name = Path(video.file_path).stem
    base_frames_dir = public_frames_base_dir_with_video_name(video_name)
    if not base_frames_dir.exists():
        raise HTTPException(
            status_code=404, detail="Frames directory not found")

    # Count available frames
    available_frames = sorted(list(base_frames_dir.glob("*.jpg")))
    if not available_frames:
        raise HTTPException(
            status_code=404, detail="No frames found for this video")

    try:
        # Initialize SAM2 Inference API with specified checkpoint
        inference_api = InferenceAPI(checkpoint=checkpoint)
        inference_api.initialize_state(frames_dir=base_frames_dir)

        # Segment object using the newly created point
        try:
            _ = inference_api.segment_object(object_id, db=db)
            result_objects = [{
                "id": object_id,
                "name": obj.name,
                "color": obj.color,
                "segmented": True
            }]
        except Exception as e:
            logger.error(f"Failed to segment object {object_id}: {str(e)}")
            result_objects = [{
                "id": object_id,
                "name": obj.name,
                "color": obj.color,
                "segmented": False,
                "error": str(e)
            }]

        # Draw the segmentation masks on the frame
        try:
            inference_thumbnail_path = draw_objects_masks_on_frame(
                video_id, db=db)
            visualization_url = str(inference_thumbnail_path)
            return {
                "status": "success",
                "objects": result_objects,
                "visualization_url": visualization_url
            }
        except Exception as e:
            logger.error(f"Failed to draw masks on frame: {str(e)}")
            return {
                "status": "partial_success",
                "objects": result_objects,
                "error": str(e)
            }
    except Exception as e:
        logger.error(f"Failed to segment objects: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to segment objects: {str(e)}"
        )


# Endpoint to propagate masks through the entire video
@app.post("/api/v1/videos/{video_id}/propagate", response_model=dict)
async def propagate_video(
    video_id: int,
    checkpoint: str = Body(..., embed=True,
                           description="SAM2 model checkpoint to use (tiny, small, base-plus, large)"),
    db: Session = Depends(get_db)
):
    # Check if video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Get all objects for this video that have points
    objects_with_points = db.query(Object).filter(
        Object.video_id == video_id,
        exists().where(Point.object_id == Object.id)
    ).all()

    if not objects_with_points:
        raise HTTPException(
            status_code=400,
            detail="No objects with points found for this video. Add points to at least one object."
        )

    try:
        # Initialize SAM2 Inference API with specified checkpoint
        inference_api = InferenceAPI(checkpoint=checkpoint)

        # Call the propagate_in_video method
        output_video_path = inference_api.propagate_in_video(video_id, db=db)

        return {
            "status": "success",
            "video_path": output_video_path,
            "video_id": video_id
        }
    except Exception as e:
        logger.error(f"Failed to propagate masks in video: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to propagate masks in video: {str(e)}"
        )


# Endpoint to remove the last point from an object and run the inference again
@app.delete("/api/v1/videos/{video_id}/objects/{object_id}/points", response_model=dict)
async def remove_last_point(
    video_id: int,
    object_id: int,
    checkpoint: str = Body(
        "tiny", description="SAM2 model checkpoint to use (tiny, small, base-plus, large)"),
    db: Session = Depends(get_db)
):
    # Check if video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Check if object exists
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    # Validate that object belongs to this video
    if obj.video_id != video_id:
        raise HTTPException(
            status_code=400, detail="Object does not belong to this video")

    # Remove the last point from the object
    last_point = db.query(Point).filter(
        Point.object_id == object_id).order_by(Point.id.desc()).first()

    if last_point:
        db.delete(last_point)
        db.commit()
        logger.info(
            f"Removed last point {last_point.id} from object {object_id}")
    else:
        raise HTTPException(
            status_code=404, detail="No points found for this object")

    # Before drawing the masks on the frame, make the inference again with the left points
    try:
        inference_api = InferenceAPI(checkpoint=checkpoint)
        video_name = Path(video.file_path).stem
        inference_api.initialize_state(
            frames_dir=public_frames_base_dir_with_video_name(video_name))
        inference_api.segment_object(object_id, db=db)
    except Exception as e:
        logger.error(f"Failed to re-segment object {object_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to re-segment object {object_id}: {str(e)}"
        )

    # Draw the updated segmentation masks on the frame
    try:
        draw_objects_masks_on_frame(video_id, db=db)
    except Exception as e:
        logger.error(f"Failed to draw updated masks on frame: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to draw updated masks on frame: {str(e)}"
        )

    return {"status": "success", "message": "Last point removed successfully"}


# Endpoint to download the YOLO dataset ZIP file
@app.get("/api/v1/videos/{video_id}/download-yolo-dataset", response_class=FileResponse)
async def download_yolo_dataset(video_id: int, db: Session = Depends(get_db)):
    """
    Generate and download a YOLO dataset ZIP file for the specified video.
    """
    # Check if video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Get video name for the filename
    video_name = Path(video.file_name).stem

    try:
        # Generate the YOLO dataset ZIP file
        zip_path = create_yolo_dataset_zip(video_id, db)

        if not zip_path or not os.path.exists(zip_path):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate YOLO dataset"
            )

        # Return the file as a download with appropriate filename
        return FileResponse(
            path=zip_path,
            filename=f"{video_name}_yolo_dataset.zip",
            media_type="application/zip"
        )

    except Exception as e:
        logger.error(f"Failed to generate YOLO dataset: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate YOLO dataset: {str(e)}"
        )


# Endpoint to get the inference results (model checkpoint and dates) using the VideoInference model
@app.get("/api/v1/videos/{video_id}/inference_results", response_model=dict)
async def get_inference_results(video_id: int, db: Session = Depends(get_db)):
    # Check if video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Get inference results from the VideoInference model
    inference_results = db.query(VideoInference).filter(
        VideoInference.base_video_id == video_id).first()
    if not inference_results:
        raise HTTPException(
            status_code=404, detail="Inference results not found")

    # Get video inference metadata from Video table
    video_inference = db.query(Video).filter(
        Video.id == inference_results.inference_video_id).first()
    if not video_inference:
        raise HTTPException(
            status_code=404, detail="Inference video not found")

    # Get the number of frames in the inference video
    video_name = Path(video.file_name).stem
    inference_frames_dir = public_frames_inference_dir_with_video_name(
        video_name)

    if not inference_frames_dir.exists():
        raise HTTPException(
            status_code=404, detail="Inference frames directory not found")

    inference_frame_count = len(list(inference_frames_dir.glob("*.jpg")))
    if inference_frame_count == 0:
        raise HTTPException(
            status_code=404, detail="No frames found in the inference video")

    return {
        "original_video": video.file_name,
        "inference_video": video_inference.file_name,
        "model_checkpoint": inference_results.model_name,
        "fps": video_inference.fps,
        "frame_count": inference_frame_count,
        "created_at": inference_results.created_at.isoformat(),
        "updated_at": inference_results.updated_at.isoformat(),
    }

# Endpoint to delete a video, its frames, and its inference results


@app.delete("/api/v1/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    # Check if video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        # Delete the video
        db.delete(video)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to delete video {video_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete video {video_id}: {str(e)}"
        )

    # Delete all inference videos from the Video table associated with this video
    try:
        inference_videos = db.query(VideoInference).filter(
            VideoInference.base_video_id == video_id).all()
        for inference_video in inference_videos:
            db.delete(inference_video)
        db.commit()
    except Exception as e:
        logger.error(
            f"Failed to delete inference videos for video {video_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete inference videos for video {video_id}: {str(e)}"
        )

    # Delete the video directory, since it contains the frames and inference results
    video_name = Path(video.file_name).stem
    video_dir = public_videos_dir_with_video_name(video_name)
    if video_dir.exists():
        try:
            for item in video_dir.iterdir():
                if item.is_file():
                    item.unlink()
                else:
                    shutil.rmtree(item)
            video_dir.rmdir()  # Remove the directory itself
        except Exception as e:
            logger.error(
                f"Failed to delete video directory {video_name}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete video directory {video_name}: {str(e)}"
            )

    return {"status": "success", "message": "Video deleted successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
