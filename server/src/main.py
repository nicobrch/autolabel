from fastapi import FastAPI, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from db import get_db, init_db
from models import Project, Video
from utils import logger, extract_video_metadata, extract_frames_at_frame_step, sqlalchemy_to_dict
from fastapi import File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import subprocess
import uvicorn

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


@app.on_event("startup")
async def startup():
    # Initialize database
    init_db()
    logger.info("Application started and database initialized")


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

    videos = db.query(Video).filter(Video.project_id == project_id).all()
    return [sqlalchemy_to_dict(video) for video in videos]


@app.post("/api/v1/videos/upload", response_model=dict)
async def upload_video(
    file: UploadFile = File(...),
    project_id: int = Query(...,
                            description="Project ID to associate with this video"),
    resolution: Optional[str] = Query(
        None, description="Resolution to resize the video, e.g., '1280x720'"),
    frame_step: Optional[int] = Query(
        10, description="Frame skip value for video processing"),
    db: Session = Depends(get_db)
):
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    # Create videos directory if it doesn't exist
    videos_dir = Path("videos")
    videos_dir.mkdir(exist_ok=True)

    # Save the original file temporarily
    temp_file_path = videos_dir / f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)
    except IOError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save video file: {e}")

    # Define the final file path
    file_path = videos_dir / file.filename

    # Resize video if resolution is provided and not "Original"
    if resolution and resolution.lower() != "original":
        import re
        if not re.match(r'^\d+x\d+$', resolution):
            # Clean up temp file
            if temp_file_path.exists():
                temp_file_path.unlink()
            raise HTTPException(
                status_code=400, detail=f"Invalid resolution format: {resolution}. Must be 'WIDTHxHEIGHT'")

        try:
            # Use ffmpeg to resize the video and remove audio track
            cmd = [
                "ffmpeg",
                "-i", str(temp_file_path),
                "-vf", f"scale={resolution}",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-an",  # Remove audio track to save disk space
                str(file_path)
            ]

            subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

            # Delete temporary file after successful resize
            if temp_file_path.exists():
                temp_file_path.unlink()

        except subprocess.SubprocessError as e:
            # Clean up temp file if resize fails
            if temp_file_path.exists():
                temp_file_path.unlink()
            raise HTTPException(
                status_code=500, detail=f"Failed to resize video: {e}")
    else:
        # Just rename the temp file to the final file name if no resize needed
        temp_file_path.rename(file_path)

    # Extract metadata from the final video file
    metadata = extract_video_metadata(file_path)
    if not metadata:
        # Clean up the saved file if metadata extraction fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500, detail="Failed to extract video metadata")

    width = metadata.get("width")
    height = metadata.get("height")
    fps = metadata.get("fps")
    duration = metadata.get("duration")
    file_size = metadata.get("file_size")

    # Create a new video entry in the database with metadata
    new_video = Video(
        project_id=project_id,
        file_path=str(file_path),
        file_name=file.filename,
        file_size=file_size,
        width=width,
        height=height,
        fps=fps,
        duration=duration,
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)
    logger.info(f"Video {file.filename} uploaded and metadata extracted.")

    # Extract frames at the specified frame step
    try:
        extract_frames_at_frame_step(file_path, frame_step, db)
    except Exception as e:
        # Clean up the saved video file if frame extraction fails
        if file_path.exists():
            file_path.unlink()
        db.delete(new_video)
        db.commit()
        raise HTTPException(
            status_code=500, detail=f"Failed to extract frames: {e}")

    return sqlalchemy_to_dict(new_video)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
