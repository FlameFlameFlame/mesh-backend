# mesh-backend

Backend service for the mesh planner UI and calculation APIs.

## What it serves

- `/api/v2/*` endpoints (projects, sites, pipeline, optimization, coverage, load/export, SSE)
- Frontend static assets from `FRONTEND_DIST_DIR` (or `../mesh-generator/dist` by default)

## Run

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## One-command Run (build frontend + start backend)

```bash
uv run mesh-web
```

Optional flags:

```bash
uv run mesh-web --host 127.0.0.1 --port 8000
uv run mesh-web --skip-build
uv run mesh-web --frontend-dir /path/to/mesh-generator
```

## Serve a specific frontend build

```bash
FRONTEND_DIST_DIR=/Users/timur/Documents/src/LoraMeshPlanner/mesh-generator/dist \
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`.

## Health check

```bash
curl http://127.0.0.1:8000/api/v2/health
```

## Optimization Logs

- Live UI stream: Optimization panel -> Optimization Log.
- Per-run file logs: saved under `<project_dir>/logs/optimization_*.log`.
- `POST /api/v2/run-optimization` now returns `log_file` with the exact path.

Server stdout is the terminal where you launched `uv run mesh-web` (or `uvicorn`).

Examples:

```bash
# Save stdout/stderr to a file while still seeing it in terminal
uv run mesh-web 2>&1 | tee /tmp/mesh-web.log

# Follow saved process output
tail -f /tmp/mesh-web.log
```
