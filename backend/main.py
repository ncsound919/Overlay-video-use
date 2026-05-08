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

# Import routers safely — modules created incrementally in Tasks 3-12
_router_modules = {
    "projects": "api/projects",
    "uploads": "api/uploads",
    "transcription": "api/transcription",
    "editing": "api/editing",
    "rendering": "api/rendering",
    "scenes": "api/scenes",
    "reframe": "api/reframe",
    "templates": "api/templates",
    "exports": "api/exports",
    "audio": "api/audio",
}

for _name, _prefix in _router_modules.items():
    try:
        _mod = __import__(f"routers.{_name}", fromlist=[_name])
        app.include_router(_mod.router, prefix=f"/{_prefix}", tags=[_name])
    except ImportError:
        pass  # Router will be available after its task is implemented


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
