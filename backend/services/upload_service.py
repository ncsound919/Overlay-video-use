import subprocess
import uuid
import shutil
import os
from pathlib import Path
from fastapi import UploadFile
from config import settings

UPLOAD_DIR = Path(settings.upload_dir)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
MAX_SIZE_BYTES = settings.max_upload_size_mb * 1024 * 1024

# ---------------------------------------------------------------------------
# Resolve ffprobe / ffmpeg at import time.
# winget adds to the USER PATH but doesn't refresh the current shell, so
# shutil.which() with the expanded environment is more reliable than relying
# on the process PATH alone.
# ---------------------------------------------------------------------------

def _find_binary(name: str) -> str:
    """Return the full path to `name`, checking the live registry PATH."""
    # 1. Already on process PATH
    found = shutil.which(name)
    if found:
        return found

    # 2. Read the current Machine + User PATH from the Windows registry
    #    (works even if the process was started before winget updated PATH)
    try:
        machine = os.environ.get("PATH", "")
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as k:
            machine = winreg.QueryValueEx(k, "Path")[0]
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
            user = winreg.QueryValueEx(k, "Path")[0]
        combined = machine + ";" + user
        found = shutil.which(name, path=combined)
        if found:
            return found
    except Exception:
        pass

    # 3. Common winget install locations
    for base in [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",
        Path("C:/ProgramData/winget/Packages"),
        Path("C:/Program Files/ffmpeg/bin"),
        Path("C:/ffmpeg/bin"),
    ]:
        for hit in base.rglob(f"{name}.exe") if base.exists() else []:
            return str(hit)

    return name  # fall back to bare name; will fail with a clear error


FFPROBE = _find_binary("ffprobe")
FFMPEG  = _find_binary("ffmpeg")


async def save_upload(file: UploadFile, project_id: int) -> dict:
    ext = (Path(file.filename).suffix.lower() if file.filename else ".mp4")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise ValueError(f"File too large. Max {settings.max_upload_size_mb}MB.")

    project_dir = UPLOAD_DIR / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = project_dir / unique_name
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
        FFPROBE, "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except Exception:
        return {"duration": 0.0, "width": 0, "height": 0, "codec": ""}
    import json
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"duration": 0.0, "width": 0, "height": 0, "codec": ""}
    video_stream = next((s for s in data.get("streams", []) if s["codec_type"] == "video"), {})
    format_info = data.get("format", {})
    return {
        "duration": float(format_info.get("duration", 0)),
        "width": int(video_stream.get("width", 0)),
        "height": int(video_stream.get("height", 0)),
        "codec": video_stream.get("codec_name", ""),
    }
