"""
OSM road data fetching via Overpass API.
"""
import httpx
import structlog

logger = structlog.get_logger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

HIGHWAY_TYPES = ["motorway", "trunk", "primary", "secondary", "tertiary"]


def build_overpass_query(south: float, west: float, north: float, east: float) -> str:
    bbox = f"{south},{west},{north},{east}"
    highway_filter = "|".join(HIGHWAY_TYPES)
    return (
        f'[out:json][timeout:60];'
        f'way["highway"~"^({highway_filter})$"]({bbox});'
        f'out body;>;out skel qt;'
    )


def parse_overpass_response(data: dict) -> dict:
    nodes = {}
    features = []

    for element in data.get("elements", []):
        if element["type"] == "node":
            nodes[element["id"]] = (element["lon"], element["lat"])

    for element in data.get("elements", []):
        if element["type"] != "way":
            continue
        coords = []
        for node_id in element.get("nodes", []):
            if node_id in nodes:
                coords.append(list(nodes[node_id]))
        if len(coords) < 2:
            continue
        tags = element.get("tags", {})
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": tags,
        })

    return {"type": "FeatureCollection", "features": features}


async def fetch_roads(south: float, west: float, north: float, east: float) -> dict:
    query = build_overpass_query(south, west, north, east)
    logger.info("Fetching roads from Overpass", bbox=[south, west, north, east])

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(OVERPASS_URL, data={"data": query})
        response.raise_for_status()
        data = response.json()

    feature_count = len([e for e in data.get("elements", []) if e["type"] == "way"])
    logger.info("Overpass response received", ways=feature_count)

    return parse_overpass_response(data)
