import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="draft")
    aspect_ratio = Column(String(10), default="16:9")
    fps = Column(Float, default=24.0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sources = relationship("Source", back_populates="project", cascade="all, delete-orphan")
    edl = relationship("EDL", back_populates="project", uselist=False, cascade="all, delete-orphan")
    renders = relationship("Render", back_populates="project", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    duration = Column(Float, default=0.0)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    codec = Column(String(50), default="")
    has_transcript = Column(Boolean, default=False)
    transcript_path = Column(String(500))
    created_at = Column(DateTime, default=_utcnow)
    project = relationship("Project", back_populates="sources")


class EDL(Base):
    __tablename__ = "edls"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    version = Column(Integer, default=1)
    grade = Column(String(100), default="")
    total_duration_s = Column(Float, default=0.0)
    ranges = Column(JSON, default=list)
    overlays = Column(JSON, default=list)
    subtitle_style = Column(String(100), default="clean_minimal")
    subtitles = Column(String(500))
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    project = relationship("Project", back_populates="edl")


class Render(Base):
    __tablename__ = "renders"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status = Column(String(50), default="pending")
    output_path = Column(String(500))
    preset = Column(String(50), default="youtube")
    width = Column(Integer, default=1920)
    height = Column(Integer, default=1080)
    duration_s = Column(Float, default=0.0)
    file_size_mb = Column(Float, default=0.0)
    error = Column(Text)
    created_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime)
    project = relationship("Project", back_populates="renders")


class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    category = Column(String(50), default="custom")
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
