import json
import logging
import os

import generator.app as generator_app_mod
import mesh_calculator.optimization.route_pipeline as route_pipeline_mod


def test_optimization_stream_includes_mesh_calculator_logs(client, tmp_path, monkeypatch):
    elevation_path = tmp_path / "elevation.tif"
    elevation_path.write_bytes(b"fake")

    generator_app_mod._elevation_path = str(elevation_path)
    generator_app_mod._grid_provider = object()
    generator_app_mod._p2p_routes = [
        {
            "route_id": "route_0",
            "site1": {"name": "A", "lat": 40.17, "lon": 44.50},
            "site2": {"name": "B", "lat": 40.18, "lon": 44.51},
        }
    ]
    generator_app_mod._p2p_all_route_features = {
        "route_0": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[44.50, 40.17], [44.51, 40.18]],
                },
                "properties": {"id": "f1"},
            }
        ]
    }

    def _fake_run_route_pipeline(**kwargs):
        logging.getLogger("mesh_calculator.optimization.route_pipeline").info("SSE_LOG_TEST")
        out_dir = kwargs["output_dir"]
        with open(os.path.join(out_dir, "report.json"), "w", encoding="utf-8") as f:
            json.dump({"ok": True}, f)
        return {"total_towers": 0, "visibility_edges": 0}

    monkeypatch.setattr(route_pipeline_mod, "run_route_pipeline", _fake_run_route_pipeline)

    start = client.post("/api/v2/run-optimization", json={})
    assert start.status_code == 200

    stream = client.get("/api/v2/optimization-stream")
    assert stream.status_code == 200
    assert "SSE_LOG_TEST" in stream.text
    assert '"done": true' in stream.text.lower()
