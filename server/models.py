import os
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, LargeBinary
from db import Base


class Video(Base):
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False, unique=True)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)  # size in bytes
    width = Column(Integer)
    height = Column(Integer)
    fps = Column(Float)
    duration = Column(Float)  # duration in seconds
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc),
                        onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Video(file_name='{self.file_name}', resolution='{self.width}x{self.height}', fps={self.fps})>"


class Clip(Base):
    __tablename__ = 'clips'

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False)
    file_path = Column(String, nullable=False, unique=True)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)  # size in bytes
    width = Column(Integer)
    height = Column(Integer)
    fps = Column(Float)
    duration = Column(Float)  # duration in seconds
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc),
                        onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Clip(file_name='{self.file_name}', resolution='{self.width}x{self.height}', fps={self.fps})>"


class Object(Base):
    __tablename__ = 'objects'

    id = Column(Integer, primary_key=True)
    clip_id = Column(Integer, ForeignKey('clips.id'), nullable=False)
    name = Column(String, nullable=False)
    color = Column(String, nullable=False)
    mask = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


class Point(Base):
    __tablename__ = 'points'

    id = Column(Integer, primary_key=True)
    object_id = Column(Integer, ForeignKey('objects.id'), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    label = Column(Integer, nullable=False)  # 1 for positive, 0 for negative
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
