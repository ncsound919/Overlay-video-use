import json
import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from models import Project, Source, EDL
from schemas import EDLCreate, EDLResponse

router = APIRouter()


class AutoEditRequest(BaseModel):
    template: str = "talking_head"


@router.post("/{project_id}/auto-edit")
def auto_edit(project_id: int, req: AutoEditRequest, db: Session = Depends(get_db)):
    """Run the deterministic edit agent to generate an EDL from transcript."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    edit_dir = Path(f"{settings.project_dir}/{project_id}/edit")
    packed = edit_dir / "takes_packed.md"

    if not packed.exists():
        raise HTTPException(400, "No transcript found. Transcribe sources first.")

    agent_script = Path(__file__).parent.parent.parent / "helpers" / "agent.py"
    if not agent_script.exists():
        raise HTTPException(500, f"Agent script not found: {agent_script}")

    try:
        result = subprocess.run(
            [sys.executable, str(agent_script),
             "--edit-dir", str(edit_dir),
             "--template", req.template],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise HTTPException(500, f"Agent failed: {result.stderr[:500]}")

        # Load generated EDL
        edl_json_path = edit_dir / "edl.json"
        if not edl_json_path.exists():
            raise HTTPException(500, "Agent ran but produced no EDL")

        edl_data = json.loads(edl_json_path.read_text())

        # Save to DB
        existing = db.query(EDL).filter(EDL.project_id == project_id).first()
        if existing:
            db.delete(existing)

        db_edl = EDL(
            project_id=project_id,
            version=1,
            grade=edl_data.get("grade", ""),
            total_duration_s=edl_data.get("total_duration_s", 0),
            ranges=edl_data.get("ranges", []),
            overlays=edl_data.get("overlays", []),
            subtitles=edl_data.get("subtitles", ""),
        )
        db.add(db_edl)
        project.status = "editing"
        db.commit()
        db.refresh(db_edl)

        print(f"Agent output:\n{result.stdout}")
        return db_edl

    except subprocess.TimeoutExpired:
        raise HTTPException(500, "Agent timed out after 120s")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Agent error: {str(e)}")


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
    edl_json_path = Path(f"{settings.project_dir}/{project_id}/edit/edl.json")
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
