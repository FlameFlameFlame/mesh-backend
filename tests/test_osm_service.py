import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.osm import build_overpass_query, parse_overpass_response, fetch_roads


def test_build_overpass_query():
    query = build_overpass_query(40.1, 44.4, 40.3, 44.6)
    assert "[out:json]" in query
    assert "40.1,44.4,40.3,44.6" in query
    assert "highway" in query
    for road_type in ["motorway", "trunk", "primary", "secondary", "tertiary"]:
        assert road_type in query


def test_parse_overpass_response():
    data = {
        "elements": [
            {"type": "node", "id": 1, "lat": 40.2, "lon": 44.5},
            {"type": "node", "id": 2, "lat": 40.21, "lon": 44.51},
            {"type": "node", "id": 3, "lat": 40.22, "lon": 44.52},
            {
                "type": "way",
                "id": 100,
                "nodes": [1, 2, 3],
                "tags": {"highway": "primary", "name": "Main St"},
            },
        ]
    }
    result = parse_overpass_response(data)
    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 1
    feature = result["features"][0]
    assert feature["geometry"]["type"] == "LineString"
    assert len(feature["geometry"]["coordinates"]) == 3
    # GeoJSON is [lon, lat]
    assert feature["geometry"]["coordinates"][0] == [44.5, 40.2]
    assert feature["properties"]["highway"] == "primary"
    assert feature["properties"]["name"] == "Main St"


def test_parse_overpass_empty():
    result = parse_overpass_response({"elements": []})
    assert result["type"] == "FeatureCollection"
    assert result["features"] == []


@pytest.mark.anyio
async def test_fetch_roads_calls_overpass():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "elements": [
            {"type": "node", "id": 1, "lat": 40.2, "lon": 44.5},
            {"type": "node", "id": 2, "lat": 40.21, "lon": 44.51},
            {
                "type": "way",
                "id": 100,
                "nodes": [1, 2],
                "tags": {"highway": "primary"},
            },
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.osm.httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await fetch_roads(40.1, 44.4, 40.3, 44.6)

    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 1
    mock_client_instance.post.assert_called_once()
