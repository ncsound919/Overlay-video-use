import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    aspect_ratio: str = "16:9"
    fps: float = 24.0


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    status: str
    aspect_ratio: str
    fps: float
    source_count: int = 0
    created_at: datetime.datetime
    updated_at: datetime.datetime
    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    id: int
    filename: str
    duration: float
    width: int
    height: int
    codec: str
    has_transcript: bool
    created_at: datetime.datetime
    class Config:
        from_attributes = True


class EDLRange(BaseModel):
    source: str
    start: float
    end: float
    beat: str = ""
    note: str = ""
    quote: str = ""


class EDLOverlay(BaseModel):
    file: str
    start_in_output: float
    duration: float


class EDLCreate(BaseModel):
    ranges: list[EDLRange]
    grade: str = ""
    overlays: list[EDLOverlay] = []


class EDLResponse(BaseModel):
    id: int
    project_id: int
    version: int
    grade: str
    total_duration_s: float
    ranges: list[dict]
    overlays: list[dict]
    subtitles: Optional[str]
    created_at: datetime.datetime
    class Config:
        from_attributes = True


class RenderCreate(BaseModel):
    preset: str = "youtube"


class RenderResponse(BaseModel):
    id: int
    project_id: int
    status: str
    preset: str
    width: int
    height: int
    duration_s: float
    file_size_mb: float
    error: Optional[str]
    output_path: Optional[str]
    created_at: datetime.datetime
    class Config:
        from_attributes = True


class TemplateCreate(BaseModel):
    name: str
    description: str = ""
    category: str = "custom"
    config: dict = Field(default_factory=dict)


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    config: dict
    created_at: Optional[datetime.datetime]
    class Config:
        from_attributes = True
