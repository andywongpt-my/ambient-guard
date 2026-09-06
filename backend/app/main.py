"""Ambient Guard FastAPI app — M0 baseline skeleton.

Real pipeline lands in M1–M4. For now /health is live and /api/v1/assess returns
a clearly-marked stub so the container and CI have something to exercise.
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Ambient Guard", version="0.1.0")


class Health(BaseModel):
    status: str
    bee_mode: str


@app.get("/health", response_model=Health)
def health() -> Health:
    return Health(status="ok", bee_mode=os.getenv("AMBIENT_GUARD_BEE_MODE", "mock"))


class AssessRequest(BaseModel):
    location: str | None = None
    time: str | None = None
    intent_override: str | None = None


@app.post("/api/v1/assess")
def assess(req: AssessRequest) -> dict:
    # STUB — real Bee -> context -> environment -> reasoning pipeline arrives in M1-M4.
    return {
        "stub": True,
        "note": "assess pipeline not yet implemented (M1-M4)",
        "echo": req.model_dump(),
        "bee_mode": os.getenv("AMBIENT_GUARD_BEE_MODE", "mock"),
    }
