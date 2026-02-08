import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator

import structlog

from ..services.engine import run_optimize

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api")


class SiteIn(BaseModel):
    name: str
    lat: float
    lon: float
    priority: int


class OptimizeRequest(BaseModel):
    sites: list[SiteIn]
    roads: dict
    parameters: Optional[dict] = None

    @field_validator("sites")
    @classmethod
    def sites_not_empty(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 sites are required")
        return v

    @field_validator("roads")
    @classmethod
    def roads_not_empty(cls, v):
        features = v.get("features", [])
        if len(features) == 0:
            raise ValueError("Roads must contain at least one feature")
        return v


@router.post("/optimize")
async def optimize(
    request: OptimizeRequest,
    include_coverage: bool = Query(False),
):
    # Validate at least one priority-1 site
    if not any(s.priority == 1 for s in request.sites):
        raise HTTPException(status_code=400, detail="At least one priority-1 site is required")

    sites_dicts = [s.model_dump() for s in request.sites]
    params = request.parameters

    logger.info("Optimize request received", sites=len(sites_dicts), include_coverage=include_coverage)

    result = await asyncio.to_thread(
        run_optimize, sites_dicts, request.roads, params, include_coverage
    )

    return result
