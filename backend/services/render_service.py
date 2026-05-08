import subprocess
import json
import time
from pathlib import Path
from config import settings


def run_render(project_id: int, preset: str = "youtube") -> dict:
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
