import subprocess
from pathlib import Path
from typing import Dict, List
import librosa
import numpy as np
import scipy.signal

def bass_boost(video_path: str, output_path: str, gain: float = 10.0, frequency: float = 100.0) -> Dict:
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", f"bass=g={gain}:f={frequency}",
        "-c:v", "copy", output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path}

def remove_silence(video_path: str, output_path: str, silence_duration: float = 0.5, silence_threshold: float = -35.0) -> Dict:
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", f"silenceremove=stop_periods=-1:stop_duration={silence_duration}:stop_threshold={silence_threshold}dB",
        "-c:v", "copy", output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path}

def reduce_noise(video_path: str, output_path: str, strength: float = 0.3) -> Dict:
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", f"afftdn=nr={strength * 100}",
        "-c:v", "copy", output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path}

def normalize_loudness(video_path: str, output_path: str) -> Dict:
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", "loudnorm=I=-14:TP=-1:LRA=11",
        "-c:v", "copy", output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path}

def studio_polish(video_path: str, output_path: str) -> Dict:
    """Professional studio vocal chain: Noise gate + Highpass + De-esser + Compressor + Reverb mix."""
    filters = (
        "afftdn=nr=15,"
        "highpass=f=80,"
        "lowpass=f=12000,"
        "acompressor=threshold=-14dB:ratio=4:attack=5:release=50,"
        "aecho=0.8:0.88:30:0.3,"
        "loudnorm=I=-14:TP=-1:LRA=11"
    )
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", filters,
        "-c:v", "copy", output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path}

def full_audio_cleanup(video_path: str, output_path: str) -> Dict:
    d = str(Path(output_path).parent)
    step1 = f"{d}/_clean_noise.mp4"
    step2 = f"{d}/_clean_silence.mp4"
    reduce_noise(video_path, step1)
    remove_silence(step1, step2)
    result = normalize_loudness(step2, output_path)
    Path(step1).unlink(missing_ok=True)
    Path(step2).unlink(missing_ok=True)
    return result

def detect_beats(audio_path: str) -> List[float]:
    """Detect beat timestamps in an audio or video file."""
    try:
        y, sr = librosa.load(audio_path, sr=None)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        return beat_times.tolist()
    except Exception as e:
        print(f"Beat detection failed: {e}")
        return []

def align_audio(master_path: str, take_path: str) -> float:
    """Finds the offset (in seconds) of take_path relative to master_path using cross-correlation."""
    try:
        sr = 11025
        y_master, _ = librosa.load(master_path, sr=sr, mono=True)
        y_take, _ = librosa.load(take_path, sr=sr, mono=True)
        
        y_master = (y_master - np.mean(y_master)) / (np.std(y_master) + 1e-8)
        y_take = (y_take - np.mean(y_take)) / (np.std(y_take) + 1e-8)
        
        correlation = scipy.signal.correlate(y_master, y_take, mode='full')
        lags = scipy.signal.correlation_lags(len(y_master), len(y_take), mode='full')
        
        best_lag_idx = np.argmax(np.abs(correlation))
        best_lag = lags[best_lag_idx]
        
        offset_seconds = best_lag / sr
        return float(offset_seconds)
    except Exception as e:
        print(f"Alignment failed between {master_path} and {take_path}: {e}")
        return 0.0

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Perform audio cleanup operations on a video.")
    ap.add_argument("video_path", type=str, help="Path to the input video file")
    ap.add_argument("output_path", type=str, help="Path to the output video file")
    ap.add_argument("--operation", type=str, choices=["remove_silence", "reduce_noise", "normalize_loudness", "full_cleanup", "bass_boost"],
                    default="full_cleanup", help="Audio cleanup operation to perform")
    args = ap.parse_args()

    if args.operation == "remove_silence":
        remove_silence(args.video_path, args.output_path)
    elif args.operation == "reduce_noise":
        reduce_noise(args.video_path, args.output_path)
    elif args.operation == "normalize_loudness":
        normalize_loudness(args.video_path, args.output_path)
    elif args.operation == "full_cleanup":
        full_audio_cleanup(args.video_path, args.output_path)
    elif args.operation == "bass_boost":
        bass_boost(args.video_path, args.output_path)
    print(f"Audio cleanup operation '{args.operation}' completed for {args.video_path} to {args.output_path}")
