import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Union, Optional

def detect_scenes_ffmpeg(video_path: str, threshold: float = 30.0) -> List[Dict]:
    cmd = [
        "ffmpeg", "-i", video_path,
        "-filter:v", f"select='gt(scene,{threshold/100})',showinfo",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    scenes = []
    for line in result.stderr.split("\n"):
        if "pts_time:" in line:
            match = re.search(r"pts_time:([\d.]+)", line)
            if match:
                scenes.append({"time_s": float(match.group(1)), "frame": len(scenes) + 1})
    return scenes


def detect_scenes_pyscenedetect(video_path: str, threshold: float = 30.0) -> List[Dict]:
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold / 10.0))
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()
        return [
            {"start": s[0].get_seconds(), "end": s[1].get_seconds(),
             "duration": s[1].get_seconds() - s[0].get_seconds()}
            for s in scene_list
        ]
    except ImportError:
        # Fallback to ffmpeg detection if pyscenedetect is not installed
        return detect_scenes_ffmpeg(video_path, threshold)

def detect_scenes(video_path: str, threshold: float = 30.0) -> List[Dict]:
    # Prioritize pyscenedetect if available
    try:
        from scenedetect import open_video, SceneManager
        return detect_scenes_pyscenedetect(video_path, threshold)
    except ImportError:
        return detect_scenes_ffmpeg(video_path, threshold)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Detect scenes in a video using ffmpeg or PySceneDetect.")
    ap.add_argument("video_path", type=str, help="Path to the video file")
    ap.add_argument("--threshold", type=float, default=30.0,
                    help="Scene detection threshold (0-100). Lower for more scenes.")
    args = ap.parse_args()

    scenes = detect_scenes(args.video_path, args.threshold)
    print(json.dumps(scenes, indent=2))
