# Change Summary

- 2026-03-08: Switched FastAPI-to-Flask adapter from deprecated `starlette.middleware.wsgi.WSGIMiddleware` to `a2wsgi.WSGIMiddleware` to improve SSE delivery behavior (live optimization log streaming) and remove deprecation risk.
- 2026-03-08: Added explicit `mesh_calculator` stdout streaming in backend runtime by attaching a dedicated stdout handler to the `mesh_calculator` logger (plus existing SSE handler), respecting `LOG_LEVEL` (default `INFO`) so optimization internals are visible in the backend terminal output.
- 2026-03-08: Optimization jobs now write per-run log files under `<project_dir>/logs/optimization_*.log`; `/api/v2/run-optimization` response includes `log_file` path, and `OptimizationJobManager` now mirrors streamed events/logs to disk.
- 2026-03-08: Added `uv run mesh-web` command (`app/run_web.py`) to build frontend (`mesh-generator`) and start backend (`uvicorn app.main:app`) in one step; supports `--skip-build`, custom host/port, and custom frontend path.
- 2026-03-08: Added a full `/api/v2` backend compatibility layer by vendoring the former `mesh-generator` Flask backend package into `mesh-backend` and mounting it behind FastAPI via WSGI path translation.
- 2026-03-08: Added backend static frontend serving (`FRONTEND_DIST_DIR`, defaulting to `../mesh-generator/dist`) so one host can serve both UI and `/api/v2`.
- 2026-03-08: Removed deprecated v1 FastAPI optimize/roads modules and replaced backend tests with `/api/v2` integration coverage (projects, sites, export/load, pipeline generate, optimization preconditions, SSE done/error/canceled, and v1 health removal).
- 2026-03-08: Updated backend dependencies and lockfile to include migrated Flask/H3/raster runtime requirements and aligned `requires-python` to `>=3.11`.
