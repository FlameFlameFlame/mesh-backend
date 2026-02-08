import pytest
from unittest.mock import AsyncMock, patch


SAMPLE_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[44.5, 40.2], [44.51, 40.21]],
            },
            "properties": {"highway": "primary"},
        }
    ],
}


@pytest.mark.anyio
async def test_roads_returns_geojson(client):
    with patch("app.routes.roads.fetch_roads", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = SAMPLE_GEOJSON
        response = await client.get(
            "/api/roads", params={"south": 40.1, "west": 44.4, "north": 40.3, "east": 44.6}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1


@pytest.mark.anyio
async def test_roads_missing_params(client):
    response = await client.get("/api/roads", params={"south": 40.1, "west": 44.4})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_roads_bbox_too_large(client):
    response = await client.get(
        "/api/roads", params={"south": 39.0, "west": 43.0, "north": 41.0, "east": 45.0}
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_roads_invalid_coords(client):
    response = await client.get(
        "/api/roads", params={"south": 41.0, "west": 44.4, "north": 40.0, "east": 44.6}
    )
    assert response.status_code == 400
