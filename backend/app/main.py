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

from app.bee import BeeError, get_bee_client

app = FastAPI(title="Ambient Guard", version="0.2.0")


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


class AssessRequest(BaseModel):
    location: str | None = None
    time: str | None = None
    intent_override: str | None = None


@app.post("/api/v1/assess")
def assess(req: AssessRequest) -> dict:
    # STUB — context normalization -> environment -> reasoning arrives in M2-M4.
    return {
        "stub": True,
        "note": "assess pipeline not yet implemented (M2-M4); Bee ingress is live at /api/v1/bee/context",
        "echo": req.model_dump(),
        "bee_mode": os.getenv("AMBIENT_GUARD_BEE_MODE", "mock"),
    }
