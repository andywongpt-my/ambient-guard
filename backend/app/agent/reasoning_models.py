"""Reasoning output models (design.md §3).

A Recommendation MUST carry >=1 Evidence item (FR-4.2), enforced by the engine.
Assessment is the full pipeline output returned by /api/v1/assess.

G2.6: Enhanced with structured explanation data for full reconstructability.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.agent.models import ContextIntent
from app.environmental.base import Observation


class Evidence(BaseModel):
    observation: Observation
    note: str                    # why this observation matters for the activity
    severity: str                # "info" | "caution" | "warning"


class PlannedWindow(BaseModel):
    """G2.6: Conditions at the planned activity time."""
    time: datetime
    severity: str                # "info" | "caution" | "warning"
    aqi: float | None = None
    pm25: float | None = None
    uv: float | None = None
    temp_c: float | None = None
    humidity: float | None = None
    data_kind: str               # "observed" | "forecast"


class AlternativeWindow(BaseModel):
    """G2.6: A candidate alternative time window."""
    time: datetime
    severity: str
    improvement: float           # Negative = better than planned
    better_metrics: list[str]
    worse_metrics: list[str]
    aqi: float | None = None
    pm25: float | None = None
    uv: float | None = None
    temp_c: float | None = None


class Recommendation(BaseModel):
    text: str
    reasoning_summary: str
    evidence: list[Evidence]     # len >= 1 (guardrail)
    timestamps: dict[str, datetime | None]
    confidence: float


class Assessment(BaseModel):
    context: ContextIntent
    observations: list[Observation]
    recommendation: Recommendation
    provider_errors: list[str] = []
    
    # G2.6: Structured explanation data
    planned_window: PlannedWindow | None = None
    alternatives: list[AlternativeWindow] = []
    recommended_time: datetime | None = None
    reason_codes: list[str] = []
    limitations: list[str] = []
