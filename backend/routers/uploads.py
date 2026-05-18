from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Project, Source, User
from schemas import SourceResponse
from services.upload_service import save_upload
from auth import get_current_user
from config import settings

router = APIRouter()


@router.post("/{project_id}", response_model=SourceResponse)
async def upload_file(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if project_id <= 0:
        raise HTTPException(400, "Invalid project ID")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if settings.auth_enabled and current_user and project.user_id != current_user.id:
        raise HTTPException(403, "You do not have access to this project")
        
    # Double-layer content-type protection
    if file.content_type and not (file.content_type.startswith("video/") or file.content_type.startswith("audio/")):
        raise HTTPException(400, "Unsupported media type. Only video and audio uploads are allowed.")
        
    try:
        info = await save_upload(file, project_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(400, str(e))
    source = Source(
        project_id=project_id,
        filename=info["filename"],
        filepath=info["filepath"],
        duration=info["duration"],
        width=info["width"],
        height=info["height"],
        codec=info["codec"],
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/{project_id}", response_model=list[SourceResponse])
def list_sources(
    project_id: int, 
    limit: int = 100, 
    offset: int = 0, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if settings.auth_enabled and current_user and project.user_id != current_user.id:
        raise HTTPException(403, "You do not have access to this project")
    return db.query(Source).filter(Source.project_id == project_id).limit(limit).offset(offset).all()
