# Change Summary

- 2026-03-08: Added a full `/api/v2` backend compatibility layer by vendoring the former `mesh-generator` Flask backend package into `mesh-backend` and mounting it behind FastAPI via WSGI path translation.
- 2026-03-08: Added backend static frontend serving (`FRONTEND_DIST_DIR`, defaulting to `../mesh-generator/dist`) so one host can serve both UI and `/api/v2`.
- 2026-03-08: Removed deprecated v1 FastAPI optimize/roads modules and replaced backend tests with `/api/v2` integration coverage (projects, sites, export/load, pipeline generate, optimization preconditions, SSE done/error/canceled, and v1 health removal).
- 2026-03-08: Updated backend dependencies and lockfile to include migrated Flask/H3/raster runtime requirements and aligned `requires-python` to `>=3.11`.
