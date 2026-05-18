from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Project, Source, User
from schemas import SourceResponse
from services.upload_service import save_upload
from auth import get_current_user

router = APIRouter()


@router.post("/{project_id}", response_model=SourceResponse)
async def upload_file(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if project_id <= 0:
        raise HTTPException(400, "Invalid project ID")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
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
def list_sources(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Source).filter(Source.project_id == project_id).all()
