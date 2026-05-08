"""Quick dev server launcher for video-use."""
import subprocess, sys, time, os, urllib.request

BASE = os.path.dirname(__file__)
BE = os.path.join(BASE, "backend")
FE = os.path.join(BASE, "frontend")
procs = []

try:
    # Always use 8002 for backend, 3002 for frontend to avoid conflicts
    be_port = "8002"
    fe_port = "3002"

    print(f"Starting backend on port {be_port}...")
    pb = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", be_port, "--log-level", "warning"],
        cwd=BE,
    )
    procs.append(pb)
    time.sleep(4)

    urllib.request.urlopen(f"http://localhost:{be_port}/api/health", timeout=5)
    print("  Backend: OK")

    os.environ["API_PORT"] = be_port
    print(f"Starting frontend on port {fe_port}...")
    pf = subprocess.Popen(
        ["cmd.exe", "/c", "npx", "next", "dev", "--port", fe_port],
        cwd=FE,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    procs.append(pf)
    time.sleep(10)

    urllib.request.urlopen(f"http://localhost:{fe_port}", timeout=10)
    print("  Frontend: OK")

    print(f"\n=== Servers Running ===")
    print(f"  Backend:  http://localhost:{be_port}")
    print(f"  Frontend: http://localhost:{fe_port}")
    print(f"  API_PORT={be_port}")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    for p in procs:
        try: p.terminate(); p.wait(3)
        except: p.kill()
    print("Done.")
