from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import DeclarativeBase


# Create declarative base
class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc),
                        onupdate=datetime.now(timezone.utc))


class Video(Base):
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey(
        'projects.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False, unique=True)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)  # size in bytes
    width = Column(Integer)
    height = Column(Integer)
    fps = Column(Float)
    duration = Column(Float)  # duration in seconds
    type = Column(String)  # e.g., "base", "inference"
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc),
                        onupdate=datetime.now(timezone.utc))


class VideoInference(Base):
    __tablename__ = 'video_inference'

    id = Column(Integer, primary_key=True)
    base_video_id = Column(Integer, ForeignKey(
        'videos.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    inference_video_id = Column(Integer, ForeignKey(
        'videos.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    model_name = Column(String, nullable=False)  # e.g., "sam2-tiny"
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc),
                        onupdate=datetime.now(timezone.utc))


class Frame(Base):
    __tablename__ = 'frames'

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey(
        'videos.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc),
                        onupdate=datetime.now(timezone.utc))


class Object(Base):
    __tablename__ = 'objects'

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey(
        'videos.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    color = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


class Mask(Base):
    __tablename__ = 'masks'

    id = Column(Integer, primary_key=True)
    object_id = Column(Integer, ForeignKey(
        'objects.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    mask = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc),
                        onupdate=datetime.now(timezone.utc))


class Point(Base):
    __tablename__ = 'points'

    id = Column(Integer, primary_key=True)
    object_id = Column(Integer, ForeignKey(
        'objects.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    label = Column(Integer, nullable=False)  # 1 for positive, 0 for negative
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
