"""Shared test fixtures for backend e2e tests."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add backend directory to sys.path to ensure dynamic routers import correctly
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import pytest
from fastapi.testclient import TestClient

os.environ["ELEVENLABS_API_KEY"] = "test-key"


@pytest.fixture(scope="session")
def test_dir():
    with tempfile.TemporaryDirectory(prefix="videouse_test_") as tmp:
        yield Path(tmp)


@pytest.fixture(autouse=True)
def _override_settings(test_dir):
    """Override settings to use temp directories for each test."""
    from config import settings
    old_db = settings.database_url
    old_rl = settings.rate_limit_enabled
    settings.database_url = f"sqlite:///{test_dir}/test.db?check_same_thread=False"
    settings.rate_limit_enabled = False

    import models
    from database import init_db, engine
    init_db()
    yield
    engine.dispose()
    db_path = test_dir / "test.db"
    if db_path.exists():
        db_path.unlink()
    settings.database_url = old_db
    settings.rate_limit_enabled = old_rl


@pytest.fixture
def client():
    from main import app
    with TestClient(app) as c:
        # Register and authenticate a default test user
        resp = c.post("/api/auth/register", json={"email": "test@example.com", "password": "password123"})
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            c.headers["Authorization"] = f"Bearer {token}"
        yield c


@pytest.fixture
def sample_video(test_dir):
    """Create a minimal valid 1-second MP4."""
    out = test_dir / "test.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=192x108:rate=24",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(out),
    ], check=True, capture_output=True)
    return out
