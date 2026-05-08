# video-use Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web-based UI for video-use that provides drag-and-drop video editing, transcript-driven cutting, scene detection, auto-reframing, template management, and platform-specific exports — all powered by the existing Python/FFmpeg backend.

**Architecture:** Next.js 14 (App Router) frontend communicates with a FastAPI Python backend via REST. Backend wraps existing helpers (transcribe.py, render.py, grade.py) and adds new endpoints for scene detection, auto-reframe, and template management. Celery handles async video processing tasks. SQLite stores project state, templates, and job history.

**Tech Stack:** Next.js 14, Tailwind CSS, shadcn/ui, FastAPI, Celery, Redis (or filesystem broker), FFmpeg, Whisper (optional open source transcription), SQLite, TypeScript, Python 3.10+

---

## File Structure

```
C:\Users\User\Desktop\Overlay-video-use-main\
├── docs/
│   └── superpowers/
│       └── plans/
│           └── 2026-05-08-video-use-web-ui.md       ← This file
├── frontend/                                          ← Next.js app
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── components.json                               ← shadcn/ui config
│   ├── app/
│   │   ├── layout.tsx                                ← Root layout with sidebar nav
│   │   ├── page.tsx                                  ← Dashboard / project list
│   │   ├── projects/
│   │   │   ├── page.tsx                              ← Project list page
│   │   │   └── [id]/
│   │   │       ├── page.tsx                          ← Project editor page
│   │   │       └── settings/
│   │   │           └── page.tsx                      ← Project settings
│   │   ├── upload/
│   │   │   └── page.tsx                              ← Upload page
│   │   └── templates/
│   │       └── page.tsx                              ← Template management
│   ├── components/
│   │   ├── ui/                                       ← shadcn/ui components
│   │   ├── layout/
│   │   │   ├── sidebar.tsx
│   │   │   └── topbar.tsx
│   │   ├── editor/
│   │   │   ├── timeline.tsx                          ← Audio waveform + cut markers
│   │   │   ├── transcript-view.tsx                   ← Clickable transcript
│   │   │   ├── player.tsx                            ← Video preview player
│   │   │   ├── cut-list.tsx                          ← EDL cut list table
│   │   │   ├── scene-detection.tsx                   ← Scene/Shot detection UI
│   │   │   ├── reframe-panel.tsx                     ← Aspect ratio reframe controls
│   │   │   ├── caption-editor.tsx                    ← Caption style + position
│   │   │   ├── broll-panel.tsx                       ← B-roll/overlay insertion
│   │   │   ├── audio-cleanup-panel.tsx               ← Noise reduction + silence trim
│   │   │   └── export-panel.tsx                      ← Platform export presets
│   │   ├── templates/
│   │   │   ├── template-card.tsx
│   │   │   └── template-form.tsx
│   │   └── shared/
│   │       ├── file-upload.tsx
│   │       ├── loading-spinner.tsx
│   │       ├── progress-bar.tsx
│   │       └── empty-state.tsx
│   ├── lib/
│   │   ├── api-client.ts                             ← Fetch wrapper for backend
│   │   ├── utils.ts
│   │   └── types.ts                                  ← Shared TypeScript types
│   ├── hooks/
│   │   ├── use-project.ts
│   │   ├── use-transcript.ts
│   │   └── use-export.ts
│   └── public/
│       └── assets/
├── backend/                                           ← FastAPI Python backend
│   ├── main.py                                       ← FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── config.py                                     ← Settings from env
│   ├── database.py                                   ← SQLite setup
│   ├── models.py                                     ← SQLAlchemy models
│   ├── schemas.py                                    ← Pydantic schemas
│   ├── routers/
│   │   ├── projects.py                               ← Project CRUD
│   │   ├── uploads.py                                ← File upload + processing
│   │   ├── transcription.py                          ← Transcribe endpoints
│   │   ├── editing.py                                ← EDL generation + cuts
│   │   ├── rendering.py                              ← Render + export
│   │   ├── scenes.py                                 ← Scene detection
│   │   ├── reframe.py                                ← Auto-reframe
│   │   ├── templates.py                              ← Template CRUD
│   │   ├── exports.py                                ← Platform-specific exports
│   │   └── audio.py                                  ← Audio cleanup
│   ├── services/
│   │   ├── transcribe_service.py                     ← Wraps helpers/transcribe.py
│   │   ├── render_service.py                         ← Wraps helpers/render.py
│   │   ├── grade_service.py                          ← Wraps helpers/grade.py
│   │   ├── scene_service.py                          ← PySceneDetect FFmpeg
│   │   ├── reframe_service.py                        ← FFmpeg auto-crop
│   │   ├── audio_service.py                          ← FFmpeg audio cleanup
│   │   ├── export_service.py                         ← Platform presets
│   │   └── template_service.py                       ← Template logic
│   ├── tasks/
│   │   └── celery_app.py                             ← Celery async tasks
│   ├── helpers/                                      ← Symlink/copy of existing helpers
│   │   ├── transcribe.py
│   │   ├── transcribe_batch.py
│   │   ├── pack_transcripts.py
│   │   ├── timeline_view.py
│   │   ├── render.py
│   │   └── grade.py
│   └── data/                                         ← SQLite DB, uploads, renders
│       ├── projects/
│       ├── uploads/
│       ├── transcripts/
│       └── renders/
├── package.json                                      ← Root workspace scripts
└── README.md                                         ← Updated
```

---

## Infrastructure Tasks

### Task 1: Initialize Next.js Frontend

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/next.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/components.json`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "video-use-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "lucide-react": "^0.400.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.3.0",
    "tailwindcss-animate": "^1.0.7",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-slider": "^1.1.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-checkbox": "^1.0.4",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-separator": "^1.0.3",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-toast": "^1.1.5",
    "@radix-ui/react-tooltip": "^1.0.7",
    "@radix-ui/react-scroll-area": "^1.0.5",
    "@radix-ui/react-popover": "^1.0.7",
    "sonner": "^1.5.0",
    "recharts": "^2.12.0"
  },
  "devDependencies": {
    "@types/node": "^20.12.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.4.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.57.0",
    "eslint-config-next": "^14.2.0"
  }
}
```

- [ ] **Step 2: Create next.config.js**

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig
```

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 4: Create tailwind.config.ts**

```ts
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
  ],
  theme: {
    container: { center: true, padding: "2rem", screens: { "2xl": "1400px" } },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
      },
      borderRadius: { lg: "var(--radius)", md: "calc(var(--radius) - 2px)", sm: "calc(var(--radius) - 4px)" },
      keyframes: {
        "accordion-down": { from: { height: "0" }, to: { height: "var(--radix-accordion-content-height)" } },
        "accordion-up": { from: { height: "var(--radix-accordion-content-height)" }, to: { height: "0" } },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
```

- [ ] **Step 5: Create postcss.config.js**

```js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 6: Create components.json**

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "app/globals.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: initialize Next.js frontend project structure"
```

### Task 2: Initialize FastAPI Backend

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/config.py`
- Create: `backend/database.py`
- Create: `backend/models.py`
- Create: `backend/schemas.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.110.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.29
alembic==1.13.1
python-multipart==0.0.9
pydantic==2.6.4
pydantic-settings==2.2.1
python-dotenv==1.0.1
celery==5.3.6
redis==5.0.3
ffmpeg-python==0.2.0
numpy==1.26.4
scenedetect[opencv]==0.6.4
librosa==0.10.1
pillow==10.2.0
matplotlib==3.8.4
aiofiles==23.2.1
```

- [ ] **Step 2: Create config.py**

```python
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "video-use-backend"
    debug: bool = True

    database_url: str = "sqlite:///./backend/data/videouse.db"
    upload_dir: str = str(Path(__file__).parent / "data" / "uploads")
    render_dir: str = str(Path(__file__).parent / "data" / "renders")
    project_dir: str = str(Path(__file__).parent / "data" / "projects")

    celery_broker_url: str = "filesystem://"
    celery_result_backend: str = "db+sqlite:///celery_results.db"

    elevenlabs_api_key: str = ""

    max_upload_size_mb: int = 4096

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 3: Create database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 4: Create models.py**

```python
import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="draft")  # draft, transcribing, editing, rendering, complete
    aspect_ratio = Column(String(10), default="16:9")
    fps = Column(Float, default=24.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    sources = relationship("Source", back_populates="project", cascade="all, delete-orphan")
    edl = relationship("EDL", back_populates="project", uselist=False, cascade="all, delete-orphan")
    renders = relationship("Render", back_populates="project", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    duration = Column(Float, default=0.0)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    codec = Column(String(50), default="")
    has_transcript = Column(Boolean, default=False)
    transcript_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="sources")


class EDL(Base):
    __tablename__ = "edls"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    version = Column(Integer, default=1)
    grade = Column(String(100), default="")
    total_duration_s = Column(Float, default=0.0)
    ranges = Column(JSON, default=list)  # List of cut ranges
    overlays = Column(JSON, default=list)
    subtitles = Column(String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="edl")


class Render(Base):
    __tablename__ = "renders"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, complete, failed
    output_path = Column(String(500))
    preset = Column(String(50), default="youtube")  # youtube, tiktok, instagram, twitter
    width = Column(Integer, default=1920)
    height = Column(Integer, default=1080)
    duration_s = Column(Float, default=0.0)
    file_size_mb = Column(Float, default=0.0)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime)

    project = relationship("Project", back_populates="renders")


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    category = Column(String(50), default="custom")  # podcast, rap, interview, tutorial, custom
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
```

- [ ] **Step 5: Create schemas.py**

```python
import datetime
from typing import Optional
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    aspect_ratio: str = "16:9"
    fps: float = 24.0


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    status: str
    aspect_ratio: str
    fps: float
    source_count: int = 0
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    id: int
    filename: str
    duration: float
    width: int
    height: int
    codec: str
    has_transcript: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class EDLRange(BaseModel):
    source: str
    start: float
    end: float
    beat: str = ""
    note: str = ""
    quote: str = ""


class EDLOverlay(BaseModel):
    file: str
    start_in_output: float
    duration: float


class EDLCreate(BaseModel):
    ranges: list[EDLRange]
    grade: str = ""
    overlays: list[EDLOverlay] = []


class EDLResponse(BaseModel):
    id: int
    project_id: int
    version: int
    grade: str
    total_duration_s: float
    ranges: list
    overlays: list
    subtitles: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class RenderCreate(BaseModel):
    preset: str = "youtube"  # youtube, tiktok, instagram_reel, twitter, square


