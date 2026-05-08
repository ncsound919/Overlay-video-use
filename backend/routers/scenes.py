from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Project, Source
from services.scene_service import detect_with_pyscenedetect

router = APIRouter()


@router.post("/{project_id}/sources/{source_id}/detect")
def detect_scenes(project_id: int, source_id: int, threshold: float = 30.0, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id, Source.project_id == project_id).first()
    if not source:
        raise HTTPException(404, "Source not found")
    scenes = detect_with_pyscenedetect(source.filepath, threshold)
    return {"scenes": scenes, "count": len(scenes)}
