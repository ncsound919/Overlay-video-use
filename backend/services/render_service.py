import subprocess
import json
import time
from pathlib import Path
from sqlalchemy.orm import Session
from config import settings
from models import EDL, Source


def write_edl_to_disk(project_id: int, db: Session) -> Path:
    project_dir = Path(f"{settings.project_dir}/{project_id}")
    edit_dir = project_dir / "edit"
    edl_path = edit_dir / "edl.json"
    edl_record = db.query(EDL).filter(EDL.project_id == project_id).first()
    if not edl_record:
        return edl_path
    sources = db.query(Source).filter(Source.project_id == project_id).all()
    edl_data = {
        "version": edl_record.version,
        "sources": {s.filename: s.filepath for s in sources},
        "ranges": edl_record.ranges or [],
        "grade": edl_record.grade or "",
        "overlays": edl_record.overlays or [],
        "total_duration_s": edl_record.total_duration_s or 0,
        "subtitles": edl_record.subtitles,
    }
    edl_path.parent.mkdir(parents=True, exist_ok=True)
    edl_path.write_text(json.dumps(edl_data, indent=2))
    return edl_path


def run_render(project_id: int, preset: str = "youtube", db: Session = None) -> dict:
    if db:
        edl_path = write_edl_to_disk(project_id, db)
    else:
        project_dir = Path(f"{settings.project_dir}/{project_id}")
        edit_dir = project_dir / "edit"
        edl_path = edit_dir / "edl.json"
    if not edl_path.exists():
        return {"error": "EDL not found. Create an EDL first."}
    output_dir = Path(f"{settings.render_dir}/{project_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    presets = {"youtube": (1920, 1080), "tiktok": (1080, 1920), "instagram_reel": (1080, 1920),
               "instagram_square": (1080, 1080), "twitter": (1280, 720)}
    width, height = presets.get(preset, (1920, 1080))
    timestamp = int(time.time())
    output_path = output_dir / f"final_{preset}_{timestamp}.mp4"
    cmd = [
        "python", str(Path(__file__).parent.parent.parent / "helpers" / "render.py"),
        str(edl_path), "-o", str(output_path), "--build-subtitles",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=3600)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        duration = 0.0
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(output_path),
        ], capture_output=True, text=True)
        if probe.stdout.strip():
            duration = float(probe.stdout.strip())
        return {"output_path": str(output_path), "width": width, "height": height,
                "duration_s": duration, "file_size_mb": round(size_mb, 1), "preset": preset}
    except subprocess.CalledProcessError as e:
        return {"error": f"Render failed: {e.stderr[:500]}"}
    except subprocess.TimeoutExpired:
        return {"error": "Render timed out after 1 hour"}
