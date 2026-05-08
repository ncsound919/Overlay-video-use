from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Project, Source
from schemas import SourceResponse
from services.upload_service import save_upload

router = APIRouter()


@router.post("/{project_id}", response_model=SourceResponse)
async def upload_file(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        from fastapi import HTTPException
        raise HTTPException(404, "Project not found")
    info = await save_upload(file, project_id)
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
def list_sources(project_id: int, db: Session = Depends(get_db)):
    return db.query(Source).filter(Source.project_id == project_id).all()
