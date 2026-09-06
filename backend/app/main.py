"""Ambient Guard FastAPI app.

M1.2: the Bee integration layer is wired in — GET /api/v1/bee/context returns REAL
Bee data (today-context + current location + optional search) via the backend
selected by AMBIENT_GUARD_BEE_MODE. The full assess pipeline (context normalization
-> environment -> reasoning) lands in M2-M4.
"""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.agent.normalize import normalize
from app.agent.reasoning import ReasoningEngine, ReasoningError
from app.bee import BeeError, get_bee_client
from app.bee.models import BeeSearchResult
from app.environmental import EnvironmentalService

app = FastAPI(title="Ambient Guard", version="0.4.0")

_env_service = EnvironmentalService()


class Health(BaseModel):
    status: str
    bee_mode: str


@app.get("/health", response_model=Health)
def health() -> Health:
    return Health(status="ok", bee_mode=os.getenv("AMBIENT_GUARD_BEE_MODE", "mock"))


@app.get("/api/v1/bee/context")
def bee_context(
    query: str | None = Query(default=None, description="Optional intent search term, e.g. 'jog'"),
    limit: int = Query(default=5, ge=1, le=50),
) -> dict:
    """Pull real Bee context. This is where Bee data ENTERS Ambient Guard.

    Returns today-context, current location, and (if a query is given) search hits.
    Bee failures surface as 502 rather than an empty-but-ok body (FR-1.2).
    """
    client = get_bee_client()
    try:
        today = client.today_context()
        location = client.current_location()
        search = client.search(query, limit=limit) if query else None
    except BeeError as e:
        raise HTTPException(status_code=502, detail=f"Bee integration error: {e}") from e

    return {
        "bee_mode": os.getenv("AMBIENT_GUARD_BEE_MODE", "mock"),
        "today_context": today.model_dump(),
        "current_location": location.model_dump(),
        "search": search.model_dump() if search else None,
    }


@app.get("/api/v1/context")
def context(
    query: str | None = Query(default="jog run walk cycle exercise", description="Intent search terms"),
    limit: int = Query(default=5, ge=1, le=50),
) -> dict:
    """Normalize real Bee context into a structured ContextIntent (M3).

    Pulls today-context + current location + intent search, then extracts
    activity / planned_time / location with traceability and confidence.
    """
    client = get_bee_client()
    try:
        today = client.today_context()
        location = client.current_location()
        search = client.search(query, limit=limit) if query else None
    except BeeError as e:
        raise HTTPException(status_code=502, detail=f"Bee integration error: {e}") from e

    intent = normalize(today, location, search)
    return {"bee_mode": os.getenv("AMBIENT_GUARD_BEE_MODE", "mock"), "context": intent.model_dump(mode="json")}


@app.get("/api/v1/environment")
def environment(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
) -> dict:
    """Environmental observations for a location (M2). Provider errors are explicit."""
    observations, errors = _env_service.observe(lat, lon)
    return {
        "observations": [o.model_dump(mode="json") for o in observations],
        "provider_errors": errors,
    }


class AssessRequest(BaseModel):
    query: str | None = "jog run walk cycle exercise"
    intent_override: str | None = None
    lat: float | None = None
    lon: float | None = None


@app.post("/api/v1/assess")
def assess(req: AssessRequest) -> dict:
    """Full vertical slice: Bee -> ContextIntent -> environment -> one grounded recommendation."""
    client = get_bee_client()
    try:
        today = client.today_context()
        location = client.current_location()
        search = client.search(req.query, limit=5) if req.query else None
    except BeeError as e:
        raise HTTPException(status_code=502, detail=f"Bee integration error: {e}") from e

    intent = normalize(today, location, search)
    if req.intent_override:
        intent = normalize(today, location,
                           BeeSearchResult(results=[{"id": 0, "short_summary": req.intent_override}]))

    lat = req.lat if req.lat is not None else intent.latitude
    lon = req.lon if req.lon is not None else intent.longitude
    if lat is None or lon is None:
        raise HTTPException(status_code=422,
                            detail="No location available (no recent Bee location and no lat/lon or AMBIENT_GUARD_DEFAULT_LOCATION).")

    observations, provider_errors = _env_service.observe(lat, lon, when=intent.planned_time)
    try:
        assessment = ReasoningEngine().assess(intent, observations, provider_errors)
    except ReasoningError as e:
        raise HTTPException(status_code=502, detail=f"Environmental data unavailable: {e}") from e

    return {"bee_mode": os.getenv("AMBIENT_GUARD_BEE_MODE", "mock"),
            "assessment": assessment.model_dump(mode="json")}
