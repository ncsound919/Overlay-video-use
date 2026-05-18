import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from helpers.scene import detect_scenes

def detect_with_pyscenedetect(video_path: str, threshold: float = 30.0) -> List[Dict]:
    return detect_scenes(video_path, threshold)
