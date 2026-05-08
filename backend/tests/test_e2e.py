"""End-to-end tests for the video-use backend API.

Tests all 24 API routes with edge cases, validation, and error handling.
"""
import io

import pytest


class TestHealth:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestProjects:
    BASE = "/api/projects"

    def test_create_project(self, client):
        resp = client.post(self.BASE, json={"name": "Test Project"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Project"
        assert data["status"] == "draft"
        assert data["aspect_ratio"] == "16:9"
        assert data["id"] > 0

    def test_create_project_with_all_fields(self, client):
        resp = client.post(self.BASE, json={
            "name": "Full Project", "description": "A test", "aspect_ratio": "9:16", "fps": 30,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Full Project"
        assert data["description"] == "A test"
        assert data["aspect_ratio"] == "9:16"
        assert data["fps"] == 30.0

    def test_create_project_empty_name(self, client):
        resp = client.post(self.BASE, json={"name": ""})
        assert resp.status_code == 200

    def test_list_projects(self, client):
        client.post(self.BASE, json={"name": "A"})
        client.post(self.BASE, json={"name": "B"})
        resp = client.get(self.BASE)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2

    def test_get_project(self, client):
        created = client.post(self.BASE, json={"name": "Get Me"}).json()
        resp = client.get(f"{self.BASE}/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Me"

    def test_get_project_not_found(self, client):
        resp = client.get(f"{self.BASE}/99999")
        assert resp.status_code == 404

    def test_get_project_invalid_id(self, client):
        resp = client.get(f"{self.BASE}/-1")
        assert resp.status_code == 404  # Negative IDs don't exist

    def test_delete_project(self, client):
        created = client.post(self.BASE, json={"name": "Delete Me"}).json()
        resp = client.delete(f"{self.BASE}/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_delete_project_not_found(self, client):
        resp = client.delete(f"{self.BASE}/99999")
        assert resp.status_code == 404

    def test_delete_twice(self, client):
        created = client.post(self.BASE, json={"name": "Twice"}).json()
        client.delete(f"{self.BASE}/{created['id']}")
        resp = client.delete(f"{self.BASE}/{created['id']}")
        assert resp.status_code == 404


class TestUploads:
    BASE = "/api/uploads"

    def _create_project(self, client):
        return client.post("/api/projects", json={"name": "Upload Test"}).json()["id"]

    def test_upload_no_file(self, client):
        pid = self._create_project(client)
        resp = client.post(f"{self.BASE}/{pid}")
        assert resp.status_code == 422  # missing file

    def test_upload_invalid_project(self, client):
        resp = client.post(f"{self.BASE}/99999", files={"file": ("test.mp4", b"fake", "video/mp4")})
        assert resp.status_code == 404

    def test_upload_zero_project_id(self, client):
        resp = client.post(f"{self.BASE}/0", files={"file": ("test.mp4", b"fake", "video/mp4")})
        assert resp.status_code == 400

    def test_upload_wrong_extension(self, client, test_dir):
        pid = self._create_project(client)
        resp = client.post(f"{self.BASE}/{pid}", files={"file": ("test.txt", b"hello", "text/plain")})
        assert resp.status_code == 400
        assert "Unsupported" in resp.text

    def test_upload_list_sources_empty(self, client):
        pid = self._create_project(client)
        resp = client.get(f"{self.BASE}/{pid}")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_upload_and_list(self, client, sample_video):
        pid = self._create_project(client)
        with open(sample_video, "rb") as f:
            resp = client.post(f"{self.BASE}/{pid}", files={"file": ("test.mp4", f, "video/mp4")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "test.mp4"
        assert data["duration"] > 0
        assert data["width"] > 0
        assert data["height"] > 0

        # Verify list includes it
        resp2 = client.get(f"{self.BASE}/{pid}")
        assert len(resp2.json()) == 1


class TestTranscription:
    BASE = "/api/transcription"

    def _create_project_with_source(self, client, sample_video):
        pid = client.post("/api/projects", json={"name": "Transcribe Test"}).json()["id"]
        with open(sample_video, "rb") as f:
            src = client.post(f"/api/uploads/{pid}", files={"file": ("test.mp4", f, "video/mp4")}).json()
        return pid, src["id"]

    def test_get_transcript_not_transcribed(self, client, sample_video):
        pid, sid = self._create_project_with_source(client, sample_video)
        resp = client.get(f"{self.BASE}/{pid}/sources/{sid}/transcript")
        assert resp.status_code == 404

    def test_transcribe_source_not_found(self, client):
        resp = client.post(f"{self.BASE}/1/sources/99999", json={"engine": "whisper"})
        assert resp.status_code == 404

    def test_transcribe_with_invalid_engine(self, client, sample_video):
        pid, sid = self._create_project_with_source(client, sample_video)
        resp = client.post(f"{self.BASE}/{pid}/sources/{sid}", json={"engine": "nonexistent"})
        # Should fail or return an error
        assert resp.status_code in (400, 500)


class TestEDL:
    BASE = "/api/editing"

    def _create_project(self, client):
        return client.post("/api/projects", json={"name": "EDL Test"}).json()["id"]

    def test_create_edl_no_project(self, client):
        resp = client.post(f"{self.BASE}/99999/edl", json={"ranges": []})
        assert resp.status_code == 404

    def test_create_empty_edl(self, client):
        pid = self._create_project(client)
        resp = client.post(f"{self.BASE}/{pid}/edl", json={"ranges": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_duration_s"] == 0.0
        assert data["ranges"] == []

    def test_create_edl_with_ranges(self, client):
        pid = self._create_project(client)
        resp = client.post(f"{self.BASE}/{pid}/edl", json={
            "ranges": [
                {"source": "clip1.mp4", "start": 1.0, "end": 5.0, "beat": "intro", "quote": "hello", "note": ""},
                {"source": "clip2.mp4", "start": 10.0, "end": 15.0, "beat": "main", "quote": "world", "note": ""},
            ],
            "grade": "neutral_punch",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["ranges"]) == 2
        assert data["total_duration_s"] == 9.0  # (5-1) + (15-10)
        assert data["grade"] == "neutral_punch"

    def test_get_edl_empty(self, client):
        pid = self._create_project(client)
        resp = client.get(f"{self.BASE}/{pid}/edl")
        assert resp.status_code == 404

    def test_get_edl_after_create(self, client):
        pid = self._create_project(client)
        client.post(f"{self.BASE}/{pid}/edl", json={
            "ranges": [{"source": "a.mp4", "start": 0, "end": 10}]
        })
        resp = client.get(f"{self.BASE}/{pid}/edl")
        assert resp.status_code == 200
        assert resp.json()["total_duration_s"] == 10.0

    def test_delete_edl(self, client):
        pid = self._create_project(client)
        client.post(f"{self.BASE}/{pid}/edl", json={"ranges": []})
        resp = client.delete(f"{self.BASE}/{pid}/edl")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_delete_edl_not_found(self, client):
        pid = self._create_project(client)
        resp = client.delete(f"{self.BASE}/{pid}/edl")
        assert resp.status_code == 404

    def test_edl_replaces_previous(self, client):
        pid = self._create_project(client)
        client.post(f"{self.BASE}/{pid}/edl", json={
            "ranges": [{"source": "a.mp4", "start": 0, "end": 5}]
        })
        client.post(f"{self.BASE}/{pid}/edl", json={
            "ranges": [{"source": "b.mp4", "start": 0, "end": 10}]
        })
        resp = client.get(f"{self.BASE}/{pid}/edl")
        assert resp.json()["total_duration_s"] == 10.0


class TestScenes:
    BASE = "/api/scenes"

    def _create_project_with_source(self, client, sample_video):
        pid = client.post("/api/projects", json={"name": "Scene Test"}).json()["id"]
        with open(sample_video, "rb") as f:
            src = client.post(f"/api/uploads/{pid}", files={"file": ("test.mp4", f, "video/mp4")}).json()
        return pid, src["id"]

    def test_detect_scenes_no_project(self, client):
        resp = client.post(f"{self.BASE}/99999/sources/1/detect")
        assert resp.status_code == 404

    def test_detect_scenes_source_not_found(self, client):
        pid = client.post("/api/projects", json={"name": "Scene"}).json()["id"]
        resp = client.post(f"{self.BASE}/{pid}/sources/99999/detect")
        assert resp.status_code == 404

    def test_detect_scenes_with_video(self, client, sample_video):
        pid, sid = self._create_project_with_source(client, sample_video)
        resp = client.post(f"{self.BASE}/{pid}/sources/{sid}/detect", params={"threshold": 30})
        assert resp.status_code == 200
        data = resp.json()
        assert "scenes" in data
        assert "count" in data


class TestReframe:
    BASE = "/api/reframe"

    def _create_project_with_source(self, client, sample_video):
        pid = client.post("/api/projects", json={"name": "Reframe Test"}).json()["id"]
        with open(sample_video, "rb") as f:
            src = client.post(f"/api/uploads/{pid}", files={"file": ("test.mp4", f, "video/mp4")}).json()
        return pid, src["id"]

    def test_reframe_no_source(self, client):
        pid = client.post("/api/projects", json={"name": "R"}).json()["id"]
        resp = client.post(f"{self.BASE}/{pid}/sources/99999/reframe", json={"target_aspect": "9:16", "mode": "crop"})
        assert resp.status_code == 404

    def test_reframe_crop(self, client, sample_video):
        pid, sid = self._create_project_with_source(client, sample_video)
        resp = client.post(f"{self.BASE}/{pid}/sources/{sid}/reframe", json={"target_aspect": "9:16", "mode": "crop"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["width"] == 1080
        assert data["height"] == 1920

    def test_reframe_pad(self, client, sample_video):
        pid, sid = self._create_project_with_source(client, sample_video)
        resp = client.post(f"{self.BASE}/{pid}/sources/{sid}/reframe", json={"target_aspect": "16:9", "mode": "pad"})
        assert resp.status_code == 200

    def test_reframe_invalid_mode(self, client, sample_video):
        pid, sid = self._create_project_with_source(client, sample_video)
        resp = client.post(f"{self.BASE}/{pid}/sources/{sid}/reframe", json={"target_aspect": "9:16", "mode": "invalid"})
        assert resp.status_code == 200
        assert "error" in resp.json()


class TestAudio:
    BASE = "/api/audio"

    def _create_project_with_source(self, client, sample_video):
        pid = client.post("/api/projects", json={"name": "Audio Test"}).json()["id"]
        with open(sample_video, "rb") as f:
            src = client.post(f"/api/uploads/{pid}", files={"file": ("test.mp4", f, "video/mp4")}).json()
        return pid, src["id"]

    def test_cleanup_no_source(self, client):
        pid = client.post("/api/projects", json={"name": "A"}).json()["id"]
        resp = client.post(f"{self.BASE}/{pid}/sources/99999/cleanup", json={"mode": "full"})
        assert resp.status_code == 404

    def test_cleanup_invalid_mode(self, client, sample_video):
        pid, sid = self._create_project_with_source(client, sample_video)
        resp = client.post(f"{self.BASE}/{pid}/sources/{sid}/cleanup", json={"mode": "bogus"})
        assert resp.status_code == 400

    def test_cleanup_silence(self, client, sample_video):
        pid, sid = self._create_project_with_source(client, sample_video)
        resp = client.post(f"{self.BASE}/{pid}/sources/{sid}/cleanup", json={"mode": "silence"})
        assert resp.status_code == 200
        assert "output_path" in resp.json()


class TestTemplates:
    BASE = "/api/templates"

    def test_list_defaults(self, client):
        resp = client.get(self.BASE)
        assert resp.status_code == 200
        data = resp.json()
        # Should include built-in defaults (id=0)
        defaults = [t for t in data if t["id"] == 0]
        assert len(defaults) >= 3  # podcast, rap, interview

    def test_list_defaults_filtered(self, client):
        resp = client.get(f"{self.BASE}?category=podcast")
        assert resp.status_code == 200
        for t in resp.json():
            assert t["category"] == "podcast"

    def test_create_template(self, client):
        resp = client.post(self.BASE, json={
            "name": "My Template",
            "description": "Custom template",
            "category": "custom",
            "config": {"grade": "warm_cinematic"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "My Template"
        assert data["id"] > 0

    def test_create_template_minimal(self, client):
        resp = client.post(self.BASE, json={"name": "Minimal"})
        assert resp.status_code == 200
        assert resp.json()["category"] == "custom"

    def test_get_template(self, client):
        created = client.post(self.BASE, json={"name": "Get Me"}).json()
        resp = client.get(f"{self.BASE}/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Me"

    def test_get_template_not_found(self, client):
        resp = client.get(f"{self.BASE}/99999")
        assert resp.status_code == 404

    def test_delete_template(self, client):
        created = client.post(self.BASE, json={"name": "Del"}).json()
        resp = client.delete(f"{self.BASE}/{created['id']}")
        assert resp.status_code == 200

    def test_delete_template_not_found(self, client):
        resp = client.delete(f"{self.BASE}/99999")
        assert resp.status_code == 404


class TestExports:
    BASE = "/api/exports"

    def test_list_presets(self, client):
        resp = client.get(f"{self.BASE}/presets")
        assert resp.status_code == 200
        data = resp.json()
        assert "youtube" in data
        assert "tiktok" in data
        assert data["youtube"]["label"] == "YouTube"

    def test_export_no_render(self, client):
        pid = client.post("/api/projects", json={"name": "Export Test"}).json()["id"]
        resp = client.post(f"{self.BASE}/{pid}/export", json={"preset": "youtube"})
        assert resp.status_code == 400

    def test_clip_invalid_range(self, client):
        pid = client.post("/api/projects", json={"name": "Clip Test"}).json()["id"]
        resp = client.post(f"{self.BASE}/{pid}/clip", json={"start": 10, "end": 5})
        assert resp.status_code == 400

    def test_clip_no_render(self, client):
        pid = client.post("/api/projects", json={"name": "Clip"}).json()["id"]
        resp = client.post(f"{self.BASE}/{pid}/clip", json={"start": 0, "end": 5})
        assert resp.status_code == 400


class TestRendering:
    BASE = "/api/rendering"

    def test_render_no_project(self, client):
        resp = client.post(f"{self.BASE}/99999/render", json={"preset": "youtube"})
        assert resp.status_code == 404

    def test_render_no_edl(self, client):
        pid = client.post("/api/projects", json={"name": "Render Test"}).json()["id"]
        resp = client.post(f"{self.BASE}/{pid}/render", json={"preset": "youtube"})
        assert resp.status_code == 500
        # Should fail because no EDL exists yet

    def test_list_renders_empty(self, client):
        pid = client.post("/api/projects", json={"name": "Renders"}).json()["id"]
        resp = client.get(f"{self.BASE}/{pid}/renders")
        assert resp.status_code == 200
        assert resp.json() == []


class TestEdgeCases:
    """Rare edge cases that could break the API."""

    def test_long_project_name(self, client):
        name = "A" * 250
        resp = client.post("/api/projects", json={"name": name})
        assert resp.status_code == 200

    def test_negative_edl_ranges(self, client):
        pid = client.post("/api/projects", json={"name": "Edge"}).json()["id"]
        resp = client.post(f"/api/editing/{pid}/edl", json={
            "ranges": [{"source": "a.mp4", "start": -1, "end": 5}]
        })
        # Should accept and create a valid EDL with negative start
        assert resp.status_code == 200
        assert resp.json()["total_duration_s"] == 6.0

    def test_overlapping_edl_ranges(self, client):
        pid = client.post("/api/projects", json={"name": "Overlap"}).json()["id"]
        resp = client.post(f"/api/editing/{pid}/edl", json={
            "ranges": [
                {"source": "a.mp4", "start": 0, "end": 10},
                {"source": "a.mp4", "start": 5, "end": 15},
            ]
        })
        assert resp.status_code == 200
        assert resp.json()["total_duration_s"] == 20.0  # No dedup - kept as-is

    def test_multiple_templates(self, client):
        for i in range(5):
            client.post("/api/templates", json={"name": f"T{i}", "category": "custom"})
        resp = client.get("/api/templates?category=custom")
        custom = [t for t in resp.json() if t["id"] > 0]
        assert len(custom) == 5

    def test_health_always_works(self, client):
        for _ in range(10):
            resp = client.get("/api/health")
            assert resp.status_code == 200
