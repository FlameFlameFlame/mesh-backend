"""
Wrapper around mesh_calculator pipeline for running optimization.
"""
import json
import os
import tempfile
from pathlib import Path

import structlog
from shapely.geometry import Point, MultiPoint, mapping

from mesh_calculator.core.config import MeshConfig, InputPaths, MeshCalculatorConfig
from mesh_calculator.core.elevation import ElevationProvider
from mesh_calculator.core.grid import load_boundary, load_roads, generate_road_grid
from mesh_calculator.data.sites import load_sites
from mesh_calculator.data.cache import LOSCache
from mesh_calculator.data.exporters import (
    export_towers_geojson,
    export_coverage_geojson,
    generate_report,
)
from mesh_calculator.network.graph import MeshSurface
from mesh_calculator.network.routing import build_routing_graph
from mesh_calculator.optimization.hierarchical import connect_sites_by_priority

logger = structlog.get_logger(__name__)

ELEVATION_PATH = str(
    Path(__file__).resolve().parent.parent.parent / "mesh-engine" / "data" / "armenia_elevation.tif"
)


def write_sites_geojson(sites: list[dict], path: str):
    features = []
    for site in sites:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [site["lon"], site["lat"]],
            },
            "properties": {
                "name": site["name"],
                "priority": site["priority"],
            },
        })
    with open(path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f)


def write_roads_geojson(roads: dict, path: str):
    with open(path, "w") as f:
        json.dump(roads, f)


def compute_boundary(sites: list[dict], roads: dict) -> dict:
    points = [Point(s["lon"], s["lat"]) for s in sites]
    for feat in roads.get("features", []):
        coords = feat.get("geometry", {}).get("coordinates", [])
        for coord in coords:
            points.append(Point(coord[0], coord[1]))

    multi = MultiPoint(points)
    hull = multi.convex_hull
    # Buffer by ~0.05 degrees (~5km) to ensure coverage
    buffered = hull.buffer(0.05)

    feature = {
        "type": "Feature",
        "geometry": mapping(buffered),
        "properties": {},
    }
    return {"type": "FeatureCollection", "features": [feature]}


def run_optimize(
    sites: list[dict],
    roads_geojson: dict,
    parameters: dict | None = None,
    include_coverage: bool = False,
) -> dict:
    logger.info("Starting optimization", sites=len(sites), include_coverage=include_coverage)

    config = MeshConfig(**(parameters or {}))

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write input files
        sites_path = os.path.join(tmpdir, "sites.geojson")
        write_sites_geojson(sites, sites_path)

        roads_path = os.path.join(tmpdir, "roads.geojson")
        write_roads_geojson(roads_geojson, roads_path)

        boundary_geojson = compute_boundary(sites, roads_geojson)
        boundary_path = os.path.join(tmpdir, "boundary.geojson")
        with open(boundary_path, "w") as f:
            json.dump(boundary_geojson, f)

        # Run pipeline
        logger.info("Loading input data")
        boundary = load_boundary(boundary_path)
        roads_gdf = load_roads(roads_path)
        site_objects = load_sites(sites_path, config.h3_resolution)

        logger.info("Loading elevation data")
        elevation_provider = ElevationProvider(ELEVATION_PATH)

        logger.info("Generating H3 grid")
        cells = generate_road_grid(boundary, roads_gdf, elevation_provider, config)

        logger.info("Creating mesh surface")
        surface = MeshSurface(cells, config)

        los_cache = LOSCache()

        logger.info("Building routing graph")
        routing_graph = build_routing_graph(cells, roads_gdf, config)

        logger.info("Connecting sites by priority")
        connect_sites_by_priority(site_objects, surface, routing_graph, los_cache)

        # Export results
        towers_path = os.path.join(tmpdir, "towers.geojson")
        export_towers_geojson(surface, towers_path)

        report_path = os.path.join(tmpdir, "report.json")
        generate_report(surface, report_path)

        with open(towers_path) as f:
            towers = json.load(f)
        with open(report_path) as f:
            report = json.load(f)

        result = {"towers": towers, "report": report}

        if include_coverage:
            coverage_path = os.path.join(tmpdir, "coverage.geojson")
            export_coverage_geojson(surface, coverage_path)
            with open(coverage_path) as f:
                result["coverage"] = json.load(f)

    logger.info("Optimization complete", towers=len(towers.get("features", [])))
    return result
