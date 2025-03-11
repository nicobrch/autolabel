from fastapi import FastAPI, Depends
import uvicorn
from sqlalchemy.orm import Session

from db import get_db, create_tables
from models import Video
from fastapi import File, UploadFile
import os
from pathlib import Path
import subprocess
import json
import sys

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
