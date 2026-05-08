from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Project, Source
from services.reframe_service import auto_reframe

router = APIRouter()


class ReframeRequest(BaseModel):
    target_aspect: str = "9:16"
    mode: str = "crop"


@router.post("/{project_id}/sources/{source_id}/reframe")
def reframe_video(project_id: int, source_id: int, req: ReframeRequest, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id, Source.project_id == project_id).first()
    if not source:
        raise HTTPException(404, "Source not found")
    output_dir = Path(f"backend/data/renders/{project_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"reframed_{req.target_aspect.replace(':', '_')}_{Path(source.filepath).stem}.mp4")
    result = auto_reframe(source.filepath, output_path, req.target_aspect, req.mode)
    return result
