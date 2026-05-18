import subprocess
import uuid
import shutil
import os
from pathlib import Path
from fastapi import UploadFile
from fastapi import HTTPException
from config import settings

UPLOAD_DIR = Path(settings.upload_dir)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv", ".wmv", ".mp3", ".wav", ".aac", ".m4a"}
MAX_SIZE_BYTES = settings.max_upload_size_mb * 1024 * 1024

def _validate_magic(content: bytes) -> bool:
    if len(content) < 12:
        return False
    if content[4:8] == b"ftyp":
        return True
    if content[0:4] == b"RIFF":
        return True
    if content[0:4] == b"\x1aE\xdf\xa3":
        return True
    if content[0:3] == b"ID3":
        return True
    if content[0:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return True
    if content[0:4] in (b"\x00\x00\x01\x00", b"\x00\x00\x00\x00"):
        return True
    return False


def _find_binary(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
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
    for base in [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",
        Path("C:/ProgramData/winget/Packages"),
        Path("C:/Program Files/ffmpeg/bin"),
        Path("C:/ffmpeg/bin"),
    ]:
        for hit in base.rglob(f"{name}.exe") if base.exists() else []:
            return str(hit)
    return name


FFPROBE = _find_binary("ffprobe")
FFMPEG  = _find_binary("ffmpeg")


async def save_upload(file: UploadFile, project_id: int) -> dict:
    if project_id <= 0:
        raise HTTPException(400, "Invalid project ID")

    ext = (Path(file.filename).suffix.lower() if file.filename else "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    content = await file.read()
    content_size = len(content)

    if content_size > MAX_SIZE_BYTES:
        raise HTTPException(413, f"File too large. Maximum size is {settings.max_upload_size_mb}MB.")

    if content_size > 32:
        if not _validate_magic(content):
            raise HTTPException(400, "File content does not match a known video format.")

    project_dir = UPLOAD_DIR / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = project_dir / unique_name
    dest.write_bytes(content)

    probe = probe_video(dest)
    if probe.get("duration", 0) == 0 and probe.get("codec", "") == "":
        dest.unlink(missing_ok=True)
        raise HTTPException(400, "Uploaded file could not be read as a valid video.")

    return {
        "filename": file.filename,
        "filepath": str(dest),
        "duration": probe.get("duration", 0.0),
        "width": probe.get("width", 0),
        "height": probe.get("height", 0),
        "codec": probe.get("codec", ""),
    }


def probe_video(path: Path) -> dict:
    cmd = [FFPROBE, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)]
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
    audio_stream = next((s for s in data.get("streams", []) if s["codec_type"] == "audio"), {})
    format_info = data.get("format", {})
    return {
        "duration": float(format_info.get("duration", 0)),
        "width": int(video_stream.get("width", 0)),
        "height": int(video_stream.get("height", 0)),
        "codec": video_stream.get("codec_name", audio_stream.get("codec_name", "")),
    }
