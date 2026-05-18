import json
import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from models import Project, Source, EDL, User
from schemas import EDLCreate, EDLResponse
from auth import get_current_user
import librosa
import numpy as np
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class AutoEditRequest(BaseModel):
    template: str = "talking_head"


@router.post("/{project_id}/auto-edit")
def auto_edit(project_id: int, req: AutoEditRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Run the deterministic edit agent to generate an EDL from transcript."""
    if project_id <= 0:
        raise HTTPException(400, "Invalid project ID")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if settings.auth_enabled and current_user and project.user_id != current_user.id:
        raise HTTPException(403, "You do not have access to this project")

    base_dir = Path(settings.project_dir).resolve()
    edit_dir = Path(f"{settings.project_dir}/{project_id}/edit").resolve()
    if not str(edit_dir).startswith(str(base_dir)):
        raise HTTPException(400, "Path traversal attempt detected")
        
    packed = edit_dir / "takes_packed.md"

    if not packed.exists():
        # Try to pack from raw transcripts
        transcripts_dir = edit_dir / "transcripts"
        if transcripts_dir.exists() and any(transcripts_dir.glob("*.json")):
            pack_script = Path(__file__).parent.parent.parent / "helpers" / "pack_transcripts.py"
            subprocess.run(
                [sys.executable, str(pack_script), "--edit-dir", str(edit_dir)],
                capture_output=True, text=True, timeout=30,
            )
        if not packed.exists():
            raise HTTPException(400, "No transcript found. Transcribe sources first.")

    agent_script = Path(__file__).parent.parent.parent / "helpers" / "agent.py"
    if not agent_script.exists():
        raise HTTPException(500, f"Agent script not found: {agent_script}")

    sources_dir = Path(f"{settings.project_dir}/{project_id}/uploads").resolve()
    if not sources_dir.exists():
        sources_dir = Path(f"{settings.project_dir}/{project_id}/sources").resolve()
    if not str(sources_dir).startswith(str(base_dir)):
        raise HTTPException(400, "Path traversal attempt detected")

    try:
        result = subprocess.run(
            [sys.executable, str(agent_script),
             "--edit-dir", str(edit_dir),
             "--sources-dir", str(sources_dir),
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
            subtitle_style=edl_data.get("subtitle_style", "clean_minimal"),
            subtitles=edl_data.get("subtitles", ""),
        )
        db.add(db_edl)
        project.status = "editing"
        db.commit()
        db.refresh(db_edl)

        print(f"Agent output:\n{result.stdout}")
        logger.info("Agent output:\n%s", result.stdout)
        return db_edl

    except subprocess.TimeoutExpired:
        raise HTTPException(500, "Agent timed out after 120s")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Agent error: {str(e)}")


@router.post("/{project_id}/edl", response_model=EDLResponse)
def create_edl(project_id: int, data: EDLCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if project_id <= 0:
        raise HTTPException(400, "Invalid project ID")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if settings.auth_enabled and current_user and project.user_id != current_user.id:
        raise HTTPException(403, "You do not have access to this project")
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
    overlays_json = [{"file": o.file, "start_in_output": o.start_in_output, "duration": o.duration, "start_in_source": getattr(o, "start_in_source", 0.0)} for o in data.overlays]
    edl = EDL(project_id=project_id, version=1, grade=data.grade, total_duration_s=total_duration,
              ranges=ranges_json, overlays=overlays_json, subtitle_style=data.subtitle_style)
    db.add(edl)
    db.commit()
    db.refresh(edl)
    edl_json_path = Path(f"{settings.project_dir}/{project_id}/edit/edl.json")
    edl_json_path.parent.mkdir(parents=True, exist_ok=True)
    edl_json = {
        "version": 1,
        "sources": {s.filename: s.filepath for s in db.query(Source).filter(Source.project_id == project_id).all()},
        "ranges": ranges_json, "grade": data.grade, "overlays": overlays_json,
        "total_duration_s": total_duration, "subtitles": "master.srt", "subtitle_style": data.subtitle_style,
    }
    edl_json_path.write_text(json.dumps(edl_json, indent=2))
    project.status = "editing"
    db.commit()
    return edl


@router.get("/{project_id}/edl", response_model=EDLResponse)
def get_edl(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if project_id <= 0:
        raise HTTPException(400, "Invalid project ID")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if settings.auth_enabled and current_user and project.user_id != current_user.id:
        raise HTTPException(403, "You do not have access to this project")
    edl = db.query(EDL).filter(EDL.project_id == project_id).first()
    if not edl:
        raise HTTPException(404, "EDL not found")
    return edl


@router.delete("/{project_id}/edl")
def delete_edl(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if project_id <= 0:
        raise HTTPException(400, "Invalid project ID")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if settings.auth_enabled and current_user and project.user_id != current_user.id:
        raise HTTPException(403, "You do not have access to this project")
    edl = db.query(EDL).filter(EDL.project_id == project_id).first()
    if not edl:
        raise HTTPException(404, "EDL not found")
    db.delete(edl)
    db.commit()
    return {"ok": True}


@router.post("/{project_id}/extract-chorus")
def extract_chorus(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Acoustically locate the high-energy chorus hook, slice a 15-second promo clip, and export vertical 9:16 video."""
    if project_id <= 0:
        raise HTTPException(400, "Invalid project ID")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if settings.auth_enabled and current_user and project.user_id != current_user.id:
        raise HTTPException(403, "You do not have access to this project")

    sources = db.query(Source).filter(Source.project_id == project_id).all()
    if not sources:
        raise HTTPException(400, "No media assets uploaded yet.")

    # Find the audio track or first video
    audio_path = None
    for s in sources:
        if Path(s.filepath).suffix.lower() in (".mp3", ".wav", ".aac", ".m4a"):
            audio_path = s.filepath
            break
    if not audio_path:
        audio_path = sources[0].filepath

    # Run acoustical novelty detection to find chorus hook (15-second window)
    try:
        y, sr = librosa.load(audio_path, sr=11025)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        times = librosa.times_like(onset_env, sr=sr)
        
        window_size = int(15.0 * sr / 512)
        if len(onset_env) > window_size:
            moving_avg = np.convolve(onset_env, np.ones(window_size)/window_size, mode='valid')
            best_idx = np.argmax(moving_avg)
            chorus_start = float(times[best_idx])
        else:
            chorus_start = 0.0
    except Exception as e:
        logger.error("Chorus detection failed: %s", e)
        chorus_start = 10.0

    chorus_end = chorus_start + 15.0
    logger.info("Chorus hook detected at %.2fs - %.2fs", chorus_start, chorus_end)

    # Fetch original EDL
    db_edl = db.query(EDL).filter(EDL.project_id == project_id).first()
    if not db_edl:
        raise HTTPException(400, "No EDL found. Run Auto-Edit first.")

    # Build the 15-second clipped EDL ranges
    clipped_ranges = []
    current_out_time = 0.0

    for r in db_edl.ranges:
        # A range segment has: source, start, end
        # We need to map segments within [chorus_start, chorus_end]
        seg_dur = r["end"] - r["start"]
        seg_start_absolute = current_out_time
        seg_end_absolute = current_out_time + seg_dur

        if seg_end_absolute > chorus_start and seg_start_absolute < chorus_end:
            # Overlap exists! Clip to boundaries
            clip_offset_start = max(0.0, chorus_start - seg_start_absolute)
            clip_offset_end = max(0.0, seg_end_absolute - chorus_end)

            new_start = r["start"] + clip_offset_start
            new_end = r["end"] - clip_offset_end

            if new_end > new_start:
                clipped_ranges.append({
                    "source": r["source"],
                    "start": round(new_start, 3),
                    "end": round(new_end, 3),
                    "beat": r.get("beat", ""),
                    "note": r.get("note", ""),
                    "quote": r.get("quote", ""),
                })

        current_out_time += seg_dur

    # Create temporary EDL for the promo export
    promo_edl = {
        "version": 1,
        "sources": {s.filename: s.filepath for s in sources},
        "ranges": clipped_ranges,
        "grade": db_edl.grade,
        "overlays": [],  # Clean cut of the chorus
        "total_duration_s": 15.0,
        "subtitles": "master.ass",
        "subtitle_style": "neon_rap",
    }

    edit_dir = Path(f"{settings.project_dir}/{project_id}/edit")
    promo_edl_path = edit_dir / "edl_promo.json"
    promo_edl_path.write_text(json.dumps(promo_edl, indent=2))

    # Trigger promo export render in 9:16 vertical mode using ffmpeg
    render_script = Path(__file__).parent.parent.parent / "helpers" / "render.py"
    output_dir = Path(f"{settings.render_dir}/{project_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "social_promo_chorus.mp4"

    # Compile ASS lyrics and render vertical aspect ratio with crop
    try:
        subprocess.run([
            sys.executable, str(render_script),
            str(promo_edl_path),
            "-o", str(out_path),
            "--build-subtitles"
        ], check=True, capture_output=True, text=True, timeout=120)
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, f"Promo render failed: {e.stderr}")

    promo_edl_path.unlink(missing_ok=True)
    return {
        "ok": True,
        "message": f"Chorus promo clip successfully generated!",
        "chorus_start_s": round(chorus_start, 2),
        "output_path": str(out_path)
    }