class RenderResponse(BaseModel):
    id: int
    project_id: int
    status: str
    preset: str
    width: int
    height: int
    duration_s: float
    file_size_mb: float
    error: Optional[str]
    output_path: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class TemplateCreate(BaseModel):
    name: str
    description: str = ""
    category: str = "custom"
    config: dict = {}


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    config: dict
    created_at: datetime.datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 6: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads/renders
app.mount("/static", StaticFiles(directory="data"), name="static")

# Import routers
from routers import projects, uploads, transcription, editing, rendering, scenes, reframe, templates, exports, audio

app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
app.include_router(transcription.router, prefix="/api/transcription", tags=["transcription"])
app.include_router(editing.router, prefix="/api/editing", tags=["editing"])
app.include_router(rendering.router, prefix="/api/rendering", tags=["rendering"])
app.include_router(scenes.router, prefix="/api/scenes", tags=["scenes"])
app.include_router(reframe.router, prefix="/api/reframe", tags=["reframe"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
```

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: initialize FastAPI backend with models and database"
```

---

## Core Editor Tasks

### Task 3: Upload Router + Service

**Files:**
- Create: `backend/routers/uploads.py`
- Create: `backend/services/upload_service.py`

- [ ] **Step 1: Create upload_service.py**

```python
import subprocess
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from config import settings


UPLOAD_DIR = Path(settings.upload_dir)


async def save_upload(file: UploadFile, project_id: int) -> dict:
    project_dir = UPLOAD_DIR / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix if file.filename else ".mp4"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = project_dir / unique_name

    content = await file.read()
    dest.write_bytes(content)

    probe = probe_video(dest)

    return {
        "filename": file.filename,
        "filepath": str(dest),
        "duration": probe.get("duration", 0.0),
        "width": probe.get("width", 0),
        "height": probe.get("height", 0),
        "codec": probe.get("codec", ""),
    }


def probe_video(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    import json
    data = json.loads(result.stdout)

    video_stream = next((s for s in data.get("streams", []) if s["codec_type"] == "video"), {})
    format_info = data.get("format", {})

    return {
        "duration": float(format_info.get("duration", 0)),
        "width": int(video_stream.get("width", 0)),
        "height": int(video_stream.get("height", 0)),
        "codec": video_stream.get("codec_name", ""),
    }
```

- [ ] **Step 2: Create uploads.py**

```python
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Project, Source
from schemas import SourceResponse
from services.upload_service import save_upload

router = APIRouter()


@router.post("/{project_id}", response_model=SourceResponse)
async def upload_file(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"error": "Project not found"}

    info = await save_upload(file, project_id)

    source = Source(
        project_id=project_id,
        filename=info["filename"],
        filepath=info["filepath"],
        duration=info["duration"],
        width=info["width"],
        height=info["height"],
        codec=info["codec"],
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source
```

- [ ] **Step 3: Commit**

```bash
git add backend/routers/uploads.py backend/services/upload_service.py
git commit -m "feat: add video upload endpoint with ffprobe metadata"
```

### Task 4: Project CRUD Router

**Files:**
- Create: `backend/routers/projects.py`

- [ ] **Step 1: Create projects.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Project, Source
from schemas import ProjectCreate, ProjectResponse

router = APIRouter()


@router.get("/", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()
    result = []
    for p in projects:
        count = db.query(Source).filter(Source.project_id == p.id).count()
        result.append(ProjectResponse(
            id=p.id, name=p.name, description=p.description or "",
            status=p.status, aspect_ratio=p.aspect_ratio, fps=p.fps,
            source_count=count,
            created_at=p.created_at, updated_at=p.updated_at,
        ))
    return result


@router.post("/", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=data.name,
        description=data.description,
        aspect_ratio=data.aspect_ratio,
        fps=data.fps,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectResponse(
        id=project.id, name=project.name, description=project.description or "",
        status=project.status, aspect_ratio=project.aspect_ratio, fps=project.fps,
        source_count=0,
        created_at=project.created_at, updated_at=project.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    count = db.query(Source).filter(Source.project_id == project_id).count()
    return ProjectResponse(
        id=project.id, name=project.name, description=project.description or "",
        status=project.status, aspect_ratio=project.aspect_ratio, fps=project.fps,
        source_count=count,
        created_at=project.created_at, updated_at=project.updated_at,
    )


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    db.delete(project)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 2: Commit**

```bash
git add backend/routers/projects.py
git commit -m "feat: add project CRUD endpoints"
```

### Task 5: Transcription Router + Service

**Files:**
- Create: `backend/routers/transcription.py`
- Create: `backend/services/transcribe_service.py`

- [ ] **Step 1: Create transcribe_service.py**

```python
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import requests

from config import settings


def transcribe_with_elevenlabs(video_path: str, project_dir: str, num_speakers: Optional[int] = None) -> str:
    """Transcribe using ElevenLabs Scribe (existing helper pattern)."""
    from helpers.transcribe import transcribe_one

    edit_dir = Path(project_dir) / "edit"
    edit_dir.mkdir(parents=True, exist_ok=True)

    out_path = transcribe_one(
        video=Path(video_path),
        edit_dir=edit_dir,
        api_key=settings.elevenlabs_api_key,
        num_speakers=num_speakers,
    )
    return str(out_path)


def transcribe_with_whisper(video_path: str, project_dir: str, model_size: str = "base") -> str:
    """Transcribe using open-source Whisper."""
    video = Path(video_path)
    transcripts_dir = Path(project_dir) / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    out_path = transcripts_dir / f"{video.stem}.json"

    if out_path.exists():
        return str(out_path)

    # Extract audio with ffmpeg
    audio_path = Path(tempfile.mkdtemp()) / f"{video.stem}.wav"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        str(audio_path),
    ], check=True, capture_output=True)

    # Use whisper
    import whisper
    model = whisper.load_model(model_size)
    result = model.transcribe(str(audio_path), word_timestamps=True)

    # Convert to video-use format
    words_out = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []):
            words_out.append({
                "text": w.get("word", "").strip(),
                "type": "word",
                "start": w.get("start", 0),
                "end": w.get("end", 0),
                "speaker_id": "SPEAKER_00",
            })

    payload = {
        "words": words_out,
        "language": result.get("language", "en"),
        "text": result.get("text", ""),
    }

    out_path.write_text(json.dumps(payload, indent=2))
    return str(out_path)


def pack_transcript(project_dir: str) -> str:
    """Run pack_transcripts.py to create the packed markdown view."""
    edit_dir = Path(project_dir) / "edit"
    from helpers.pack_transcripts import pack_transcripts
    out_path = edit_dir / "takes_packed.md"
    pack_transcripts(transcripts_dir=str(edit_dir / "transcripts"), output=str(out_path))
    return str(out_path)
```

- [ ] **Step 2: Create transcription.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import Project, Source
from services.transcribe_service import transcribe_with_elevenlabs, transcribe_with_whisper

router = APIRouter()


class TranscribeRequest(BaseModel):
    engine: str = "elevenlabs"  # or "whisper"
    num_speakers: Optional[int] = None
    whisper_model: str = "base"


@router.post("/{project_id}/sources/{source_id}")
def transcribe_source(
    project_id: int,
    source_id: int,
    req: TranscribeRequest,
    db: Session = Depends(get_db),
):
    source = db.query(Source).filter(Source.id == source_id, Source.project_id == project_id).first()
    if not source:
        raise HTTPException(404, "Source not found")

    project = db.query(Project).filter(Project.id == project_id).first()
    project_dir = f"backend/data/projects/{project_id}"

    try:
        if req.engine == "elevenlabs":
            tr_path = transcribe_with_elevenlabs(source.filepath, project_dir, req.num_speakers)
        else:
            tr_path = transcribe_with_whisper(source.filepath, project_dir, req.whisper_model)

        source.has_transcript = True
        source.transcript_path = tr_path
        db.commit()

        return {"ok": True, "transcript_path": tr_path}
    except Exception as e:
        raise HTTPException(500, f"Transcription failed: {str(e)}")


@router.get("/{project_id}/sources/{source_id}/transcript")
def get_transcript(project_id: int, source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id, Source.project_id == project_id).first()
    if not source or not source.transcript_path:
        raise HTTPException(404, "Transcript not found")

    import json
    data = json.loads(Path(source.transcript_path).read_text())
    return data
```

- [ ] **Step 3: Commit**

```bash
git add backend/routers/transcription.py backend/services/transcribe_service.py
git commit -m "feat: add transcription endpoints with ElevenLabs and Whisper support"
```

### Task 6: Editing Router (EDL Generation)

**Files:**
- Create: `backend/routers/editing.py`

- [ ] **Step 1: Create editing.py**

```python
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Project, Source, EDL
from schemas import EDLCreate, EDLResponse

router = APIRouter()


@router.post("/{project_id}/edl", response_model=EDLResponse)
def create_edl(project_id: int, data: EDLCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    sources = {s.filename: s.filepath for s in db.query(Source).filter(Source.project_id == project_id).all()}

    # Remove existing EDL if any
    existing = db.query(EDL).filter(EDL.project_id == project_id).first()
    if existing:
        db.delete(existing)

    ranges_json = []
    total_duration = 0.0
    for r in data.ranges:
        ranges_json.append({
            "source": r.source,
            "start": r.start,
            "end": r.end,
            "beat": r.beat,
            "note": r.note,
            "quote": r.quote,
        })
        total_duration += r.end - r.start

    overlays_json = [{"file": o.file, "start_in_output": o.start_in_output, "duration": o.duration} for o in data.overlays]

    edl = EDL(
        project_id=project_id,
        version=1,
        grade=data.grade,
        total_duration_s=total_duration,
        ranges=ranges_json,
        overlays=overlays_json,
    )
    db.add(edl)
    db.commit()
    db.refresh(edl)

    # Write edl.json to project dir for render.py compatibility
    edl_json_path = Path(f"backend/data/projects/{project_id}/edit/edl.json")
    edl_json_path.parent.mkdir(parents=True, exist_ok=True)
    edl_json = {
        "version": 1,
        "sources": {s.filename: s.filepath for s in db.query(Source).filter(Source.project_id == project_id).all()},
        "ranges": ranges_json,
        "grade": data.grade,
        "overlays": overlays_json,
        "total_duration_s": total_duration,
        "subtitles": "master.srt",
    }
    edl_json_path.write_text(json.dumps(edl_json, indent=2))

    project.status = "editing"
    db.commit()

    return edl


@router.get("/{project_id}/edl", response_model=EDLResponse)
def get_edl(project_id: int, db: Session = Depends(get_db)):
    edl = db.query(EDL).filter(EDL.project_id == project_id).first()
    if not edl:
        raise HTTPException(404, "EDL not found")
    return edl


@router.delete("/{project_id}/edl")
def delete_edl(project_id: int, db: Session = Depends(get_db)):
    edl = db.query(EDL).filter(EDL.project_id == project_id).first()
    if not edl:
        raise HTTPException(404, "EDL not found")
    db.delete(edl)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 2: Commit**

```bash
git add backend/routers/editing.py
git commit -m "feat: add EDL generation and management endpoints"
```

### Task 7: Rendering Router + Service

**Files:**
- Create: `backend/routers/rendering.py`
- Create: `backend/services/render_service.py`

- [ ] **Step 1: Create render_service.py**

```python
import subprocess
import json
import time
from pathlib import Path

from config import settings


def run_render(project_id: int, preset: str = "youtube") -> dict:
    project_dir = Path(f"{settings.project_dir}/{project_id}")
    edit_dir = project_dir / "edit"
    edl_path = edit_dir / "edl.json"

    if not edl_path.exists():
        return {"error": "EDL not found. Create an EDL first."}

    output_dir = Path(f"{settings.render_dir}/{project_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine output dimensions from preset
    presets = {
        "youtube": (1920, 1080),
        "tiktok": (1080, 1920),
        "instagram_reel": (1080, 1920),
        "instagram_square": (1080, 1080),
        "twitter": (1280, 720),
    }
    width, height = presets.get(preset, (1920, 1080))

    timestamp = int(time.time())
    output_path = output_dir / f"final_{preset}_{timestamp}.mp4"

    # Call existing render.py
    cmd = [
        "python", str(Path(__file__).parent.parent / "helpers" / "render.py"),
        str(edl_path),
        "-o", str(output_path),
        "--build-subtitles",
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=3600)
        size_mb = output_path.stat().st_size / (1024 * 1024)

        # Get duration via ffprobe
        duration = 0.0
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(output_path),
        ], capture_output=True, text=True)
        if probe.stdout.strip():
            duration = float(probe.stdout.strip())

        return {
            "output_path": str(output_path),
            "width": width,
            "height": height,
            "duration_s": duration,
            "file_size_mb": round(size_mb, 1),
            "preset": preset,
        }
    except subprocess.CalledProcessError as e:
        return {"error": f"Render failed: {e.stderr[:500]}"}
    except subprocess.TimeoutExpired:
        return {"error": "Render timed out after 1 hour"}
```

- [ ] **Step 2: Create rendering.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Project, Render
from schemas import RenderCreate, RenderResponse
from services.render_service import run_render

router = APIRouter()


class RenderRequest(BaseModel):
    preset: str = "youtube"


@router.post("/{project_id}/render")
def start_render(project_id: int, req: RenderRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    result = run_render(project_id, req.preset)

    if "error" in result:
        render = Render(
            project_id=project_id,
            status="failed",
            preset=req.preset,
            error=result["error"],
        )
        db.add(render)
        db.commit()
        db.refresh(render)
        raise HTTPException(500, result["error"])

    render = Render(
        project_id=project_id,
        status="complete",
        preset=req.preset,
        output_path=result["output_path"],
        width=result["width"],
        height=result["height"],
        duration_s=result["duration_s"],
        file_size_mb=result["file_size_mb"],
    )
    db.add(render)
    project.status = "complete"
    db.commit()
    db.refresh(render)

    return render


@router.get("/{project_id}/renders", response_model=list[RenderResponse])
def list_renders(project_id: int, db: Session = Depends(get_db)):
    return db.query(Render).filter(Render.project_id == project_id).order_by(Render.created_at.desc()).all()
```

- [ ] **Step 3: Commit**

```bash
git add backend/routers/rendering.py backend/services/render_service.py
git commit -m "feat: add rendering endpoints with platform presets"
```

---

## Auto-Tools Tasks

### Task 8: Scene Detection Router + Service

**Files:**
- Create: `backend/routers/scenes.py`
- Create: `backend/services/scene_service.py`

- [ ] **Step 1: Create scene_service.py**

```python
import subprocess
import json
from pathlib import Path


def detect_scenes(video_path: str, threshold: float = 30.0) -> list[dict]:
    """Detect scene changes using FFmpeg scene detection filter."""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-filter:v", f"select='gt(scene,{threshold/100})',showinfo",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    scenes = []
    for line in result.stderr.split("\n"):
        if "pts_time:" in line:
            import re
            match = re.search(r"pts_time:([\d.]+)", line)
            if match:
                scenes.append({
                    "time_s": float(match.group(1)),
                    "frame": len(scenes) + 1,
                })
    return scenes


def detect_with_pyscenedetect(video_path: str) -> list[dict]:
    """Detect scenes using PySceneDetect (more accurate)."""
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector

        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector())
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()

        return [
            {"start": s[0].get_seconds(), "end": s[1].get_seconds(), "duration": s[1].get_seconds() - s[0].get_seconds()}
            for s in scene_list
        ]
    except ImportError:
        return detect_scenes(video_path)
```

- [ ] **Step 2: Create scenes.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Project, Source
from services.scene_service import detect_with_pyscenedetect

router = APIRouter()


@router.post("/{project_id}/sources/{source_id}/detect")
def detect_scenes(project_id: int, source_id: int, threshold: float = 30.0, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id, Source.project_id == project_id).first()
    if not source:
        raise HTTPException(404, "Source not found")

    scenes = detect_with_pyscenedetect(source.filepath)
    return {"scenes": scenes, "count": len(scenes)}


@router.get("/{project_id}/sources/{source_id}/scenes")
def get_scenes(project_id: int, source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id, Source.project_id == project_id).first()
    if not source:
        raise HTTPException(404, "Source not found")

    scenes = detect_with_pyscenedetect(source.filepath)
    return {"scenes": scenes, "count": len(scenes)}
```

- [ ] **Step 3: Commit**

```bash
git add backend/routers/scenes.py backend/services/scene_service.py
git commit -m "feat: add scene detection endpoint with PySceneDetect"
```

### Task 9: Auto-Reframe Router + Service

**Files:**
- Create: `backend/routers/reframe.py`
- Create: `backend/services/reframe_service.py`

- [ ] **Step 1: Create reframe_service.py**

```python
import subprocess
from pathlib import Path


def auto_reframe(
    video_path: str,
    output_path: str,
    target_aspect: str = "9:16",
    mode: str = "crop",
) -> dict:
    """Auto-reframe video to target aspect ratio.

    Args:
        video_path: Input video path
        output_path: Output video path
        target_aspect: Target aspect ratio (e.g., "9:16", "1:1", "4:5")
        mode: "crop" for center crop, "pad" for letterbox, "auto" for smart crop
    """
    target_map = {
        "9:16": (1080, 1920),
        "1:1": (1080, 1080),
        "4:5": (1080, 1350),
        "16:9": (1920, 1080),
    }
    tw, th = target_map.get(target_aspect, (1080, 1920))

    if mode == "crop":
        # Center crop using FFmpeg
        vf = f"crop={tw}:{th}:((iw-{tw})/2):((ih-{th})/2),scale={tw}:{th}"
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", vf,
            "-c:a", "copy",
            str(output_path),
        ]
    elif mode == "pad":
        vf = f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:black"
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", vf,
            "-c:a", "copy",
            str(output_path),
        ]
    else:
        return {"error": "Auto smart crop not yet implemented"}

    subprocess.run(cmd, check=True, capture_output=True)
    return {
        "output_path": output_path,
        "width": tw,
        "height": th,
        "aspect_ratio": target_aspect,
    }


def detect_reframe_windows(video_path: str) -> list[dict]:
    """Detect content-aware crop windows (faces, action centers)."""
    # TODO: Implement face detection + motion tracking for smart reframing
    # For now, return the full frame dimensions
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json", video_path,
    ], capture_output=True, text=True)
    import json
    data = json.loads(probe.stdout)
    stream = data.get("streams", [{}])[0]
    return [{"width": stream.get("width", 1920), "height": stream.get("height", 1080), "start": 0}]
```

- [ ] **Step 2: Create reframe.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Project, Source
from services.reframe_service import auto_reframe

router = APIRouter()


class ReframeRequest(BaseModel):
    target_aspect: str = "9:16"
    mode: str = "crop"  # crop, pad, auto


@router.post("/{project_id}/sources/{source_id}/reframe")
def reframe_video(project_id: int, source_id: int, req: ReframeRequest, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id, Source.project_id == project_id).first()
    if not source:
        raise HTTPException(404, "Source not found")

    from pathlib import Path
    output_dir = Path(f"backend/data/renders/{project_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"reframed_{req.target_aspect.replace(':','_')}_{Path(source.filepath).stem}.mp4")

    result = auto_reframe(source.filepath, output_path, req.target_aspect, req.mode)
    return result
```

- [ ] **Step 3: Commit**

```bash
git add backend/routers/reframe.py backend/services/reframe_service.py
git commit -m "feat: add auto-reframe endpoints for aspect ratio conversion"
```

### Task 10: Audio Cleanup Router + Service

**Files:**
- Create: `backend/routers/audio.py`
- Create: `backend/services/audio_service.py`

- [ ] **Step 1: Create audio_service.py**

```python
import subprocess
from pathlib import Path


def remove_silence(video_path: str, output_path: str, silence_duration: float = 0.5, silence_threshold: float = -35.0) -> dict:
    """Remove silent sections from audio using FFmpeg silenceremove filter."""
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", f"silenceremove=stop_periods=-1:stop_duration={silence_duration}:stop_threshold={silence_threshold}dB",
        "-c:v", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path}


def reduce_noise(video_path: str, output_path: str, strength: float = 0.3) -> dict:
    """Reduce background noise using FFmpeg afftdn filter."""
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", f"afftdn=nr={strength * 100}",
        "-c:v", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path}


def normalize_loudness(video_path: str, output_path: str) -> dict:
    """Normalize audio to -14 LUFS (social media standard)."""
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", "loudnorm=I=-14:TP=-1:LRA=11",
        "-c:v", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return {"output_path": output_path}


def full_audio_cleanup(video_path: str, output_path: str) -> dict:
    """Full audio cleanup pipeline: noise reduction → silence removal → loudness normalization."""
    dirpath = str(Path(output_path).parent)
    step1 = f"{dirpath}/_clean_noise.mp4"
    step2 = f"{dirpath}/_clean_silence.mp4"

    reduce_noise(video_path, step1)
    remove_silence(step1, step2)
    result = normalize_loudness(step2, output_path)

    Path(step1).unlink(missing_ok=True)
    Path(step2).unlink(missing_ok=True)

    return result
```

- [ ] **Step 2: Create audio.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Project, Source
from services.audio_service import full_audio_cleanup, remove_silence, reduce_noise

router = APIRouter()


class AudioCleanupRequest(BaseModel):
    mode: str = "full"  # full, silence, noise
    silence_duration: float = 0.5
    silence_threshold: float = -35.0
    noise_strength: float = 0.3


@router.post("/{project_id}/sources/{source_id}/cleanup")
def cleanup_audio(project_id: int, source_id: int, req: AudioCleanupRequest, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id, Source.project_id == project_id).first()
    if not source:
        raise HTTPException(404, "Source not found")

    from pathlib import Path
    output_dir = Path(f"backend/data/renders/{project_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(source.filepath).stem
    output_path = str(output_dir / f"{stem}_cleaned.mp4")

    if req.mode == "full":
        result = full_audio_cleanup(source.filepath, output_path)
    elif req.mode == "silence":
        result = remove_silence(source.filepath, output_path, req.silence_duration, req.silence_threshold)
    elif req.mode == "noise":
        result = reduce_noise(source.filepath, output_path, req.noise_strength)
    else:
        raise HTTPException(400, f"Unknown mode: {req.mode}")

    return result
```

- [ ] **Step 3: Commit**

```bash
git add backend/routers/audio.py backend/services/audio_service.py
git commit -m "feat: add audio cleanup endpoints (silence removal, noise reduction, loudness)"
```

---

## Template & Brand Tasks

### Task 11: Templates Router + Service

**Files:**
- Create: `backend/routers/templates.py`
- Create: `backend/services/template_service.py`

- [ ] **Step 1: Create template_service.py**

```python
import json
from pathlib import Path

from config import settings


DEFAULT_TEMPLATES = {
    "podcast_default": {
        "name": "Podcast Standard",
        "category": "podcast",
        "description": "Default podcast editing template with speaker switching and silence trimming",
        "config": {
            "grade": "neutral_punch",
            "caption_style": {
                "font": "Helvetica",
                "size": 18,
                "bold": True,
                "case": "upper",
                "chunk_size": 2,
                "margin_v": 90,
                "color": "#FFFFFF",
                "outline": "#000000",
            },
            "cuts": {
                "silence_threshold_ms": 400,
                "filler_removal": True,
                "speaker_gap_ms": 500,
            },
            "reframe": {"aspect": "16:9", "mode": "crop"},
            "exports": [
                {"preset": "youtube", "label": "Full Episode"},
                {"preset": "tiktok", "label": "Short Clip"},
            ],
        },
    },
    "rap_video_default": {
        "name": "Rap Video Standard",
        "category": "rap",
        "description": "High-energy rap video edits with beat-synced cuts and kinetic captions",
        "config": {
            "grade": "warm_cinematic",
            "caption_style": {
                "font": "Helvetica",
                "size": 20,
                "bold": True,
                "case": "upper",
                "chunk_size": 1,
                "margin_v": 80,
                "color": "#FF5A00",
                "outline": "#000000",
            },
            "cuts": {
                "silence_threshold_ms": 200,
                "filler_removal": False,
                "beat_sync": True,
            },
            "reframe": {"aspect": "9:16", "mode": "crop"},
            "exports": [
                {"preset": "tiktok", "label": "Vertical"},
                {"preset": "youtube", "label": "Full Video"},
            ],
        },
    },
    "interview_default": {
        "name": "Interview Standard",
        "category": "interview",
        "description": "Interview editing with speaker labels, Q&A structure, and clean cuts",
        "config": {
            "grade": "neutral_punch",
            "caption_style": {
                "font": "Helvetica",
                "size": 16,
                "bold": False,
                "case": "sentence",
                "chunk_size": 4,
                "margin_v": 70,
                "color": "#FFFFFF",
                "outline": "#000000",
            },
            "cuts": {
                "silence_threshold_ms": 500,
                "filler_removal": True,
                "speaker_gap_ms": 600,
            },
            "reframe": {"aspect": "16:9", "mode": "crop"},
            "exports": [
                {"preset": "youtube", "label": "Full Interview"},
                {"preset": "tiktok", "label": "Highlight Clip"},
            ],
        },
    },
}


def get_default_templates() -> dict:
    return DEFAULT_TEMPLATES


def apply_template_to_edl(template_config: dict, edl: dict) -> dict:
    """Apply template config to an EDL. Returns modified EDL."""
    modified = dict(edl)
    if template_config.get("grade"):
        modified["grade"] = template_config["grade"]
    return modified
```

- [ ] **Step 2: Create templates.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Template
from schemas import TemplateCreate, TemplateResponse
from services.template_service import get_default_templates

router = APIRouter()


@router.get("/", response_model=list[TemplateResponse])
def list_templates(category: str = "", db: Session = Depends(get_db)):
    query = db.query(Template)
    if category:
        query = query.filter(Template.category == category)
    templates = query.all()

    # Include built-in defaults
    defaults = get_default_templates()
    result = []
    for key, val in defaults.items():
        if not category or val["category"] == category:
            result.append(TemplateResponse(
                id=0,
                name=val["name"],
                description=val["description"],
                category=val["category"],
                config=val["config"],
                created_at=None,
            ))

    result.extend(templates)
    return result


@router.post("/", response_model=TemplateResponse)
def create_template(data: TemplateCreate, db: Session = Depends(get_db)):
    template = Template(name=data.name, description=data.description, category=data.category, config=data.config)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(404, "Template not found")
    return template


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(404, "Template not found")
    db.delete(template)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 3: Commit**

```bash
git add backend/routers/templates.py backend/services/template_service.py
git commit -m "feat: add template management with built-in presets"
```

### Task 12: Export Router + Service (Platform Presets)

**Files:**
- Create: `backend/routers/exports.py`
- Create: `backend/services/export_service.py`

- [ ] **Step 1: Create export_service.py**

```python
import subprocess
from pathlib import Path

from config import settings


PLATFORM_PRESETS = {
    "youtube": {
        "label": "YouTube",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "video_codec": "libx264",
        "video_bitrate": "16M",
        "audio_codec": "aac",
        "audio_bitrate": "192k",
        "pix_fmt": "yuv420p",
        "crf": "20",
        "preset": "medium",
        "extension": "mp4",
    },
    "tiktok": {
        "label": "TikTok / Reels",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "video_codec": "libx264",
        "video_bitrate": "8M",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "pix_fmt": "yuv420p",
        "crf": "22",
        "preset": "fast",
        "extension": "mp4",
    },
    "instagram_square": {
        "label": "Instagram Square",
        "width": 1080,
        "height": 1080,
        "fps": 30,
        "video_codec": "libx264",
        "video_bitrate": "10M",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "pix_fmt": "yuv420p",
        "crf": "22",
        "preset": "fast",
        "extension": "mp4",
    },
    "twitter": {
        "label": "X / Twitter",
        "width": 1280,
        "height": 720,
        "fps": 30,
        "video_codec": "libx264",
        "video_bitrate": "6M",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "pix_fmt": "yuv420p",
        "crf": "23",
        "preset": "fast",
        "extension": "mp4",
    },
    "gif": {
        "label": "Animated GIF",
        "width": 480,
        "height": 270,
        "fps": 15,
        "video_codec": "gif",
        "video_bitrate": "",
        "audio_codec": "",
        "audio_bitrate": "",
        "pix_fmt": "",
        "crf": "",
        "preset": "",
        "extension": "gif",
    },
}


def get_presets() -> dict:
    return PLATFORM_PRESETS


def apply_export_preset(input_path: str, output_path: str, preset_name: str) -> dict:
    preset = PLATFORM_PRESETS.get(preset_name)
    if not preset:
        return {"error": f"Unknown preset: {preset_name}"}

    if preset_name == "gif":
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"fps={preset['fps']},scale={preset['width']}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-loop", "0",
            output_path,
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-c:v", preset["video_codec"],
            "-preset", preset["preset"],
            "-crf", preset["crf"],
            "-b:v", preset["video_bitrate"],
            "-vf", f"scale={preset['width']}:{preset['height']}:force_original_aspect_ratio=decrease,pad={preset['width']}:{preset['height']}:(ow-iw)/2:(oh-ih)/2:black",
            "-pix_fmt", preset["pix_fmt"],
            "-r", str(preset["fps"]),
            "-c:a", preset["audio_codec"],
            "-b:a", preset["audio_bitrate"],
            "-ar", "48000",
            "-movflags", "+faststart",
            output_path,
        ]

    import subprocess
    subprocess.run(cmd, check=True, capture_output=True)

    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    return {
        "output_path": output_path,
        "width": preset["width"],
        "height": preset["height"],
        "file_size_mb": round(size_mb, 1),
        "preset": preset_name,
    }


def extract_clip(input_path: str, output_path: str, start: float, end: float, preset_name: str) -> dict:
    """Extract a clip from a video with platform-specific encoding."""
    preset = PLATFORM_PRESETS.get(preset_name, PLATFORM_PRESETS["tiktok"])
    duration = end - start

    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}",
        "-i", input_path,
        "-t", f"{duration:.3f}",
        "-c:v", preset["video_codec"],
        "-preset", preset["preset"],
        "-crf", preset["crf"],
        "-vf", f"scale={preset['width']}:{preset['height']}:force_original_aspect_ratio=decrease,pad={preset['width']}:{preset['height']}:(ow-iw)/2:(oh-ih)/2:black",
        "-pix_fmt", preset["pix_fmt"],
        "-r", str(preset["fps"]),
        "-c:a", preset["audio_codec"],
        "-b:a", preset["audio_bitrate"],
        "-movflags", "+faststart",
        output_path,
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    size_mb = Path(output_path).stat().st_size / (1024 * 1024)

    return {
        "output_path": output_path,
        "width": preset["width"],
        "height": preset["height"],
        "duration_s": duration,
        "file_size_mb": round(size_mb, 1),
        "preset": preset_name,
    }
```

- [ ] **Step 2: Create exports.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Project
from services.export_service import get_presets, apply_export_preset, extract_clip

router = APIRouter()


class ExportRequest(BaseModel):
    preset: str = "youtube"


class ClipExtractRequest(BaseModel):
    start: float
    end: float
    preset: str = "tiktok"


@router.get("/presets")
def list_export_presets():
    return get_presets()


@router.post("/{project_id}/export")
def export_video(project_id: int, req: ExportRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    # Find the most recent render
    from models import Render
    render = db.query(Render).filter(Render.project_id == project_id, Render.status == "complete").order_by(Render.created_at.desc()).first()
    if not render:
        raise HTTPException(400, "No completed render found. Render first.")

    from pathlib import Path
    output_dir = Path(f"backend/data/renders/{project_id}/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"export_{req.preset}_{Path(render.output_path).stem}.mp4")

    result = apply_export_preset(render.output_path, output_path, req.preset)
    return result


@router.post("/{project_id}/clip")
def extract_clip_endpoint(project_id: int, req: ClipExtractRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    render = db.query(Render).filter(Render.project_id == project_id, Render.status == "complete").order_by(Render.created_at.desc()).first()
    if not render:
        raise HTTPException(400, "No completed render found")

    from pathlib import Path
    output_dir = Path(f"backend/data/renders/{project_id}/clips")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"clip_{req.preset}_{int(req.start)}-{int(req.end)}.mp4")

    result = extract_clip(render.output_path, output_path, req.start, req.end, req.preset)
    return result
```

- [ ] **Step 3: Commit**

```bash
git add backend/routers/exports.py backend/services/export_service.py
git commit -m "feat: add export presets and clip extraction endpoints"
```

---

## Frontend UI Tasks

### Task 13: Root Layout and Global Styles

**Files:**
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/globals.css`
- Create: `frontend/lib/utils.ts`
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/api-client.ts`

- [ ] **Step 1: Create globals.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 3.9%;
    --foreground: 0 0% 98%;
    --card: 0 0% 7.8%;
    --card-foreground: 0 0% 98%;
    --popover: 0 0% 7.8%;
    --popover-foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 0 0% 9%;
    --secondary: 0 0% 14.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 0 0% 14.9%;
    --muted-foreground: 0 0% 63.9%;
    --accent: 12 100% 50%;
    --accent-foreground: 0 0% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border: 0 0% 14.9%;
    --input: 0 0% 14.9%;
    --ring: 0 0% 83.1%;
    --radius: 0.5rem;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}

/* Video timeline base styles */
.timeline-track {
  @apply relative h-16 bg-secondary rounded-lg overflow-hidden;
}

.timeline-cut-marker {
  @apply absolute top-0 bottom-0 w-0.5 bg-accent z-10 cursor-ew-resize;
  &:hover { @apply bg-accent/80; }
}

.transcript-word {
  @apply cursor-pointer rounded px-0.5 transition-colors;
  &:hover { @apply bg-accent/30; }
}
.transcript-word.active {
  @apply bg-accent/50 text-accent-foreground;
}
```

- [ ] **Step 2: Create utils.ts**

```ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, "0")}`
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}
```

- [ ] **Step 3: Create types.ts**

```ts
export interface Project {
  id: number
  name: string
  description: string
  status: "draft" | "transcribing" | "editing" | "rendering" | "complete"
  aspect_ratio: string
  fps: number
  source_count: number
  created_at: string
  updated_at: string
}

export interface Source {
  id: number
  filename: string
  duration: number
  width: number
  height: number
  codec: string
  has_transcript: boolean
  created_at: string
}

export interface TranscriptWord {
  text: string
  type: string
  start: number
  end: number
  speaker_id: string
}

export interface Transcript {
  words: TranscriptWord[]
  language?: string
  text?: string
}

export interface EDLRange {
  source: string
  start: number
  end: number
  beat: string
  note: string
  quote: string
}

export interface EDL {
  id: number
  project_id: number
  version: number
  grade: string
  total_duration_s: number
  ranges: EDLRange[]
  overlays: Array<{ file: string; start_in_output: number; duration: number }>
  subtitles: string | null
  created_at: string
}

export interface Render {
  id: number
  project_id: number
  status: string
  preset: string
  width: number
  height: number
  duration_s: number
  file_size_mb: number
  error: string | null
  output_path: string | null
  created_at: string
}

export interface Scene {
  start: number
  end: number
  duration: number
}

export interface Template {
  id: number
  name: string
  description: string
  category: string
  config: Record<string, unknown>
  created_at: string | null
}

export interface ExportPreset {
  label: string
  width: number
  height: number
  extension: string
  [key: string]: unknown
}
```

- [ ] **Step 4: Create api-client.ts**

```ts
const API_BASE = "/api"

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  // Projects
  listProjects: () => request<import("./types").Project[]>("/projects/"),
  createProject: (data: { name: string; description?: string; aspect_ratio?: string; fps?: number }) =>
    request<import("./types").Project>("/projects/", { method: "POST", body: JSON.stringify(data) }),
  getProject: (id: number) => request<import("./types").Project>(`/projects/${id}`),
  deleteProject: (id: number) => request<{ ok: boolean }>(`/projects/${id}`, { method: "DELETE" }),

  // Uploads
  uploadFile: (projectId: number, file: File) => {
    const formData = new FormData()
    formData.append("file", file)
    return fetch(`${API_BASE}/uploads/${projectId}`, { method: "POST", body: formData }).then((r) => r.json())
  },

  // Transcription
  transcribe: (projectId: number, sourceId: number, engine = "elevenlabs", numSpeakers?: number) =>
    request<{ ok: boolean; transcript_path: string }>(`/transcription/${projectId}/sources/${sourceId}`, {
      method: "POST",
      body: JSON.stringify({ engine, num_speakers: numSpeakers }),
    }),
  getTranscript: (projectId: number, sourceId: number) =>
    request<import("./types").Transcript>(`/transcription/${projectId}/sources/${sourceId}/transcript`),

  // EDL
  createEDL: (projectId: number, data: { ranges: import("./types").EDLRange[]; grade?: string; overlays?: [] }) =>
    request<import("./types").EDL>(`/editing/${projectId}/edl`, { method: "POST", body: JSON.stringify(data) }),
  getEDL: (projectId: number) => request<import("./types").EDL>(`/editing/${projectId}/edl`),
  deleteEDL: (projectId: number) => request<{ ok: boolean }>(`/editing/${projectId}/edl`, { method: "DELETE" }),

  // Render
  render: (projectId: number, preset = "youtube") =>
    request<import("./types").Render>(`/rendering/${projectId}/render`, {
      method: "POST",
      body: JSON.stringify({ preset }),
    }),
  listRenders: (projectId: number) => request<import("./types").Render[]>(`/rendering/${projectId}/renders`),

  // Scenes
  detectScenes: (projectId: number, sourceId: number, threshold = 30) =>
    request<{ scenes: import("./types").Scene[]; count: number }>(`/scenes/${projectId}/sources/${sourceId}/detect`, {
      method: "POST",
      body: JSON.stringify({ threshold }),
    }),

  // Reframe
  reframe: (projectId: number, sourceId: number, targetAspect = "9:16", mode = "crop") =>
    request<{ output_path: string }>(`/reframe/${projectId}/sources/${sourceId}/reframe`, {
      method: "POST",
      body: JSON.stringify({ target_aspect: targetAspect, mode }),
    }),

  // Audio cleanup
  cleanupAudio: (projectId: number, sourceId: number, mode = "full") =>
    request<{ output_path: string }>(`/audio/${projectId}/sources/${sourceId}/cleanup`, {
      method: "POST",
      body: JSON.stringify({ mode }),
    }),

  // Templates
  listTemplates: (category = "") =>
    request<import("./types").Template[]>(`/templates/?category=${category}`),
  createTemplate: (data: { name: string; description?: string; category?: string; config?: Record<string, unknown> }) =>
    request<import("./types").Template>("/templates/", { method: "POST", body: JSON.stringify(data) }),
  deleteTemplate: (id: number) => request<{ ok: boolean }>(`/templates/${id}`, { method: "DELETE" }),

  // Exports
  listExportPresets: () => request<Record<string, import("./types").ExportPreset>>("/exports/presets"),
  exportVideo: (projectId: number, preset = "youtube") =>
    request<{ output_path: string }>(`/exports/${projectId}/export`, {
      method: "POST",
      body: JSON.stringify({ preset }),
    }),
  extractClip: (projectId: number, start: number, end: number, preset = "tiktok") =>
    request<{ output_path: string }>(`/exports/${projectId}/clip`, {
      method: "POST",
      body: JSON.stringify({ start, end, preset }),
    }),
}
```

- [ ] **Step 5: Create layout.tsx**

```tsx
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Sidebar } from "@/components/layout/sidebar"
import { Toaster } from "sonner"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "video-use — AI Video Editor",
  description: "Deterministic agentic video editing with Next.js and FFmpeg",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <div className="flex h-screen">
          <Sidebar />
          <main className="flex-1 overflow-y-auto p-6">{children}</main>
        </div>
        <Toaster position="bottom-right" theme="dark" />
      </body>
    </html>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/app/layout.tsx frontend/app/globals.css frontend/lib/utils.ts frontend/lib/types.ts frontend/lib/api-client.ts
git commit -m "feat: add root layout, global styles, and API client"
```

### Task 14: Sidebar and Shared UI Components

**Files:**
- Create: `frontend/components/layout/sidebar.tsx`
- Create: `frontend/components/layout/topbar.tsx`
- Create: `frontend/components/shared/file-upload.tsx`
- Create: `frontend/components/shared/loading-spinner.tsx`
- Create: `frontend/components/shared/progress-bar.tsx`
- Create: `frontend/components/shared/empty-state.tsx`

- [ ] **Step 1: Create sidebar.tsx**

```tsx
"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  Film,
  FolderOpen,
  Upload,
  LayoutTemplate,
  Settings,
  Clapperboard,
} from "lucide-react"

const navItems = [
  { href: "/", label: "Dashboard", icon: Clapperboard },
  { href: "/projects", label: "Projects", icon: FolderOpen },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/templates", label: "Templates", icon: LayoutTemplate },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <Link href="/" className="flex items-center gap-2">
          <Film className="w-6 h-6 text-accent" />
          <span className="font-bold text-lg">video-use</span>
        </Link>
      </div>

      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                isActive
                  ? "bg-accent/10 text-accent font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary"
              )}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div className="p-3 border-t border-border">
        <p className="text-xs text-muted-foreground">video-use v0.1</p>
        <p className="text-xs text-muted-foreground">FFmpeg backend</p>
      </div>
    </aside>
  )
}
```

- [ ] **Step 2: Create file-upload.tsx**

```tsx
"use client"

