import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from config import settings


def transcribe_with_elevenlabs(video_path: str, project_dir: str, num_speakers: Optional[int] = None) -> str:
    edit_dir = Path(project_dir) / "edit"
    edit_dir.mkdir(parents=True, exist_ok=True)
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from helpers.transcribe import transcribe_one
    out_path = transcribe_one(
        video=Path(video_path),
        edit_dir=edit_dir,
        api_key=settings.elevenlabs_api_key,
        num_speakers=num_speakers,
    )
    return str(out_path)


def transcribe_with_whisper(video_path: str, project_dir: str, model_size: str = "base") -> str:
    video = Path(video_path)
    transcripts_dir = Path(project_dir) / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    out_path = transcripts_dir / f"{video.stem}.json"
    if out_path.exists():
        return str(out_path)
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / f"{video.stem}.wav"
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video),
            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio_path),
        ], check=True, capture_output=True)
        try:
            import whisper
            model = whisper.load_model(model_size)
        except ImportError:
            raise RuntimeError("whisper not installed. Install with: pip install openai-whisper")
        result = model.transcribe(str(audio_path), word_timestamps=True)
        words_out = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                words_out.append({
                    "text": w.get("word", "").strip(),
                    "type": "word",
                    "start": w.get("start", 0),
                    "end": w.get("end", 0),
                    "speaker_id": "SPEAKER_00",
                })
        payload = {"words": words_out, "language": result.get("language", "en"), "text": result.get("text", "")}
        out_path.write_text(json.dumps(payload, indent=2))
    return str(out_path)
