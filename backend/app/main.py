"""Ambient Guard FastAPI app.

M1.2: the Bee integration layer is wired in — GET /api/v1/bee/context returns REAL
Bee data (today-context + current location + optional search) via the backend
selected by AMBIENT_GUARD_BEE_MODE. The full assess pipeline (context normalization
-> environment -> reasoning) lands in M2-M4.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent.normalize import normalize
from app.agent.reasoning import ReasoningEngine, ReasoningError
from app.bee import BeeError, get_bee_client
from app.bee.models import BeeSearchResult
from app.environmental import EnvironmentalService

app = FastAPI(title="Ambient Guard", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # demo; tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

_env_service = EnvironmentalService()
_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


def _safe_search(client, query: str | None, limit: int):
    """bee_search is a SUPPLEMENTARY intent source and is currently prone to
    server-side hangs (see FRICTION_LOG FR-007). today-context + activeTodos already
    carry the intent, so a search failure must NOT break the pipeline — swallow it
    and continue with the rest of the context."""
    if not query:
        return None, None
    try:
        return client.search(query, limit=limit), None
    except BeeError as e:
        return None, f"bee_search unavailable: {e}"


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
    except BeeError as e:
        raise HTTPException(status_code=502, detail=f"Bee integration error: {e}") from e
    search, search_err = _safe_search(client, query, limit)

    intent = normalize(today, location, search)
    out = intent.model_dump(mode="json")
    if search_err:
        out.setdefault("notes", []).append(search_err)
    return {"bee_mode": os.getenv("AMBIENT_GUARD_BEE_MODE", "mock"), "context": out}


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
    except BeeError as e:
        raise HTTPException(status_code=502, detail=f"Bee integration error: {e}") from e
    search, _search_err = _safe_search(client, req.query, 5)

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


@app.get("/api/v1/timeline")
def timeline(
    lat: float = Query(...),
    lon: float = Query(...),
    hours: int = Query(default=6, ge=1, le=12),
) -> dict:
    """Environmental timeline (M5 seed): AQI/UV/temp at hourly steps from now.

    Each entry is labeled observed vs forecast. Built from the same provider layer.
    """
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    entries = []
    for h in range(hours + 1):
        when = now + timedelta(hours=h)
        obs, errors = _env_service.observe(lat, lon, when=when)
        by = {o.metric: o for o in obs}
        entries.append({
            "time": when.isoformat(),
            "kind": "observed" if h == 0 else "forecast",
            "aqi": by["aqi"].value if "aqi" in by else None,
            "uv": by["uv"].value if "uv" in by else None,
            "temp_c": by["temp_c"].value if "temp_c" in by else None,
            "pm25": by["pm25"].value if "pm25" in by else None,
        })
    return {"entries": entries}


# --- static demo UI (zero-build; served by the backend) ---------------------
if os.path.isdir(_STATIC_DIR):
    app.mount("/ui", StaticFiles(directory=_STATIC_DIR, html=True), name="ui")


@app.get("/")
def root() -> FileResponse:
    index = os.path.join(_STATIC_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    raise HTTPException(status_code=404, detail="UI not built")
