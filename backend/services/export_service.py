import subprocess
from pathlib import Path

PLATFORM_PRESETS = {
    "youtube": {"label": "YouTube", "width": 1920, "height": 1080, "fps": 30, "video_codec": "libx264", "video_bitrate": "16M", "audio_codec": "aac", "audio_bitrate": "192k", "pix_fmt": "yuv420p", "crf": "20", "preset": "medium", "extension": "mp4"},
    "tiktok": {"label": "TikTok / Reels", "width": 1080, "height": 1920, "fps": 30, "video_codec": "libx264", "video_bitrate": "8M", "audio_codec": "aac", "audio_bitrate": "128k", "pix_fmt": "yuv420p", "crf": "22", "preset": "fast", "extension": "mp4"},
    "instagram_square": {"label": "Instagram Square", "width": 1080, "height": 1080, "fps": 30, "video_codec": "libx264", "video_bitrate": "10M", "audio_codec": "aac", "audio_bitrate": "128k", "pix_fmt": "yuv420p", "crf": "22", "preset": "fast", "extension": "mp4"},
    "twitter": {"label": "X / Twitter", "width": 1280, "height": 720, "fps": 30, "video_codec": "libx264", "video_bitrate": "6M", "audio_codec": "aac", "audio_bitrate": "128k", "pix_fmt": "yuv420p", "crf": "23", "preset": "fast", "extension": "mp4"},
    "gif": {"label": "Animated GIF", "width": 480, "height": 270, "fps": 15, "video_codec": "gif", "video_bitrate": "", "audio_codec": "", "audio_bitrate": "", "pix_fmt": "", "crf": "", "preset": "", "extension": "gif"},
}


def get_presets() -> dict:
    return PLATFORM_PRESETS


def apply_export_preset(input_path: str, output_path: str, preset_name: str) -> dict:
    preset = PLATFORM_PRESETS.get(preset_name)
    if not preset:
        return {"error": f"Unknown preset: {preset_name}"}
    if preset_name == "gif":
        cmd = ["ffmpeg", "-y", "-i", input_path,
               "-vf", f"fps={preset['fps']},scale={preset['width']}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
               "-loop", "0", output_path]
    else:
        cmd = ["ffmpeg", "-y", "-i", input_path,
               "-c:v", preset["video_codec"], "-preset", preset["preset"], "-crf", preset["crf"],
               "-b:v", preset["video_bitrate"],
               "-vf", f"scale={preset['width']}:{preset['height']}:force_original_aspect_ratio=decrease,pad={preset['width']}:{preset['height']}:(ow-iw)/2:(oh-ih)/2:black",
               "-pix_fmt", preset["pix_fmt"], "-r", str(preset["fps"]),
               "-c:a", preset["audio_codec"], "-b:a", preset["audio_bitrate"], "-ar", "48000",
               "-movflags", "+faststart", output_path]
    subprocess.run(cmd, check=True, capture_output=True)
    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    return {"output_path": output_path, "width": preset["width"], "height": preset["height"],
            "file_size_mb": round(size_mb, 1), "preset": preset_name}


def extract_clip(input_path: str, output_path: str, start: float, end: float, preset_name: str) -> dict:
    preset = PLATFORM_PRESETS.get(preset_name, PLATFORM_PRESETS["tiktok"])
    duration = end - start
    cmd = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", input_path, "-t", f"{duration:.3f}",
           "-c:v", preset["video_codec"], "-preset", preset["preset"], "-crf", preset["crf"],
           "-vf", f"scale={preset['width']}:{preset['height']}:force_original_aspect_ratio=decrease,pad={preset['width']}:{preset['height']}:(ow-iw)/2:(oh-ih)/2:black",
           "-pix_fmt", preset["pix_fmt"], "-r", str(preset["fps"]),
           "-c:a", preset["audio_codec"], "-b:a", preset["audio_bitrate"], "-movflags", "+faststart", output_path]
    subprocess.run(cmd, check=True, capture_output=True)
    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    return {"output_path": output_path, "width": preset["width"], "height": preset["height"],
            "duration_s": duration, "file_size_mb": round(size_mb, 1), "preset": preset_name}
