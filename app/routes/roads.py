from fastapi import APIRouter, HTTPException, Query

from ..services.osm import fetch_roads

router = APIRouter(prefix="/api")


@router.get("/roads")
async def get_roads(
    south: float = Query(...),
    west: float = Query(...),
    north: float = Query(...),
    east: float = Query(...),
):
    if south >= north:
        raise HTTPException(status_code=400, detail="south must be less than north")
    if west >= east:
        raise HTTPException(status_code=400, detail="west must be less than east")
    if (north - south) > 1.0 or (east - west) > 1.0:
        raise HTTPException(status_code=400, detail="Bounding box too large (max 1 degree)")

    return await fetch_roads(south, west, north, east)
