import subprocess
import uuid
from pathlib import Path
from fastapi import UploadFile
from config import settings

UPLOAD_DIR = Path(settings.upload_dir)


async def save_upload(file: UploadFile, project_id: int) -> dict:
    project_dir = UPLOAD_DIR / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix if file.filename else ".mp4"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = project_dir / unique_name
    content = await file.read()
    dest.write_bytes(content)
    probe = probe_video(dest)
    return {
        "filename": file.filename,
        "filepath": str(dest),
        "duration": probe.get("duration", 0.0),
        "width": probe.get("width", 0),
        "height": probe.get("height", 0),
        "codec": probe.get("codec", ""),
    }


def probe_video(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    import json
    data = json.loads(result.stdout)
    video_stream = next((s for s in data.get("streams", []) if s["codec_type"] == "video"), {})
    format_info = data.get("format", {})
    return {
        "duration": float(format_info.get("duration", 0)),
        "width": int(video_stream.get("width", 0)),
        "height": int(video_stream.get("height", 0)),
        "codec": video_stream.get("codec_name", ""),
    }
