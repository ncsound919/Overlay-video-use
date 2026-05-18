from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Project, Source, User
from schemas import ProjectCreate, ProjectResponse
from auth import get_current_user
from services.cleanup_service import delete_project_assets
from config import settings

router = APIRouter()


@router.get("/", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Project)
    if settings.auth_enabled and current_user:
        query = query.filter(Project.user_id == current_user.id)
    projects = query.order_by(Project.updated_at.desc()).all()
    result = []
    for p in projects:
        count = db.query(Source).filter(Source.project_id == p.id).count()
        result.append(ProjectResponse(
            id=p.id, name=p.name, description=p.description or "",
            status=p.status, aspect_ratio=p.aspect_ratio, fps=p.fps,
            source_count=count,
            created_at=p.created_at, updated_at=p.updated_at,
        ))
    return result


@router.post("/", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid = current_user.id if current_user else None
    project = Project(name=data.name, description=data.description, aspect_ratio=data.aspect_ratio, fps=data.fps, user_id=uid)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectResponse(
        id=project.id, name=project.name, description=project.description or "",
        status=project.status, aspect_ratio=project.aspect_ratio, fps=project.fps,
        source_count=0, created_at=project.created_at, updated_at=project.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if settings.auth_enabled and current_user and project.user_id != current_user.id:
        raise HTTPException(403, "You do not have access to this project")
    count = db.query(Source).filter(Source.project_id == project_id).count()
    return ProjectResponse(
        id=project.id, name=project.name, description=project.description or "",
        status=project.status, aspect_ratio=project.aspect_ratio, fps=project.fps,
        source_count=count, created_at=project.created_at, updated_at=project.updated_at,
    )


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if settings.auth_enabled and current_user and project.user_id != current_user.id:
        raise HTTPException(403, "You do not have access to this project")
    db.delete(project)
    db.commit()
    delete_project_assets(project_id)
    return {"ok": True}
