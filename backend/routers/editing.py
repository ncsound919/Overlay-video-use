import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Project, Source, EDL
from schemas import EDLCreate, EDLResponse

router = APIRouter()


@router.post("/{project_id}/edl", response_model=EDLResponse)
def create_edl(project_id: int, data: EDLCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    existing = db.query(EDL).filter(EDL.project_id == project_id).first()
    if existing:
        db.delete(existing)
    ranges_json = []
    total_duration = 0.0
    for r in data.ranges:
        ranges_json.append({
            "source": r.source, "start": r.start, "end": r.end,
            "beat": r.beat, "note": r.note, "quote": r.quote,
        })
        total_duration += r.end - r.start
    overlays_json = [{"file": o.file, "start_in_output": o.start_in_output, "duration": o.duration} for o in data.overlays]
    edl = EDL(project_id=project_id, version=1, grade=data.grade, total_duration_s=total_duration,
              ranges=ranges_json, overlays=overlays_json)
    db.add(edl)
    db.commit()
    db.refresh(edl)
    edl_json_path = Path(f"backend/data/projects/{project_id}/edit/edl.json")
    edl_json_path.parent.mkdir(parents=True, exist_ok=True)
    edl_json = {
        "version": 1,
        "sources": {s.filename: s.filepath for s in db.query(Source).filter(Source.project_id == project_id).all()},
        "ranges": ranges_json, "grade": data.grade, "overlays": overlays_json,
        "total_duration_s": total_duration, "subtitles": "master.srt",
    }
    edl_json_path.write_text(json.dumps(edl_json, indent=2))
    project.status = "editing"
    db.commit()
    return edl


@router.get("/{project_id}/edl", response_model=EDLResponse)
def get_edl(project_id: int, db: Session = Depends(get_db)):
    edl = db.query(EDL).filter(EDL.project_id == project_id).first()
    if not edl:
        raise HTTPException(404, "EDL not found")
    return edl


@router.delete("/{project_id}/edl")
def delete_edl(project_id: int, db: Session = Depends(get_db)):
    edl = db.query(EDL).filter(EDL.project_id == project_id).first()
    if not edl:
        raise HTTPException(404, "EDL not found")
    db.delete(edl)
    db.commit()
    return {"ok": True}
