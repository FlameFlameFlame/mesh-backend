import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from a2wsgi import WSGIMiddleware

from generator import app as generator_app_mod

from .logging_config import setup_logging


class _ApiV2PathAdapter:
    """Translate `/api/v2/*` paths to legacy Flask `/api/*` handlers."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO") or "/"
        if not path.startswith("/"):
            path = f"/{path}"
        environ["PATH_INFO"] = "/api" if path == "/" else f"/api{path}"
        return self.wsgi_app(environ, start_response)


def _default_frontend_dist() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return (repo_root / "mesh-generator" / "dist").resolve()


def _resolve_frontend_dist() -> Path:
    configured = (os.getenv("FRONTEND_DIST_DIR") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return _default_frontend_dist()


def _serve_frontend(app: FastAPI, rel_path: str):
    dist_dir: Path = app.state.frontend_dist_dir
    if not dist_dir.is_dir():
        return JSONResponse(
            {
                "error": "Frontend build is missing",
                "frontend_dist_dir": str(dist_dir),
            },
            status_code=503,
        )

    cleaned = rel_path.lstrip("/")
    target = (dist_dir / cleaned).resolve()
    if cleaned:
        if target.is_file() and target.is_relative_to(dist_dir):
            return FileResponse(target)

    index_file = dist_dir / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)

    return JSONResponse(
        {
            "error": "Frontend index.html is missing",
            "frontend_dist_dir": str(dist_dir),
        },
        status_code=503,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Mesh Backend", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.frontend_dist_dir = _resolve_frontend_dist()

    @app.get("/api/v2/health")
    async def health_v2():
        return {"status": "ok", "api_version": "v2"}

    legacy_flask_app = generator_app_mod.create_app()
    app.mount("/api/v2", WSGIMiddleware(_ApiV2PathAdapter(legacy_flask_app)))

    @app.get("/", include_in_schema=False)
    async def serve_root():
        return _serve_frontend(app, "")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_paths(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        return _serve_frontend(app, full_path)

    return app


app = create_app()
