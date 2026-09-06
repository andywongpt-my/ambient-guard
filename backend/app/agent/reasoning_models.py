"""Reasoning output models (design.md §3).

A Recommendation MUST carry >=1 Evidence item (FR-4.2), enforced by the engine.
Assessment is the full pipeline output returned by /api/v1/assess.
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
