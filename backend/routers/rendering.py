from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Project, Render
from schemas import RenderResponse
from services.render_service import run_render

router = APIRouter()


class RenderRequest(BaseModel):
    preset: str = "youtube"


@router.post("/{project_id}/render")
def start_render(project_id: int, req: RenderRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    result = run_render(project_id, req.preset)
    if "error" in result:
        render = Render(project_id=project_id, status="failed", preset=req.preset, error=result["error"])
        db.add(render)
        db.commit()
        db.refresh(render)
        raise HTTPException(500, result["error"])
    render = Render(project_id=project_id, status="complete", preset=req.preset,
                    output_path=result["output_path"], width=result["width"], height=result["height"],
                    duration_s=result["duration_s"], file_size_mb=result["file_size_mb"])
    db.add(render)
    project.status = "complete"
    db.commit()
    db.refresh(render)
    return render


@router.get("/{project_id}/renders", response_model=list[RenderResponse])
def list_renders(project_id: int, db: Session = Depends(get_db)):
    return db.query(Render).filter(Render.project_id == project_id).order_by(Render.created_at.desc()).all()
