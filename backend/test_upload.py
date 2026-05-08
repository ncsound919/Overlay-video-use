"""Test upload with requests library (full error output)."""
import requests, json, tempfile, os

BASE = "http://localhost:8002"

r = requests.post(f"{BASE}/api/projects/", json={"name": "TestUpload"})
proj = r.json()
print(f"Project: {proj['id']}")

with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
    f.write(b"\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42mp41isom")
    tmp = f.name

try:
    with open(tmp, "rb") as vf:
        r2 = requests.post(
            f"{BASE}/api/uploads/{proj['id']}",
            files={"file": ("test.mp4", vf, "video/mp4")},
        )
    print(f"Status: {r2.status_code}")
    if r2.status_code >= 400:
        print(r2.text[:3000])
        print("---FULL DETAIL---")
        print(r2.json() if r2.text.startswith("{") else "HTML response")
    else:
        print(json.dumps(r2.json(), indent=2))
finally:
    os.unlink(tmp)
