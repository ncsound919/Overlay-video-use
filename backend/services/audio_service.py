from pathlib import Path
from typing import Dict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from helpers.audio import remove_silence, reduce_noise, normalize_loudness, full_audio_cleanup, bass_boost, studio_polish

def run_remove_silence(video_path: str, output_path: str, silence_duration: float = 0.5, silence_threshold: float = -35.0) -> Dict:
    return remove_silence(video_path, output_path, silence_duration, silence_threshold)

def run_reduce_noise(video_path: str, output_path: str, strength: float = 0.3) -> Dict:
    return reduce_noise(video_path, output_path, strength)

def run_normalize_loudness(video_path: str, output_path: str) -> Dict:
    return normalize_loudness(video_path, output_path)

def run_full_audio_cleanup(video_path: str, output_path: str) -> Dict:
    return full_audio_cleanup(video_path, output_path)

def run_bass_boost(video_path: str, output_path: str, gain: float = 10.0, frequency: float = 100.0) -> Dict:
    return bass_boost(video_path, output_path, gain, frequency)

def run_studio_polish(video_path: str, output_path: str) -> Dict:
    return studio_polish(video_path, output_path)
