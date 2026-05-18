from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from models import Project, Source, User
from auth import get_current_user
from services.audio_service import full_audio_cleanup, remove_silence, reduce_noise, run_bass_boost, run_studio_polish

router = APIRouter()


class AudioCleanupRequest(BaseModel):
    mode: str = "full"
    silence_duration: float = 0.5
    silence_threshold: float = -35.0
    noise_strength: float = 0.3


@router.post("/{project_id}/sources/{source_id}/cleanup")
def cleanup_audio(project_id: int, source_id: int, req: AudioCleanupRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
        
    base_dir = Path(settings.render_dir).resolve()
    output_dir = Path(f"{settings.render_dir}/{project_id}").resolve()
    if not str(output_dir).startswith(str(base_dir)):
        raise HTTPException(400, "Path traversal attempt detected")
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(source.filepath).stem
    output_path = str(output_dir / f"{stem}_cleaned.mp4")
    if req.mode == "full":
        result = full_audio_cleanup(source.filepath, output_path)
    elif req.mode == "silence":
        result = remove_silence(source.filepath, output_path, req.silence_duration, req.silence_threshold)
    elif req.mode == "noise":
        result = reduce_noise(source.filepath, output_path, req.noise_strength)
    elif req.mode == "bass_boost":
        result = run_bass_boost(source.filepath, output_path)
    elif req.mode == "studio_polish":
        result = run_studio_polish(source.filepath, output_path)
    else:
        raise HTTPException(400, f"Unknown mode: {req.mode}")
    return result
