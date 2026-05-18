from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Project, Source, User
from services.scene_service import detect_with_pyscenedetect
from auth import get_current_user
from config import settings

router = APIRouter()


@router.post("/{project_id}/sources/{source_id}/detect")
def detect_scenes(project_id: int, source_id: int, threshold: float = 30.0, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if project_id <= 0:
        raise HTTPException(400, "Invalid project ID")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if settings.auth_enabled and current_user and project.user_id != current_user.id:
        raise HTTPException(403, "You do not have access to this project")

    source = db.query(Source).filter(Source.id == source_id, Source.project_id == project_id).first()
    if not source:
        raise HTTPException(404, "Source not found")
    scenes = detect_with_pyscenedetect(source.filepath, threshold)
    return {"scenes": scenes, "count": len(scenes)}
