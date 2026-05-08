from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Project, Render
from services.export_service import get_presets, apply_export_preset, extract_clip

router = APIRouter()


class ExportRequest(BaseModel):
    preset: str = "youtube"


class ClipExtractRequest(BaseModel):
    start: float
    end: float
    preset: str = "tiktok"


@router.get("/presets")
def list_export_presets():
    return get_presets()


@router.post("/{project_id}/export")
def export_video(project_id: int, req: ExportRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    render = db.query(Render).filter(Render.project_id == project_id, Render.status == "complete").order_by(Render.created_at.desc()).first()
    if not render:
        raise HTTPException(400, "No completed render found. Render first.")
    output_dir = Path(f"backend/data/renders/{project_id}/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"export_{req.preset}_{Path(render.output_path).stem}.mp4")
    result = apply_export_preset(render.output_path, output_path, req.preset)
    return result


@router.post("/{project_id}/clip")
def extract_clip_endpoint(project_id: int, req: ClipExtractRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    render = db.query(Render).filter(Render.project_id == project_id, Render.status == "complete").order_by(Render.created_at.desc()).first()
    if not render:
        raise HTTPException(400, "No completed render found")
    output_dir = Path(f"backend/data/renders/{project_id}/clips")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"clip_{req.preset}_{int(req.start)}-{int(req.end)}.mp4")
    result = extract_clip(render.output_path, output_path, req.start, req.end, req.preset)
    return result
