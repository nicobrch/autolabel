from fastapi import FastAPI, Depends
import uvicorn
from sqlalchemy.orm import Session

from db import get_db, create_tables
from models import Video
from utils import time_to_seconds, extract_video_metadata
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

    metadata = extract_video_metadata(file_path)
    if not metadata:
        raise HTTPException(
            status_code=500, detail="Failed to extract video metadata")
    width = metadata.get("width")
    height = metadata.get("height")
    fps = metadata.get("fps")
    duration = metadata.get("duration")
    file_size = metadata.get("file_size")

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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
