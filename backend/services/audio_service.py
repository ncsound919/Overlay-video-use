import subprocess
from pathlib import Path


def remove_silence(video_path: str, output_path: str, silence_duration: float = 0.5, silence_threshold: float = -35.0) -> dict:
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", f"silenceremove=stop_periods=-1:stop_duration={silence_duration}:stop_threshold={silence_threshold}dB",
        "-c:v", "copy", output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path}


def reduce_noise(video_path: str, output_path: str, strength: float = 0.3) -> dict:
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", f"afftdn=nr={strength * 100}",
        "-c:v", "copy", output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path}


def normalize_loudness(video_path: str, output_path: str) -> dict:
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", "loudnorm=I=-14:TP=-1:LRA=11",
        "-c:v", "copy", output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path}


def full_audio_cleanup(video_path: str, output_path: str) -> dict:
    d = str(Path(output_path).parent)
    step1 = f"{d}/_clean_noise.mp4"
    step2 = f"{d}/_clean_silence.mp4"
    reduce_noise(video_path, step1)
    remove_silence(step1, step2)
    result = normalize_loudness(step2, output_path)
    Path(step1).unlink(missing_ok=True)
    Path(step2).unlink(missing_ok=True)
    return result
