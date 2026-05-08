import subprocess
from pathlib import Path


def auto_reframe(video_path: str, output_path: str, target_aspect: str = "9:16", mode: str = "crop") -> dict:
    target_map = {"9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350), "16:9": (1920, 1080)}
    tw, th = target_map.get(target_aspect, (1080, 1920))
    if mode == "crop":
        vf = f"crop={tw}:{th}:((iw-{tw})/2):((ih-{th})/2),scale={tw}:{th}"
        cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", vf, "-c:a", "copy", output_path]
    elif mode == "pad":
        vf = f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:black"
        cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", vf, "-c:a", "copy", output_path]
    else:
        return {"error": "Auto smart crop not yet implemented"}
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path, "width": tw, "height": th, "aspect_ratio": target_aspect}
