"""Shared domain models — the structured output of context normalization.

Mirrors design.md §3. Every ContextIntent carries a SourceRef (traceability, FR-2.2)
and a confidence (FR-2.1). Fields that cannot be determined stay None with reduced
confidence — never invented (FR-2.3 / no unsupported inference).
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    provider: str                       # "bee"
    ref_id: str | None = None           # e.g. Bee conversation id
    observed_at: datetime | None = None
    location: str | None = None


class ContextIntent(BaseModel):
    activity: str | None = None
    planned_time: datetime | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_is_recent: bool | None = None   # from Bee; drives R3 fallback decisions
    intent_text: str
    source_ref: SourceRef
    confidence: float = Field(ge=0.0, le=1.0)
    notes: list[str] = []               # human-readable trace of how fields were derived
