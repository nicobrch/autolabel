from fastapi import FastAPI, Depends
import uvicorn
from sqlalchemy.orm import Session

from db import get_db, create_tables
from models import Video, Clip
from utils import time_to_seconds
from fastapi import File, UploadFile, HTTPException
import os
from pathlib import Path
import subprocess
import json
import sys
import random
import string

app = FastAPI(title="Simple FastAPI App")


@app.on_event("startup")
async def startup():
    # Initialize database
    create_tables()


@app.get("/api/v1/")
async def root():
    return {"message": "Hello World"}


@app.get("/api/v1/videos")
async def list_videos(db: Session = Depends(get_db)):
    videos = db.query(Video).all()
    if not videos:
        return {"error": "No videos found"}
    return videos


@app.get("/api/v1/videos/{video_id}")
async def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        return {"error": "Video not found"}
    return video


@app.post("/api/v1/videos/upload")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type.startswith("video/"):
        return {"error": "File must be a video"}

    # Create videos directory if it doesn't exist
    videos_dir = Path("videos")
    videos_dir.mkdir(exist_ok=True)

    # Save the file
    file_path = videos_dir / file.filename
    with open(file_path, "wb") as buffer:
        contents = await file.read()
        buffer.write(contents)

    # Get video metadata using ffprobe
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,duration",
            "-of", "json",
            str(file_path)
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
        file_size = os.path.getsize(file_path)

    except (subprocess.SubprocessError, json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Error extracting video metadata: {e}", file=sys.stderr)
        width, height, fps, duration = 0, 0, 0, 0
        file_size = os.path.getsize(
            file_path) if os.path.exists(file_path) else 0

    # Create a new video entry in the database with metadata
    new_video = Video(
        file_path=str(file_path),
        file_name=file.filename,
        file_size=file_size,
        width=width,
        height=height,
        fps=fps,
        duration=duration
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    return {"message": "Video uploaded successfully", "video_id": new_video.id}


@app.post("/api/v1/clips/create")
async def create_clip(video_id: int, start_time: str, end_time: str, db: Session = Depends(get_db)):
    # Validate and convert time parameters
    try:
        start_seconds = time_to_seconds(start_time)
        end_seconds = time_to_seconds(end_time)

        if start_seconds >= end_seconds:
            raise HTTPException(
                status_code=400, detail="End time must be after start time")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Find the source video
    source_video = db.query(Video).filter(Video.id == video_id).first()
    if not source_video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Check if source video exists on disk
    if not os.path.exists(source_video.file_path):
        raise HTTPException(
            status_code=404, detail="Source video file not found on disk")

    # Generate random 6-letter suffix for the clip name
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))

    # Create clips directory if it doesn't exist
    clips_dir = Path("clips")
    clips_dir.mkdir(exist_ok=True)

    # Prepare clip filename (preserve extension)
    file_base, file_ext = os.path.splitext(source_video.file_name)
    clip_filename = f"{file_base}_{random_suffix}{file_ext}"
    clip_path = clips_dir / clip_filename

    # Use ffmpeg to cut the video - use time strings directly
    try:
        cmd = [
            "ffmpeg",
            "-i", source_video.file_path,
            "-ss", start_time,  # Use time string format directly with ffmpeg
            "-to", end_time,    # Use time string format directly with ffmpeg
            "-c", "copy",       # Use copy codec for fast clipping without re-encoding
            str(clip_path),
            "-y"                # Overwrite output file if it exists
        ]

        subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Get clip metadata
        probe_cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,duration",
            "-of", "json",
            str(clip_path)
        ]

        result = subprocess.run(
            probe_cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)

        # Extract metadata
        stream = metadata.get("streams", [{}])[0]
        width = int(stream.get("width", 0))
        height = int(stream.get("height", 0))

        # Parse framerate
        fps = 0
        if "r_frame_rate" in stream:
            rate_parts = stream["r_frame_rate"].split("/")
            if len(rate_parts) == 2 and int(rate_parts[1]) != 0:
                fps = float(int(rate_parts[0]) / int(rate_parts[1]))

        # Get duration
        duration = float(stream.get("duration", 0))

        # Get file size
        file_size = os.path.getsize(clip_path)

    except (subprocess.SubprocessError, json.JSONDecodeError, ValueError, KeyError) as e:
        # Clean up the incomplete file if it exists
        if os.path.exists(clip_path):
            os.remove(clip_path)
        print(f"Error creating clip: {e}", file=sys.stderr)
        raise HTTPException(
            status_code=500, detail=f"Failed to create clip: {str(e)}")

    # Create a new clip entry in the database
    new_clip = Clip(
        video_id=video_id,
        file_path=str(clip_path),
        file_name=clip_filename,
        file_size=file_size,
        width=width,
        height=height,
        fps=fps,
        duration=duration
    )

    db.add(new_clip)
    db.commit()
    db.refresh(new_clip)

    return {
        "message": "Clip created successfully",
        "clip_id": new_clip.id,
        "clip_details": {
            "file_name": new_clip.file_name,
            "duration": new_clip.duration,
            "path": new_clip.file_path,
            "start_time": start_time,
            "end_time": end_time
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
