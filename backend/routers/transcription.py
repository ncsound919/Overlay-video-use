from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from config import settings
from database import get_db
from models import Project, Source, User
from services.transcribe_service import transcribe_with_elevenlabs, transcribe_with_whisper
from auth import get_current_user

router = APIRouter()


class TranscribeRequest(BaseModel):
    engine: str = "elevenlabs"
    num_speakers: Optional[int] = None
    whisper_model: str = "base"


@router.post("/{project_id}/sources/{source_id}")
def transcribe_source(project_id: int, source_id: int, req: TranscribeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    if req.engine not in ("elevenlabs", "whisper"):
        raise HTTPException(400, f"Unknown engine: {req.engine}. Use 'elevenlabs' or 'whisper'.")
    base_dir = Path(settings.project_dir).resolve()
    project_dir = Path(f"{settings.project_dir}/{project_id}").resolve()
    if not str(project_dir).startswith(str(base_dir)):
        raise HTTPException(400, "Path traversal attempt detected")
    try:
        if req.engine == "elevenlabs":
            tr_path = transcribe_with_elevenlabs(source.filepath, project_dir, req.num_speakers)
        else:
            tr_path = transcribe_with_whisper(source.filepath, project_dir, req.whisper_model)
        source.has_transcript = True
        source.transcript_path = tr_path
        db.commit()

        try:
            import subprocess, sys
            pack_script = Path(__file__).parent.parent.parent / "helpers" / "pack_transcripts.py"
            edit_dir = Path(f"{settings.project_dir}/{project_id}/edit")
            edit_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [sys.executable, str(pack_script), "--edit-dir", str(edit_dir)],
                capture_output=True, text=True, timeout=30,
            )
        except Exception:
            pass

        return {"ok": True, "transcript_path": tr_path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Transcription failed: {str(e)}")


@router.get("/{project_id}/sources/{source_id}/transcript")
def get_transcript(project_id: int, source_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if project_id <= 0:
        raise HTTPException(400, "Invalid project ID")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if settings.auth_enabled and current_user and project.user_id != current_user.id:
        raise HTTPException(403, "You do not have access to this project")

    source = db.query(Source).filter(Source.id == source_id, Source.project_id == project_id).first()
    if not source or not source.transcript_path:
        raise HTTPException(404, "Transcript not found")
    import json
    data = json.loads(Path(source.transcript_path).read_text())
    return data
