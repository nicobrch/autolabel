from fastapi import FastAPI, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from db import get_db, create_tables
from models import Project, Video, Frame, Object, Mask, Point
from utils import extract_video_metadata, extract_frames_at_frame_step, sqlalchemy_to_dict
from fastapi import File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
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
    create_tables()


@app.get("/api/v1/")
async def root():
    return {"message": "AutoLabel API is running"}

# -------------- Project CRUD Operations --------------


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
    # Check if a project with the same name already exists
    existing_project = db.query(Project).filter(Project.name == name).first()
    if existing_project:
        raise HTTPException(
            status_code=400, detail="Project with this name already exists")

    new_project = Project(name=name, description=description)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return sqlalchemy_to_dict(new_project)


@app.put("/api/v1/projects/{project_id}", response_model=dict)
async def update_project(
    project_id: int,
    name: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if name is not None:
        # Check if another project with the same name exists
        existing_project = db.query(Project).filter(
            Project.name == name, Project.id != project_id).first()
        if existing_project:
            raise HTTPException(
                status_code=400, detail="Project with this name already exists")
        project.name = name

    if description is not None:
        project.description = description

    db.commit()
    db.refresh(project)
    return sqlalchemy_to_dict(project)


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

# -------------- Video CRUD Operations --------------


@app.get("/api/v1/videos", response_model=List[dict])
async def list_videos(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Video)
    if project_id:
        query = query.filter(Video.project_id == project_id)

    videos = query.offset(skip).limit(limit).all()
    return [sqlalchemy_to_dict(video) for video in videos]


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
        project_id=project_id,
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

    return sqlalchemy_to_dict(new_video)


@app.delete("/api/v1/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Delete the physical file
    try:
        if Path(video.file_path).exists():
            Path(video.file_path).unlink()
    except Exception as e:
        # Log the error but continue with DB deletion
        pass

    db.delete(video)
    db.commit()
    return None

# -------------- Frame CRUD Operations --------------


@app.get("/api/v1/frames", response_model=List[dict])
async def list_frames(
    video_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Frame)
    if video_id:
        query = query.filter(Frame.video_id == video_id)

    frames = query.offset(skip).limit(limit).all()
    return [sqlalchemy_to_dict(frame) for frame in frames]


@app.get("/api/v1/frames/{frame_id}", response_model=dict)
async def get_frame(frame_id: int, db: Session = Depends(get_db)):
    frame = db.query(Frame).filter(Frame.id == frame_id).first()
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")
    return sqlalchemy_to_dict(frame)


@app.post("/api/v1/videos/{video_id}/extract_frames", response_model=dict)
async def extract_frames(
    video_id: int,
    frame_step: int = Query(10, description="Extract every Nth frame"),
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    frames_dir = extract_frames_at_frame_step(video.file_path, frame_step, db)
    if not frames_dir:
        raise HTTPException(status_code=500, detail="Failed to extract frames")

    # Count how many frames were extracted
    frame_count = db.query(Frame).filter(Frame.video_id == video_id).count()

    return {
        "message": "Frames extracted successfully",
        "video_id": video_id,
        "frames_count": frame_count,
        "frames_directory": str(frames_dir)
    }


@app.delete("/api/v1/frames/{frame_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_frame(frame_id: int, db: Session = Depends(get_db)):
    frame = db.query(Frame).filter(Frame.id == frame_id).first()
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")

    # Delete the physical file
    try:
        if Path(frame.file_path).exists():
            Path(frame.file_path).unlink()
    except Exception as e:
        # Log the error but continue with DB deletion
        pass

    db.delete(frame)
    db.commit()
    return None

# -------------- Object CRUD Operations --------------


@app.get("/api/v1/objects", response_model=List[dict])
async def list_objects(
    video_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Object)
    if video_id:
        query = query.filter(Object.video_id == video_id)

    objects = query.offset(skip).limit(limit).all()
    return [sqlalchemy_to_dict(obj) for obj in objects]


@app.get("/api/v1/objects/{object_id}", response_model=dict)
async def get_object(object_id: int, db: Session = Depends(get_db)):
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    return sqlalchemy_to_dict(obj)


@app.post("/api/v1/videos/{video_id}/objects", response_model=dict)
async def create_object(
    video_id: int,
    name: str = Body(...),
    color: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Generate random color if not provided
    if not color:
        import numpy as np
        r = np.random.randint(0, 255)
        g = np.random.randint(0, 255)
        b = np.random.randint(0, 255)
        color = f"#{r:02x}{g:02x}{b:02x}"

    new_object = Object(
        video_id=video_id,
        name=name,
        color=color
    )
    db.add(new_object)
    db.commit()
    db.refresh(new_object)
    return sqlalchemy_to_dict(new_object)


@app.put("/api/v1/objects/{object_id}", response_model=dict)
async def update_object(
    object_id: int,
    name: Optional[str] = Body(None),
    color: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    if name is not None:
        obj.name = name

    if color is not None:
        obj.color = color

    db.commit()
    db.refresh(obj)
    return sqlalchemy_to_dict(obj)


@app.delete("/api/v1/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(object_id: int, db: Session = Depends(get_db)):
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    db.delete(obj)
    db.commit()
    return None

# -------------- Point CRUD Operations --------------


@app.get("/api/v1/points", response_model=List[dict])
async def list_points(
    object_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Point)
    if object_id:
        query = query.filter(Point.object_id == object_id)

    points = query.offset(skip).limit(limit).all()
    return [sqlalchemy_to_dict(point) for point in points]


@app.get("/api/v1/points/{point_id}", response_model=dict)
async def get_point(point_id: int, db: Session = Depends(get_db)):
    point = db.query(Point).filter(Point.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="Point not found")
    return sqlalchemy_to_dict(point)


@app.post("/api/v1/objects/{object_id}/points", response_model=dict)
async def create_point(
    object_id: int,
    x: int = Body(...),
    y: int = Body(...),
    label: int = Body(..., description="1 for positive, 0 for negative"),
    db: Session = Depends(get_db)
):
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    if label not in [0, 1]:
        raise HTTPException(status_code=400, detail="Label must be 0 or 1")

    new_point = Point(
        object_id=object_id,
        x=x,
        y=y,
        label=label
    )
    db.add(new_point)
    db.commit()
    db.refresh(new_point)
    return sqlalchemy_to_dict(new_point)


@app.put("/api/v1/points/{point_id}", response_model=dict)
async def update_point(
    point_id: int,
    x: Optional[int] = Body(None),
    y: Optional[int] = Body(None),
    label: Optional[int] = Body(None),
    db: Session = Depends(get_db)
):
    point = db.query(Point).filter(Point.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="Point not found")

    if x is not None:
        point.x = x

    if y is not None:
        point.y = y

    if label is not None:
        if label not in [0, 1]:
            raise HTTPException(status_code=400, detail="Label must be 0 or 1")
        point.label = label

    db.commit()
    db.refresh(point)
    return sqlalchemy_to_dict(point)


@app.delete("/api/v1/points/{point_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_point(point_id: int, db: Session = Depends(get_db)):
    point = db.query(Point).filter(Point.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="Point not found")

    db.delete(point)
    db.commit()
    return None

# -------------- Mask CRUD Operations --------------


@app.get("/api/v1/masks", response_model=List[dict])
async def list_masks(
    object_id: Optional[int] = None,
    frame_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Mask)
    if object_id:
        query = query.filter(Mask.object_id == object_id)
    if frame_id:
        query = query.filter(Mask.frame_id == frame_id)

    masks = query.offset(skip).limit(limit).all()
    return [sqlalchemy_to_dict(mask) for mask in masks]


@app.get("/api/v1/masks/{mask_id}")
async def get_mask(mask_id: int, db: Session = Depends(get_db)):
    mask = db.query(Mask).filter(Mask.id == mask_id).first()
    if not mask:
        raise HTTPException(status_code=404, detail="Mask not found")
    return sqlalchemy_to_dict(mask)


@app.delete("/api/v1/masks/{mask_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mask(mask_id: int, db: Session = Depends(get_db)):
    mask = db.query(Mask).filter(Mask.id == mask_id).first()
    if not mask:
        raise HTTPException(status_code=404, detail="Mask not found")

    db.delete(mask)
    db.commit()
    return None


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
