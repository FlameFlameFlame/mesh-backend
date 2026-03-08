Note: All of the code was written by LLMs: Claude Code and ChatGPT.

# Project Description
mesh-backend is a FastAPI service for the mesh planner application. It exposes planner APIs and can serve the built frontend bundle.

# How to Run It
```bash
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or run the helper entrypoint:

```bash
uv run mesh-web
```

If you want to serve a specific frontend build:

```bash
FRONTEND_DIST_DIR=../mesh-generator/dist uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

# High-Level Implementation Details
The service is structured around `app/` modules and serves `/api/v2/*` endpoints for projects, optimization workflows, and result handling. It integrates `mesh_calculator` for optimization and radio-planning computations, and mounts static frontend files from a configured `FRONTEND_DIST_DIR` directory.
