import logging
import time
import uuid
from collections import defaultdict
from typing import DefaultDict, List

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from config import settings
from migrations import run_migrations
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield

app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store: DefaultDict[str, List[float]] = defaultdict(list)
        self._counter = 0


    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            ip = request.client.host if request.client else "unknown"
            now = time.time()
            timestamps = [t for t in self._store[ip] if now - t < self.window_seconds]
            if len(timestamps) >= self.max_requests:
                return Response(
                    content='{"detail":"Too many requests"}',
                    status_code=429,
                    media_type="application/json",
                )
            timestamps.append(now)
            self._store[ip] = timestamps
            
            # Periodically prune stale IP rate-limit logs to prevent memory leaks
            self._counter += 1
            if self._counter % 100 == 0:
                for k in list(self._store.keys()):
                    self._store[k] = [t for t in self._store[k] if now - t < self.window_seconds]
                    if not self._store[k]:
                        del self._store[k]
        return await call_next(request)


# Middleware order: first added = outermost wrapper
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-Request-ID"],
)

# Only serve rendered outputs, not source uploads
app.mount("/renders", StaticFiles(directory=settings.render_dir), name="renders")

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
        logger.warning("router '%s' not yet available (implemented in later task)", _name)

try:
    from routers import auth as auth_router
    app.include_router(auth_router.router, tags=["auth"])
except ImportError:
    logger.warning("router 'auth' not yet available")


# Removed startup event in favor of modern Lifespan manager


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
