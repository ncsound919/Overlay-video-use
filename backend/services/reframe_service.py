from typing import Dict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from helpers.reframe import auto_reframe

def run_auto_reframe(video_path: str, output_path: str, target_aspect: str = "9:16", mode: str = "crop") -> Dict:
    return auto_reframe(video_path, output_path, target_aspect, mode)
