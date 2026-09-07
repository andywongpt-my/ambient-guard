"""Shared domain models — the structured output of context normalization.

Mirrors design.md §3. Every ContextIntent carries a SourceRef (traceability, FR-2.2)
and a confidence (FR-2.1). Fields that cannot be determined stay None with reduced
confidence — never invented (FR-2.3 / no unsupported inference).

G2.2: Confidence is now decomposed per field with explicit sources, making the
overall confidence reconstructable rather than a single opaque number.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    provider: str                       # "bee"
    ref_id: str | None = None           # e.g. Bee conversation id
    observed_at: datetime | None = None
    location: str | None = None


class FieldConfidence(BaseModel):
    """G2.2: Per-field confidence decomposition with explicit source attribution."""
    value: str | float | datetime | None = None
    source: str | None = None           # "bee_todo" | "bee_conversation" | "bee_location" | "fallback" | None
    confidence: float = Field(ge=0.0, le=1.0)
    note: str | None = None


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
    
    # G2.2: Decomposed confidence with sources
    activity_confidence: FieldConfidence | None = None
    planned_time_confidence: FieldConfidence | None = None
    location_confidence: FieldConfidence | None = None