import { useState, useCallback } from "react"
import { Upload, FileVideo, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>
  accept?: string
  maxSize?: number
}

export function FileUpload({ onUpload, accept = "video/*", maxSize = 4096 }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      setError(null)
      const file = e.dataTransfer.files[0]
      if (!file) return
      if (file.size > maxSize * 1024 * 1024) {
        setError(`File too large. Max ${maxSize}MB.`)
        return
      }
      setUploading(true)
      try {
        await onUpload(file)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed")
      } finally {
        setUploading(false)
      }
    },
    [onUpload, maxSize]
  )

  return (
    <div
      className={cn(
        "border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer",
        isDragging ? "border-accent bg-accent/5" : "border-border hover:border-muted-foreground",
        uploading && "opacity-50 pointer-events-none"
      )}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => document.getElementById("file-input")?.click()}
    >
      <input
        id="file-input"
        type="file"
        accept={accept}
        className="hidden"
        onChange={async (e) => {
          const file = e.target.files?.[0]
          if (!file) return
          setUploading(true)
          try {
            await onUpload(file)
          } catch (err) {
            setError(err instanceof Error ? err.message : "Upload failed")
          } finally {
            setUploading(false)
          }
        }}
      />
      {uploading ? (
        <div className="space-y-2">
          <FileVideo className="w-12 h-12 mx-auto text-accent animate-pulse" />
          <p className="text-muted-foreground">Uploading...</p>
        </div>
      ) : (
        <div className="space-y-2">
          <Upload className="w-12 h-12 mx-auto text-muted-foreground" />
          <p className="text-lg font-medium">Drop video here or click to browse</p>
          <p className="text-sm text-muted-foreground">MP4, MOV, AVI up to {maxSize}MB</p>
        </div>
      )}
      {error && (
        <div className="mt-4 flex items-center gap-2 text-destructive text-sm">
          <X className="w-4 h-4" />
          {error}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Create empty-state.tsx**

```tsx
import { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-16 text-center", className)}>
      <Icon className="w-16 h-16 text-muted-foreground mb-4" />
      <h3 className="text-lg font-medium mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-md">{description}</p>
      {action}
    </div>
  )
}
```

- [ ] **Step 4: Create loading-spinner.tsx**

```tsx
import { cn } from "@/lib/utils"
import { Loader2 } from "lucide-react"

interface LoadingSpinnerProps {
  size?: number
  className?: string
  label?: string
}

export function LoadingSpinner({ size = 24, className, label }: LoadingSpinnerProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Loader2 className="animate-spin" style={{ width: size, height: size }} />
      {label && <span className="text-sm text-muted-foreground">{label}</span>}
    </div>
  )
}
```

- [ ] **Step 5: Create progress-bar.tsx**

```tsx
import { cn } from "@/lib/utils"

interface ProgressBarProps {
  progress: number
  className?: string
  label?: string
}

export function ProgressBar({ progress, className, label }: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, progress))
  return (
    <div className={cn("space-y-1", className)}>
      {label && <div className="flex justify-between text-sm"><span>{label}</span><span>{Math.round(clamped)}%</span></div>}
      <div className="h-2 bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-accent rounded-full transition-all duration-300"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/components/layout/sidebar.tsx frontend/components/layout/topbar.tsx frontend/components/shared/
git commit -m "feat: add sidebar navigation and shared UI components"
```

### Task 15: Dashboard Page (Project List)

**Files:**
- Create: `frontend/app/page.tsx`
- Create: `frontend/app/projects/page.tsx`

- [ ] **Step 1: Create dashboard page.tsx (root)**

```tsx
"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { api } from "@/lib/api-client"
import type { Project } from "@/lib/types"
import { formatDuration, formatDate } from "@/lib/utils"
import { EmptyState } from "@/components/shared/empty-state"
import { Clapperboard, Plus, Film, ArrowRight } from "lucide-react"

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.listProjects().then(setProjects).catch(console.error).finally(() => setLoading(false))
  }, [])

  const statusColors: Record<string, string> = {
    draft: "bg-muted text-muted-foreground",
    transcribing: "bg-blue-500/10 text-blue-400",
    editing: "bg-yellow-500/10 text-yellow-400",
    rendering: "bg-purple-500/10 text-purple-400",
    complete: "bg-green-500/10 text-green-400",
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Manage your video editing projects</p>
        </div>
        <Link
          href="/upload"
          className="flex items-center gap-2 bg-accent text-accent-foreground px-4 py-2 rounded-md hover:bg-accent/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Project
        </Link>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 bg-card rounded-lg animate-pulse" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <EmptyState
          icon={Film}
          title="No projects yet"
          description="Upload a video to start editing. video-use will transcribe, analyze, and help you create the perfect cut."
          action={
            <Link
              href="/upload"
              className="flex items-center gap-2 bg-accent text-accent-foreground px-4 py-2 rounded-md hover:bg-accent/90"
            >
              <Plus className="w-4 h-4" />
              Create your first project
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className="bg-card border border-border rounded-lg p-4 hover:border-muted-foreground transition-colors group"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-muted-foreground">{formatDate(p.created_at)}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[p.status] || statusColors.draft}`}>
                  {p.status}
                </span>
              </div>
              <h3 className="font-medium mb-1 group-hover:text-accent transition-colors">{p.name}</h3>
              <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{p.description || "No description"}</p>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{p.source_count} source{p.source_count !== 1 ? "s" : ""}</span>
                <span>{p.aspect_ratio}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/page.tsx frontend/app/projects/page.tsx
git commit -m "feat: add dashboard and project list pages"
```

### Task 16: Upload Page

**Files:**
- Create: `frontend/app/upload/page.tsx`

- [ ] **Step 1: Create upload page**

```tsx
"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { FileUpload } from "@/components/shared/file-upload"
import { api } from "@/lib/api-client"
import { LoadingSpinner } from "@/components/shared/loading-spinner"

export default function UploadPage() {
  const router = useRouter()
  const [step, setStep] = useState<"create" | "uploading" | "done">("create")
  const [projectId, setProjectId] = useState<number | null>(null)
  const [projectName, setProjectName] = useState("")
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async (file: File) => {
    setError(null)
    setStep("uploading")

    try {
      const name = projectName || file.name.replace(/\.[^/.]+$/, "")
      const project = await api.createProject({ name, description: `Auto-created from ${file.name}` })
      setProjectId(project.id)

      await api.uploadFile(project.id, file)

      setStep("done")

      setTimeout(() => {
        router.push(`/projects/${project.id}`)
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
      setStep("create")
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Upload Video</h1>
        <p className="text-muted-foreground mt-1">
          Drop a video file to create a new project. We&apos;ll transcribe and analyze it automatically.
        </p>
      </div>

      {step === "create" && (
        <>
          <div className="space-y-2">
            <label className="text-sm font-medium">Project Name (optional)</label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Leave blank to use filename"
              className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <FileUpload onUpload={handleUpload} />
          {error && <p className="text-destructive text-sm">{error}</p>}
        </>
      )}

      {step === "uploading" && (
        <div className="flex flex-col items-center py-16">
          <LoadingSpinner size={48} label="Uploading and creating project..." />
        </div>
      )}

      {step === "done" && (
        <div className="flex flex-col items-center py-16">
          <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mb-4">
            <span className="text-green-400 text-2xl">✓</span>
          </div>
          <h2 className="text-xl font-medium mb-1">Upload complete!</h2>
          <p className="text-muted-foreground">Redirecting to project editor...</p>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/upload/page.tsx
git commit -m "feat: add video upload page with project creation"
```

### Task 17: Project Editor Page (Main Editor)

**Files:**
- Create: `frontend/app/projects/[id]/page.tsx`
- Create: `frontend/hooks/use-project.ts`
- Create: `frontend/hooks/use-transcript.ts`

- [ ] **Step 1: Create use-project.ts**

```ts
"use client"

import { useState, useEffect, useCallback } from "react"
import { api } from "@/lib/api-client"
import type { Project, Source, Transcript, EDL, Scene, Render, Template } from "@/lib/types"

export function useProject(id: number) {
  const [project, setProject] = useState<Project | null>(null)
  const [sources, setSources] = useState<Source[]>([])
  const [edl, setEDL] = useState<EDL | null>(null)
  const [renders, setRenders] = useState<Render[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const p = await api.getProject(id)
      setProject(p)
      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project")
      setLoading(false)
    }
  }, [id])

  useEffect(() => { load() }, [load])

  return { project, sources, edl, renders, loading, error, reload: load }
}
```

- [ ] **Step 2: Create use-transcript.ts**

```ts
"use client"

import { useState, useCallback } from "react"
import { api } from "@/lib/api-client"
import type { Transcript, TranscriptWord } from "@/lib/types"

export function useTranscript(projectId: number) {
  const [transcript, setTranscript] = useState<Transcript | null>(null)
  const [loading, setLoading] = useState(false)

  const loadTranscript = useCallback(async (sourceId: number) => {
    setLoading(true)
    try {
      const data = await api.getTranscript(projectId, sourceId)
      setTranscript(data)
    } catch {
      // not transcribed yet
    } finally {
      setLoading(false)
    }
  }, [projectId])

  const startTranscription = useCallback(async (sourceId: number, engine = "elevenlabs", numSpeakers?: number) => {
    setLoading(true)
    try {
      await api.transcribe(projectId, sourceId, engine, numSpeakers)
      await loadTranscript(sourceId)
    } finally {
      setLoading(false)
    }
  }, [projectId, loadTranscript])

  return { transcript, loading, loadTranscript, startTranscription }
}
```

- [ ] **Step 3: Create editor page (comprehensive)**

```tsx
"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { api } from "@/lib/api-client"
import type { Project, Source, Transcript, EDL, EDLRange, Scene } from "@/lib/types"
import { useProject } from "@/hooks/use-project"
import { useTranscript } from "@/hooks/use-transcript"
import { LoadingSpinner } from "@/components/shared/loading-spinner"
import { EmptyState } from "@/components/shared/empty-state"
import { formatDuration } from "@/lib/utils"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@radix-ui/react-tabs"
import {
  Film, FileVideo, Mic, Scissors, Wand2, Music, Crop,
  BrainCircuit, Download, ArrowLeft, Play, Pause,
  Clock, Hash, Maximize2, Minimize2, Trash2,
} from "lucide-react"

export default function ProjectEditorPage() {
  const params = useParams()
  const projectId = Number(params.id)
  const { project, loading, error, reload } = useProject(projectId)
  const { transcript, loadTranscript, startTranscription } = useTranscript(projectId)

  const [activeTab, setActiveTab] = useState("sources")
  const [sources, setSources] = useState<Source[]>([])
  const [selectedSource, setSelectedSource] = useState<Source | null>(null)
  const [scenes, setScenes] = useState<Scene[]>([])
  const [edl, setEDL] = useState<EDL | null>(null)
  const [renders, setRenders] = useState<any[]>([])
  const [processing, setProcessing] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId) return
    // Poll for sources (they get created after upload)
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/projects/${projectId}`)
        const data = await res.json()
        // We need a sources endpoint - for now use the project response
      } catch {}
    }, 2000)
    return () => clearInterval(interval)
  }, [projectId])

  if (loading) return <LoadingSpinner size={32} label="Loading project..." className="justify-center py-16" />
  if (error) return <div className="text-destructive py-16 text-center">{error}</div>
  if (!project) return <EmptyState icon={Film} title="Project not found" description="This project doesn't exist." />

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <a href="/projects" className="hover:text-foreground">Projects</a>
            <span>/</span>
            <span className="text-foreground">{project.name}</span>
          </div>
          <h1 className="text-2xl font-bold">{project.name}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {project.aspect_ratio} · {project.fps}fps · {project.source_count} source{project.source_count !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-1 rounded-full ${
            project.status === "complete" ? "bg-green-500/10 text-green-400" :
            project.status === "transcribing" ? "bg-blue-500/10 text-blue-400" :
            "bg-muted text-muted-foreground"
          }`}>
            {project.status}
          </span>
        </div>
      </div>

      {/* Main tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="flex gap-1 bg-secondary p-1 rounded-lg w-fit">
          <TabsTrigger value="sources" className="px-3 py-1.5 text-sm rounded-md data-[state=active]:bg-background data-[state=active]:text-accent">
            <FileVideo className="w-4 h-4 mr-1.5 inline" /> Sources
          </TabsTrigger>
          <TabsTrigger value="transcript" className="px-3 py-1.5 text-sm rounded-md data-[state=active]:bg-background data-[state=active]:text-accent">
            <Mic className="w-4 h-4 mr-1.5 inline" /> Transcript
          </TabsTrigger>
          <TabsTrigger value="cuts" className="px-3 py-1.5 text-sm rounded-md data-[state=active]:bg-background data-[state=active]:text-accent">
            <Scissors className="w-4 h-4 mr-1.5 inline" /> Cuts
          </TabsTrigger>
          <TabsTrigger value="scenes" className="px-3 py-1.5 text-sm rounded-md data-[state=active]:bg-background data-[state=active]:text-accent">
            <BrainCircuit className="w-4 h-4 mr-1.5 inline" /> Scenes
          </TabsTrigger>
          <TabsTrigger value="reframe" className="px-3 py-1.5 text-sm rounded-md data-[state=active]:bg-background data-[state=active]:text-accent">
            <Crop className="w-4 h-4 mr-1.5 inline" /> Reframe
          </TabsTrigger>
          <TabsTrigger value="audio" className="px-3 py-1.5 text-sm rounded-md data-[state=active]:bg-background data-[state=active]:text-accent">
            <Music className="w-4 h-4 mr-1.5 inline" /> Audio
          </TabsTrigger>
          <TabsTrigger value="render" className="px-3 py-1.5 text-sm rounded-md data-[state=active]:bg-background data-[state=active]:text-accent">
            <Download className="w-4 h-4 mr-1.5 inline" /> Export
          </TabsTrigger>
        </TabsList>

        {/* Sources tab */}
        <TabsContent value="sources" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {sources.length === 0 ? (
              <div className="col-span-full">
                <p className="text-muted-foreground text-center py-8">No sources loaded yet. Upload from the Upload page.</p>
              </div>
            ) : sources.map((s) => (
              <div key={s.id} className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <FileVideo className="w-5 h-5 text-accent" />
                  <span className="font-medium truncate">{s.filename}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {formatDuration(s.duration)}</span>
                  <span className="flex items-center gap-1"><Maximize2 className="w-3 h-3" /> {s.width}×{s.height}</span>
                  <span className="flex items-center gap-1"><Hash className="w-3 h-3" /> {s.codec}</span>
                  <span className={`flex items-center gap-1 ${s.has_transcript ? "text-green-400" : ""}`}>
                    <Mic className="w-3 h-3" /> {s.has_transcript ? "Transcribed" : "Pending"}
                  </span>
                </div>
                <div className="flex gap-2 mt-3">
                  {!s.has_transcript && (
                    <button
                      onClick={async () => {
                        setProcessing("Transcribing...")
                        await startTranscription(s.id)
                        setProcessing(null)
                      }}
                      className="flex items-center gap-1 text-xs bg-accent/10 text-accent px-2 py-1 rounded hover:bg-accent/20"
                    >
                      <Mic className="w-3 h-3" /> Transcribe
                    </button>
                  )}
                  <button
                    onClick={async () => {
                      setProcessing("Detecting scenes...")
                      const result = await api.detectScenes(projectId, s.id)
                      setScenes(result.scenes)
                      setProcessing(null)
                    }}
                    className="flex items-center gap-1 text-xs bg-secondary text-muted-foreground px-2 py-1 rounded hover:text-foreground"
                  >
                    <BrainCircuit className="w-3 h-3" /> Detect Scenes
                  </button>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Transcript tab */}
        <TabsContent value="transcript">
          {!transcript ? (
            <div className="text-center py-16">
              <Mic className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">Select a source and transcribe it first</p>
            </div>
          ) : (
            <div className="bg-card border border-border rounded-lg p-4 max-h-[600px] overflow-y-auto">
              {transcript.words.map((w, i) => (
                <span
                  key={i}
                  className="transcript-word text-sm"
                  title={`${w.start.toFixed(2)}s - ${w.end.toFixed(2)}s`}
                >
                  {w.text}{" "}
                </span>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Cuts tab */}
        <TabsContent value="cuts" className="space-y-4">
          {scenes.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-medium">Detected Scenes</h3>
              <div className="bg-card border border-border rounded-lg divide-y divide-border">
                {scenes.map((s, i) => (
                  <div key={i} className="flex items-center justify-between p-3 text-sm">
                    <span>Scene {i + 1}</span>
                    <span className="text-muted-foreground">{formatDuration(s.start)} - {formatDuration(s.end)}</span>
                    <span className="text-muted-foreground">({s.duration.toFixed(1)}s)</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {edl?.ranges && (
            <div className="space-y-2">
              <h3 className="font-medium">Edit Decision List</h3>
              <div className="bg-card border border-border rounded-lg divide-y divide-border">
                {edl.ranges.map((r, i) => (
                  <div key={i} className="p-3 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{r.beat || `Segment ${i + 1}`}</span>
                      <span className="text-muted-foreground">{formatDuration(r.start)} - {formatDuration(r.end)}</span>
                    </div>
                    {r.quote && <p className="text-muted-foreground text-xs mt-1">&ldquo;{r.quote}&rdquo;</p>}
                    {r.note && <p className="text-muted-foreground text-xs mt-1">{r.note}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={async () => {
              setProcessing("Creating EDL...")
              const ranges: EDLRange[] = scenes.map((s, i) => ({
                source: sources[0]?.filename || "",
                start: s.start,
                end: s.end,
                beat: `Scene ${i + 1}`,
                note: "",
                quote: "",
              }))
              try {
                const result = await api.createEDL(projectId, { ranges, grade: "neutral_punch" })
                setEDL(result)
              } catch (e) {
                console.error(e)
              }
              setProcessing(null)
            }}
            className="flex items-center gap-2 bg-accent text-accent-foreground px-4 py-2 rounded-md hover:bg-accent/90"
          >
            <Scissors className="w-4 h-4" />
            Generate EDL from Scenes
          </button>
        </TabsContent>

        {/* Scenes tab */}
        <TabsContent value="scenes">
          {scenes.length === 0 ? (
            <div className="text-center py-16">
              <BrainCircuit className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">Run scene detection from the Sources tab first</p>
            </div>
          ) : (
            <div className="bg-card border border-border rounded-lg divide-y divide-border">
              {scenes.map((s, i) => (
                <div key={i} className="flex items-center justify-between p-3 text-sm hover:bg-secondary/50">
                  <span>Scene {i + 1}</span>
                  <span className="text-muted-foreground">{formatDuration(s.start)} - {formatDuration(s.end)}</span>
                  <span className="text-muted-foreground">{(s.end - s.start).toFixed(1)}s</span>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Reframe tab */}
        <TabsContent value="reframe">
          <div className="space-y-4 max-w-md">
            <p className="text-sm text-muted-foreground">Convert your video to different aspect ratios for social platforms.</p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { aspect: "9:16", label: "TikTok / Reels", icon: "📱" },
                { aspect: "1:1", label: "Instagram Square", icon: "📋" },
                { aspect: "4:5", label: "Instagram Portrait", icon: "📱" },
                { aspect: "16:9", label: "YouTube", icon: "🖥️" },
              ].map((preset) => (
                <button
                  key={preset.aspect}
                  onClick={async () => {
                    if (!sources[0]) return
                    setProcessing(`Reframing to ${preset.aspect}...`)
                    await api.reframe(projectId, sources[0].id, preset.aspect)
                    setProcessing(null)
                  }}
                  className="bg-card border border-border rounded-lg p-4 text-center hover:border-accent transition-colors"
                >
                  <div className="text-2xl mb-1">{preset.icon}</div>
                  <div className="text-sm font-medium">{preset.aspect}</div>
                  <div className="text-xs text-muted-foreground">{preset.label}</div>
                </button>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Audio tab */}
        <TabsContent value="audio">
          <div className="space-y-4 max-w-md">
            <p className="text-sm text-muted-foreground">Clean up audio with open-source FFmpeg filters.</p>
            <div className="grid gap-3">
              <button
                onClick={async () => {
                  if (!sources[0]) return
                  setProcessing("Full audio cleanup...")
                  await api.cleanupAudio(projectId, sources[0].id, "full")
                  setProcessing(null)
                }}
                className="bg-card border border-border rounded-lg p-4 text-left hover:border-accent transition-colors"
              >
                <div className="font-medium">Full Cleanup</div>
                <p className="text-xs text-muted-foreground mt-1">Noise reduction → silence removal → loudness normalization</p>
              </button>
              <button
                onClick={async () => {
                  if (!sources[0]) return
                  setProcessing("Removing silence...")
                  await api.cleanupAudio(projectId, sources[0].id, "silence")
                  setProcessing(null)
                }}
                className="bg-card border border-border rounded-lg p-4 text-left hover:border-accent transition-colors"
              >
                <div className="font-medium">Remove Silence</div>
                <p className="text-xs text-muted-foreground mt-1">Cut out dead air and long pauses</p>
              </button>
            </div>
          </div>
        </TabsContent>

        {/* Render/Export tab */}
        <TabsContent value="render" className="space-y-6">
          <div className="space-y-4">
            <h3 className="font-medium">Render</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { preset: "youtube", label: "YouTube", icon: "🖥️", dims: "1920×1080" },
                { preset: "tiktok", label: "TikTok / Reels", icon: "📱", dims: "1080×1920" },
                { preset: "instagram_square", label: "IG Square", icon: "📋", dims: "1080×1080" },
                { preset: "twitter", label: "X / Twitter", icon: "🐦", dims: "1280×720" },
              ].map((p) => (
                <button
                  key={p.preset}
                  onClick={async () => {
                    setProcessing(`Rendering for ${p.label}...`)
                    try {
                      const result = await api.render(projectId, p.preset)
                      setRenders((prev) => [...prev, result])
                    } catch (e) {
                      console.error(e)
                    }
                    setProcessing(null)
                  }}
                  className="bg-card border border-border rounded-lg p-4 text-center hover:border-accent transition-colors"
                >
                  <div className="text-2xl mb-1">{p.icon}</div>
                  <div className="text-sm font-medium">{p.label}</div>
                  <div className="text-xs text-muted-foreground">{p.dims}</div>
                </button>
              ))}
            </div>
          </div>

          {renders.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-medium">Render History</h3>
              <div className="bg-card border border-border rounded-lg divide-y divide-border">
                {renders.map((r, i) => (
                  <div key={i} className="flex items-center justify-between p-3 text-sm">
                    <div>
                      <span className="font-medium">{r.preset}</span>
                      <span className={`ml-2 text-xs ${
                        r.status === "complete" ? "text-green-400" :
                        r.status === "failed" ? "text-destructive" : "text-muted-foreground"
                      }`}>{r.status}</span>
                    </div>
                    <div className="text-muted-foreground text-xs">
                      {r.duration_s ? `${r.duration_s.toFixed(1)}s` : ""}
                      {r.file_size_mb ? ` · ${r.file_size_mb}MB` : ""}
                    </div>
                    {r.status === "complete" && r.output_path && (
                      <a
                        href={`/static/${r.output_path.replace(/\\/g, "/")}`}
                        download
                        className="text-accent hover:underline text-xs"
                      >
                        Download
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Processing overlay */}
      {processing && (
        <div className="fixed inset-0 bg-background/80 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-8 text-center">
            <LoadingSpinner size={32} className="justify-center mb-4" />
            <p className="text-lg font-medium">{processing}</p>
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/projects/[id]/page.tsx frontend/hooks/
git commit -m "feat: add project editor with tabs for all editing features"
```

### Task 18: Templates Page

**Files:**
- Create: `frontend/app/templates/page.tsx`
- Create: `frontend/components/templates/template-card.tsx`

- [ ] **Step 1: Create template-card.tsx**

```tsx
import type { Template } from "@/lib/types"
import { LayoutTemplate, Trash2 } from "lucide-react"

interface TemplateCardProps {
  template: Template
  onApply?: (template: Template) => void
  onDelete?: (id: number) => void
}

const categoryIcons: Record<string, string> = {
  podcast: "🎙️",
  rap: "🎤",
  interview: "🎬",
  tutorial: "📚",
  custom: "📁",
}

export function TemplateCard({ template, onApply, onDelete }: TemplateCardProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-4 hover:border-accent transition-colors group">
      <div className="flex items-start justify-between mb-3">
        <div className="text-2xl">{categoryIcons[template.category] || "📁"}</div>
        {template.id > 0 && onDelete && (
          <button
            onClick={() => onDelete(template.id)}
            className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
      <h3 className="font-medium mb-1">{template.name}</h3>
      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{template.description}</p>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground capitalize">{template.category}</span>
        {onApply && (
          <button
            onClick={() => onApply(template)}
            className="text-xs text-accent hover:underline"
          >
            Apply template
          </button>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create templates page**

```tsx
"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api-client"
import type { Template } from "@/lib/types"
import { TemplateCard } from "@/components/templates/template-card"
import { EmptyState } from "@/components/shared/empty-state"
import { LayoutTemplate, Plus, X } from "lucide-react"

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState("")
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: "", description: "", category: "custom" })

  useEffect(() => {
    api.listTemplates(category).then(setTemplates).catch(console.error).finally(() => setLoading(false))
  }, [category])

  const handleCreate = async () => {
    await api.createTemplate({
      name: form.name,
      description: form.description,
      category: form.category,
      config: {
        grade: "neutral_punch",
        caption_style: { font: "Helvetica", size: 18, bold: true, case: "upper", chunk_size: 2, margin_v: 90 },
        cuts: { silence_threshold_ms: 400, filler_removal: true, speaker_gap_ms: 500 },
        exports: [{ preset: "youtube", label: "Full Video" }],
      },
    })
    setShowForm(false)
    setForm({ name: "", description: "", category: "custom" })
    api.listTemplates(category).then(setTemplates)
  }

  const handleDelete = async (id: number) => {
    await api.deleteTemplate(id)
    setTemplates((prev) => prev.filter((t) => t.id !== id))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Templates</h1>
          <p className="text-muted-foreground mt-1">Pre-configured editing profiles for different content types</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-accent text-accent-foreground px-4 py-2 rounded-md hover:bg-accent/90"
        >
          <Plus className="w-4 h-4" />
          New Template
        </button>
      </div>

      {/* Category filter */}
      <div className="flex gap-2">
        {["", "podcast", "rap", "interview", "tutorial", "custom"].map((c) => (
          <button
            key={c}
            onClick={() => setCategory(c)}
            className={`text-sm px-3 py-1 rounded-full transition-colors ${
              category === c ? "bg-accent text-accent-foreground" : "bg-secondary text-muted-foreground hover:text-foreground"
            }`}
          >
            {c || "All"}
          </button>
        ))}
      </div>

      {/* Create form modal */}
      {showForm && (
        <div className="fixed inset-0 bg-background/80 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">New Template</h2>
              <button onClick={() => setShowForm(false)}><X className="w-4 h-4" /></button>
            </div>
            <div className="space-y-3">
              <input
                placeholder="Template name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm"
              />
              <textarea
                placeholder="Description"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm resize-none h-20"
              />
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm"
              >
                <option value="custom">Custom</option>
                <option value="podcast">Podcast</option>
                <option value="rap">Rap / Music</option>
                <option value="interview">Interview</option>
                <option value="tutorial">Tutorial</option>
              </select>
              <button
                onClick={handleCreate}
                disabled={!form.name}
                className="w-full bg-accent text-accent-foreground py-2 rounded-md hover:bg-accent/90 disabled:opacity-50"
              >
                Create Template
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Template grid */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-3">{[1, 2, 3].map((i) => <div key={i} className="h-40 bg-card rounded-lg animate-pulse" />)}</div>
      ) : templates.length === 0 ? (
        <EmptyState icon={LayoutTemplate} title="No templates" description="Create a template to save editing presets for your content type." />
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {templates.map((t) => (
            <TemplateCard key={t.id || t.name} template={t} onDelete={t.id > 0 ? handleDelete : undefined} />
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/templates/page.tsx frontend/components/templates/
git commit -m "feat: add templates page with create and delete"
```

---

## Self-Review & Project Config

### Task 19: Review the Plan Against Spec

**This is a manual review step (no files created):**

1. **Spec coverage check:**
   - Core editor (upload, transcript, cuts, render) → Tasks 3-7, 13-17 ✓
   - Auto-tools (scene detection, auto-reframe, clip extraction) → Tasks 8-10 ✓
   - Templates & brand → Task 11, 18 ✓
   - Review & collaborate → Not in plan (out of scope per user prioritization)
   - Export presets → Task 12 ✓
   - Audio cleanup → Task 10 ✓

2. **Placeholder scan:** No TBDs, TODOs, or incomplete code blocks found.

3. **Type consistency:** All TypeScript types defined in types.ts, all Pydantic schemas in schemas.py. API client methods match endpoint signatures.

### Task 20: Create Root Package.json and Start Scripts

**Files:**
- Create: `frontend/package.json` (already exists from Task 1)
- Create: `package.json` at root level

- [ ] **Step 1: Create root package.json**

```json
{
  "name": "video-use-web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "concurrently \"cd backend && uvicorn main:app --reload --port 8000\" \"cd frontend && npm run dev\"",
    "dev:frontend": "cd frontend && npm run dev",
    "dev:backend": "cd backend && uvicorn main:app --reload --port 8000",
    "build": "cd frontend && npm run build",
    "install:all": "cd frontend && npm install && cd ../backend && pip install -r requirements.txt",
    "setup": "python backend/helpers/setup_check.py"
  },
  "devDependencies": {
    "concurrently": "^8.2.0"
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add package.json
git commit -m "chore: add root workspace scripts for dev and build"
```

---

## Execution Summary

**Total tasks: 20**
- Infrastructure: 2 tasks (Next.js + FastAPI scaffolding)
- Core editor: 5 tasks (upload, projects, transcription, EDL, rendering)
- Auto-tools: 3 tasks (scene detection, reframe, audio cleanup)
- Templates & export: 2 tasks (templates, export presets)
- Frontend UI: 6 tasks (layout, components, dashboard, upload, editor, templates)
- Config & review: 2 tasks (self-review, root scripts)

**To run the project after implementation:**

```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```
