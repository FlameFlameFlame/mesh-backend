from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
import generator.app as generator_app_mod


@pytest.fixture
def projects_dir(tmp_path, monkeypatch) -> Path:
    projects = tmp_path / "projects"
    projects.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(generator_app_mod, "DEFAULT_OUTPUT_DIR", str(projects))
    return projects


@pytest.fixture
def client(tmp_path, monkeypatch, projects_dir):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "index.html").write_text("<!doctype html><html><body>mesh frontend</body></html>", encoding="utf-8")
    monkeypatch.setenv("FRONTEND_DIST_DIR", str(dist_dir))

    app = create_app()
    with TestClient(app) as test_client:
        test_client.post("/api/v2/clear")
        generator_app_mod._job_manager.prepare_new_job()
        generator_app_mod._job_manager.mark_finished()
        yield test_client
        test_client.post("/api/v2/clear")
        generator_app_mod._job_manager.prepare_new_job()
        generator_app_mod._job_manager.mark_finished()
