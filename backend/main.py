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

app.mount("/static", StaticFiles(directory="data"), name="static")

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
