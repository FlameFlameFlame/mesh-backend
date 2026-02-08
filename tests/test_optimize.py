import pytest
from unittest.mock import patch, MagicMock


SAMPLE_REQUEST = {
    "sites": [
        {"name": "Yerevan", "lat": 40.1811, "lon": 44.5136, "priority": 1},
        {"name": "Gyumri", "lat": 40.7942, "lon": 43.8453, "priority": 2},
    ],
    "roads": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[44.5, 40.2], [43.85, 40.79]],
                },
                "properties": {"highway": "primary"},
            }
        ],
    },
}

MOCK_RESULT = {
    "towers": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [44.3, 40.4]},
                "properties": {"tower_id": "t1"},
            }
        ],
    },
    "report": {"total_towers": 1, "total_cells": 10},
}


@pytest.mark.anyio
async def test_optimize_returns_towers(client):
    with patch("app.routes.optimize.run_optimize", return_value=MOCK_RESULT) as mock_run:
        response = await client.post("/api/optimize", json=SAMPLE_REQUEST)
    assert response.status_code == 200
    data = response.json()
    assert "towers" in data
    assert "report" in data
    mock_run.assert_called_once()


@pytest.mark.anyio
async def test_optimize_missing_sites(client):
    request = {**SAMPLE_REQUEST, "sites": []}
    response = await client.post("/api/optimize", json=request)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_optimize_no_priority_1(client):
    request = {
        **SAMPLE_REQUEST,
        "sites": [
            {"name": "A", "lat": 40.0, "lon": 44.0, "priority": 2},
            {"name": "B", "lat": 40.5, "lon": 44.5, "priority": 3},
        ],
    }
    response = await client.post("/api/optimize", json=request)
    assert response.status_code == 400


@pytest.mark.anyio
async def test_optimize_missing_roads(client):
    request = {
        **SAMPLE_REQUEST,
        "roads": {"type": "FeatureCollection", "features": []},
    }
    response = await client.post("/api/optimize", json=request)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_optimize_includes_coverage(client):
    result_with_coverage = {
        **MOCK_RESULT,
        "coverage": {"type": "FeatureCollection", "features": []},
    }
    with patch("app.routes.optimize.run_optimize", return_value=result_with_coverage):
        response = await client.post(
            "/api/optimize", json=SAMPLE_REQUEST, params={"include_coverage": True}
        )
    assert response.status_code == 200
    data = response.json()
    assert "coverage" in data
