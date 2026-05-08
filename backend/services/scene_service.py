import subprocess
import json
from pathlib import Path


def detect_scenes(video_path: str, threshold: float = 30.0) -> list[dict]:
    cmd = [
        "ffmpeg", "-i", video_path,
        "-filter:v", f"select='gt(scene,{threshold/100})',showinfo",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    scenes = []
    for line in result.stderr.split("\n"):
        if "pts_time:" in line:
            import re
            match = re.search(r"pts_time:([\d.]+)", line)
            if match:
                scenes.append({"time_s": float(match.group(1)), "frame": len(scenes) + 1})
    return scenes


def detect_with_pyscenedetect(video_path: str) -> list[dict]:
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector())
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()
        return [
            {"start": s[0].get_seconds(), "end": s[1].get_seconds(),
             "duration": s[1].get_seconds() - s[0].get_seconds()}
            for s in scene_list
        ]
    except ImportError:
        return detect_scenes(video_path)
