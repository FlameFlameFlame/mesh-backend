from pathlib import Path

import generator.app as generator_app_mod
import generator.handlers.pipeline_site_handlers as pipeline_handlers


SAMPLE_ROADS = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[44.5000, 40.1700], [44.5100, 40.1800]],
            },
            "properties": {"highway": "primary", "name": "Sample"},
        }
    ],
}


def _add_site(client, name: str, lat: float, lon: float):
    resp = client.post(
        "/api/v2/sites",
        json={
            "name": name,
            "lat": lat,
            "lon": lon,
            "priority": 1,
            "site_height_m": 0.0,
            "fetch_city": False,
        },
    )
    assert resp.status_code == 200


def test_health_and_frontend_root(client):
    health = client.get("/api/v2/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["api_version"] == "v2"

    root = client.get("/")
    assert root.status_code == 200
    assert "mesh frontend" in root.text


def test_v1_health_is_removed(client):
    legacy = client.get("/api/health")
    assert legacy.status_code == 404


def test_projects_lifecycle(client, projects_dir):
    created = client.post("/api/v2/projects/create", json={"name": "demo"})
    assert created.status_code == 200

    listed = client.get("/api/v2/projects")
    assert listed.status_code == 200
    payload = listed.json()
    names = [p["name"] for p in payload["projects"]]
    assert "demo" in names
    assert Path(payload["root"]) == projects_dir

    runs = client.get("/api/v2/projects/runs", params={"project_name": "demo"})
    assert runs.status_code == 200
    assert runs.json()["runs"] == []

    renamed = client.post("/api/v2/projects/rename", json={"old_name": "demo", "new_name": "demo-renamed"})
    assert renamed.status_code == 200

    opened = client.post("/api/v2/projects/open", json={"project_name": "demo-renamed"})
    assert opened.status_code == 200
    assert opened.json()["project_name"] == "demo-renamed"


def test_sites_export_and_load(client):
    create_project = client.post("/api/v2/projects/create", json={"name": "demo"})
    assert create_project.status_code == 200

    _add_site(client, "A", 40.1750, 44.5050)
    _add_site(client, "B", 40.1810, 44.5110)

    exported = client.post(
        "/api/v2/export",
        json={
            "project_name": "demo",
            "parameters": {"max_towers_per_route": 5},
        },
    )
    assert exported.status_code == 200
    config_path = Path(exported.json()["config_path"])
    assert config_path.is_file()

    loaded = client.post("/api/v2/load", json={"path": str(config_path)})
    assert loaded.status_code == 200
    loaded_payload = loaded.json()
    assert "sites" in loaded_payload
    assert len(loaded_payload["sites"]) == 2

    cleared = client.post("/api/v2/clear")
    assert cleared.status_code == 200
    sites = client.get("/api/v2/sites")
    assert sites.status_code == 200
    assert sites.json() == []


def test_generate_with_mocked_roads(client, monkeypatch):
    _add_site(client, "A", 40.1750, 44.5050)
    _add_site(client, "B", 40.1810, 44.5110)

    monkeypatch.setattr(pipeline_handlers, "fetch_roads_cached", lambda *args, **kwargs: SAMPLE_ROADS)

    generated = client.post("/api/v2/generate", json={"project_name": "demo"})
    assert generated.status_code == 200
    payload = generated.json()
    assert payload["road_count"] == 1
    assert "roads" in payload["layers"]


def test_optimization_preconditions_and_cancel(client):
    run_resp = client.post("/api/v2/run-optimization", json={"project_name": "demo"})
    assert run_resp.status_code == 400
    assert "Filter P2P" in run_resp.json()["error"]

    cancel_resp = client.post("/api/v2/cancel-optimization")
    assert cancel_resp.status_code == 409


def test_optimization_stream_done_error_and_canceled(client):
    generator_app_mod._job_manager.prepare_new_job()
    generator_app_mod._job_manager.put({"progress": {"stage": "run", "percent": 25}})
    generator_app_mod._job_manager.put({"done": True, "summary": {"total_towers": 1}})
    done_stream = client.get("/api/v2/optimization-stream")
    assert done_stream.status_code == 200
    assert '"done": true' in done_stream.text.lower()

    generator_app_mod._job_manager.prepare_new_job()
    generator_app_mod._job_manager.put({"error": "boom"})
    error_stream = client.get("/api/v2/optimization-stream")
    assert error_stream.status_code == 200
    assert "boom" in error_stream.text

    generator_app_mod._job_manager.prepare_new_job()
    generator_app_mod._job_manager.put({"canceled": True, "message": "user canceled"})
    cancel_stream = client.get("/api/v2/optimization-stream")
    assert cancel_stream.status_code == 200
    assert "canceled" in cancel_stream.text.lower()
