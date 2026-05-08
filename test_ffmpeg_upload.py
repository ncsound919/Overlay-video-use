import requests, tempfile, subprocess, os

# Create real 2s video
tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=24",
    "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", tmp],
    check=True, capture_output=True)

BASE = "http://localhost:8002"
r = requests.post(f"{BASE}/api/projects/", json={"name": "MetaTest"})
pid = r.json()["id"]

with open(tmp, "rb") as f:
    r2 = requests.post(f"{BASE}/api/uploads/{pid}", files={"file": ("video.mp4", f, "video/mp4")})
src = r2.json()

print(f"Upload: duration={src['duration']:.1f}s  {src['width']}x{src['height']}  codec={src['codec']}")
os.unlink(tmp)
