import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from app.services.engine import (
    write_sites_geojson,
    write_roads_geojson,
    compute_boundary,
    run_optimize,
)


SAMPLE_SITES = [
    {"name": "Yerevan", "lat": 40.1811, "lon": 44.5136, "priority": 1},
    {"name": "Gyumri", "lat": 40.7942, "lon": 43.8453, "priority": 2},
]

SAMPLE_ROADS = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[44.5, 40.2], [44.0, 40.5], [43.85, 40.79]],
            },
            "properties": {"highway": "primary"},
        }
    ],
}


def test_write_sites_geojson():
    with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as f:
        path = f.name
    try:
        write_sites_geojson(SAMPLE_SITES, path)
        with open(path) as f:
            data = json.load(f)
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 2
        feat = data["features"][0]
        assert feat["geometry"]["type"] == "Point"
        assert feat["geometry"]["coordinates"] == [44.5136, 40.1811]
        assert feat["properties"]["name"] == "Yerevan"
        assert feat["properties"]["priority"] == 1
    finally:
        os.unlink(path)


def test_write_roads_geojson():
    with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as f:
        path = f.name
    try:
        write_roads_geojson(SAMPLE_ROADS, path)
        with open(path) as f:
            data = json.load(f)
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 1
    finally:
        os.unlink(path)


def test_compute_boundary():
    boundary = compute_boundary(SAMPLE_SITES, SAMPLE_ROADS)
    assert boundary["type"] == "FeatureCollection"
    assert len(boundary["features"]) == 1
    geom = boundary["features"][0]["geometry"]
    assert geom["type"] == "Polygon"
    # Boundary should enclose all sites
    coords = geom["coordinates"][0]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    assert min(lons) < 43.85  # west of Gyumri
    assert max(lons) > 44.51  # east of Yerevan
    assert min(lats) < 40.18  # south of Yerevan
    assert max(lats) > 40.79  # north of Gyumri


@patch("app.services.engine.connect_sites_by_priority")
@patch("app.services.engine.build_routing_graph")
@patch("app.services.engine.MeshSurface")
@patch("app.services.engine.generate_road_grid")
@patch("app.services.engine.ElevationProvider")
@patch("app.services.engine.load_sites")
@patch("app.services.engine.load_roads")
@patch("app.services.engine.load_boundary")
def test_run_optimize_calls_pipeline(
    mock_load_boundary,
    mock_load_roads,
    mock_load_sites,
    mock_elevation,
    mock_generate_grid,
    mock_mesh_surface,
    mock_build_routing,
    mock_connect_sites,
):
    # Set up mocks
    mock_load_boundary.return_value = MagicMock()
    mock_load_roads.return_value = MagicMock()
    mock_load_sites.return_value = [MagicMock(), MagicMock()]
    mock_elevation.return_value = MagicMock()
    mock_generate_grid.return_value = {}
    mock_surface = MagicMock()
    mock_surface.towers = {}
    mock_surface.cells = {}
    mock_mesh_surface.return_value = mock_surface
    mock_build_routing.return_value = MagicMock()

    result = run_optimize(SAMPLE_SITES, SAMPLE_ROADS)

    mock_load_boundary.assert_called_once()
    mock_load_roads.assert_called_once()
    mock_load_sites.assert_called_once()
    mock_elevation.assert_called_once()
    mock_generate_grid.assert_called_once()
    mock_mesh_surface.assert_called_once()
    mock_build_routing.assert_called_once()
    mock_connect_sites.assert_called_once()

    assert "towers" in result
    assert "report" in result
