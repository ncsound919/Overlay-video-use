# video-use Web UI — Project Status

## Current State (May 8, 2026)

### What's Built

**Backend (FastAPI + SQLite) — 24 API routes on port 8002**

| Module | Routes | Status |
|--------|--------|--------|
| Projects | CRUD (list, create, get, delete) | Working |
| Uploads | Upload video + ffprobe metadata, list sources | Working* |
| Transcription | ElevenLabs Scribe + open-source Whisper | Working* |
| Editing | EDL creation in JSON, persisted to disk | Working |
| Rendering | Platform renders via render.py + FFmpeg | Needs FFmpeg |
| Scene Detection | PySceneDetect / FFmpeg scene detection | Needs FFmpeg |
| Auto-Reframe | 9:16, 1:1, 4:5, 16:9 crop/pad modes | Needs FFmpeg |
| Audio Cleanup | Noise reduction, silence removal, loudness | Needs FFmpeg |
| Templates | 3 built-in (podcast, rap, interview) + custom CRUD | Working |
| Exports | Platform presets (YouTube, TikTok, IG, X, GIF) | Working* |

*\*FFmpeg not installed on dev machine — video processing features will return 0 metadata/empty output until installed (`winget install ffmpeg`)*

**Frontend (Next.js 14 + Tailwind + shadcn/ui) — port 3002**

| Page | Status |
|------|--------|
| Dashboard | Project grid, status badges, New Project button |
| Projects List | All projects with nav |
| Upload | Drag-and-drop, auto creates project, redirects to editor |
| Editor (Sources tab) | Shows uploaded files, "Add Videos" multi-upload, Transcribe/Detect Scenes buttons |
| Editor (Transcript) | Word-level transcript display |
| Editor (Scenes) | Scene list from detection |
| Editor (Reframe) | Four aspect ratio presets |
| Editor (Audio tab) | Full Cleanup / Remove Silence |
| Editor (Export tab) | Four platform presets, render history, download link |
| Templates | Built-in + custom CRUD, category filter |
| Sidebar | Dashboard, Projects, Upload, Templates nav |

### Testing

- **Backend**: 49/49 pytest e2e tests passing (`backend/tests/test_e2e.py`)
- **Frontend Playwright**: 4/7 UI tests passing — filechooser interaction broken due to React synthetic event mismatch

### Known Issues

1. **FFmpeg not installed** — `winget install ffmpeg` needed for video processing
2. **Upload filechooser** — React's `onChange` on `<input type="file">` not firing from Playwright's `setInputFiles`. Component uses `useRef` with `sr-only` class. May need native DOM event listener.
3. **Port 8000 zombie** — Stale backend process on port 8000 survives restarts (Windows TCP issue). Workaround: always use port 8002.
4. **CORS** — `main.py` currently allows ports 3000 and 3002. Add more ports as needed.
5. **Template individual page** — No `/templates/[id]` route exists.
6. **EDL editor** — EDL creation via scenes works but no visual cut editor (transcript-click-to-cut).
7. **Config path** — `database_url` uses absolute path from `Path(__file__).parent`.
8. **datetime.utcnow()** — Deprecated in Python 3.12, needs `datetime.now(datetime.UTC)`.

### How to Run

```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --port 8002 --log-level warning

# Terminal 2: Frontend
cd frontend
npm install
npx next dev --port 3002
```

### Test Commands

```bash
# Backend API tests
cd backend && python -m pytest tests/test_e2e.py -v

# Frontend Playwright
cd frontend && npx playwright test --project=chromium
```

### Architecture

```
frontend (Next.js 14) ← API proxy → backend (FastAPI) ← FFmpeg / Whisper / ElevenLabs
       :3002                              :8002

  app/                   backend/
  ├─ page.tsx            ├─ main.py          (FastAPI app, CORS, router loading)
  ├─ layout.tsx          ├─ config.py        (Pydantic Settings)
  ├─ projects/[id]/      ├─ database.py      (SQLAlchemy + SQLite)
  ├─ upload/             ├─ models.py        (Project, Source, EDL, Render, Template)
  ├─ templates/          ├─ schemas.py       (Pydantic request/response)
  ├─ components/         ├─ routers/         (10 route modules)
  │  ├─ layout/          └─ services/        (10 service modules)
  │  ├─ shared/
  │  └─ templates/       helpers/            (Original CLI tools)
  ├─ hooks/              ├─ render.py
  ├─ lib/                ├─ transcribe.py
  └─ tests/              ├─ grade.py
     └─ e2e.spec.ts      ├─ timeline_view.py
                          └─ pack_transcripts.py
```

### Next Steps (Priority)

1. Install FFmpeg — unlocks all video processing features
2. Fix filechooser / React onChange for Playwright compatibility
3. Add Editor link to sidebar for quick project access
4. Add inline editor to Upload page to support adding to existing projects
5. Individual template page + template application to projects
6. Visual EDL / timeline editor
7. Database migrations (Alembic) for production
8. Celery async tasks for long-running renders
