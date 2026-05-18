import subprocess
from typing import Dict

def auto_reframe(video_path: str, output_path: str, target_aspect: str = "9:16", mode: str = "crop") -> Dict:
    target_map = {"9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350), "16:9": (1920, 1080)}
    tw, th = target_map.get(target_aspect, (1080, 1920))
    if mode == "crop":
        vf = f"scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th}"
        cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", vf, "-c:a", "copy", output_path]
    elif mode == "pad":
        vf = f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:black"
        cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", vf, "-c:a", "copy", output_path]
    else:
        return {"error": "Auto smart crop not yet implemented"}
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path, "width": tw, "height": th, "aspect_ratio": target_aspect}

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Perform video reframing.")
    ap.add_argument("video_path", type=str, help="Path to the input video file")
    ap.add_argument("output_path", type=str, help="Path to the output video file")
    ap.add_argument("--aspect_ratio", type=str, default="9:16",
                    help="Target aspect ratio (e.g., 9:16, 1:1, 4:5, 16:9)")
    ap.add_argument("--mode", type=str, choices=["crop", "pad"],
                    default="crop", help="Reframing mode (crop or pad)")
    args = ap.parse_args()
    
    result = auto_reframe(args.video_path, args.output_path, args.aspect_ratio, args.mode)
    print(f"Reframing completed. Output: {result}")
