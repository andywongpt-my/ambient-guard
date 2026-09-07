"""Reasoning output models (design.md §3).

A Recommendation MUST carry >=1 Evidence item (FR-4.2), enforced by the engine.
Assessment is the full pipeline output returned by /api/v1/assess.

G2.6: Enhanced with structured explanation data for full reconstructability.

G3: Enhanced with personal context intelligence:
- Personal feasibility evaluation for candidate windows
- Decision state machine outputs
- Personal Environmental Timeline
- Context provenance and freshness
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

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
    
    # G3: Personal feasibility for this candidate
    personal_feasibility_status: str | None = None  # "feasible" | "conflicting" | "unknown"
    personal_conflicts: list[dict[str, Any]] = []   # List of conflicting constraints


class PersonalConstraintRecord(BaseModel):
    """G3.11: A personal constraint used in the decision, with provenance."""
    constraint_type: str
    value: str                   # ISO time or description
    source_type: str             # "bee_todo" | "bee_conversation" | etc.
    source_id: str | None = None
    confidence: str              # "high" | "medium" | "low"


class PersonalContextRecord(BaseModel):
    """G3: Personal context used in the decision, sanitized for output."""
    constraints: list[PersonalConstraintRecord] = []
    preferences: list[dict[str, Any]] = []
    freshness: dict[str, Any] = {}  # Summary of freshness evaluation


class TimelineEntry(BaseModel):
    """G3.9: A single entry in the Personal Environmental Timeline."""
    time: datetime
    entry_type: str              # "bee_context" | "environmental" | "alternative" | "planned"
    label: str                   # Human-readable description
    environmental_conditions: dict[str, Any] | None = None
    bee_context: str | None = None  # Sanitized Bee context description
    exposure_kind: str | None = None  # "outdoor" | "transit" | "indoor"
    data_kind: str | None = None     # "observed" | "forecast"
    uncertainty: list[str] = []


class PersonalEnvironmentalTimeline(BaseModel):
    """G3.9: Timeline combining Bee context with environmental conditions."""
    entries: list[TimelineEntry] = []
    date: str | None = None
    timezone: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "timezone": self.timezone,
            "entries": [e.model_dump() for e in self.entries],
        }


class Recommendation(BaseModel):
    text: str
    reasoning_summary: str
    evidence: list[Evidence]     # len >= 1 (guardrail)
    timestamps: dict[str, datetime | None]
    confidence: float
    
    # G3: Decision state
    decision_state: str | None = None  # Machine-readable state


class Assessment(BaseModel):
    context: ContextIntent
    observations: list[Observation]
    recommendation: Recommendation
    provider_errors: list[str] = []
    
    # G2.6: Structured explanation data
    planned_window: PlannedWindow | None = None
    alternatives: list[AlternativeWindow] = []
    # G2.7: Distinguish environmentally-better from personally-recommended
    environmentally_better_window: datetime | None = None  # Based on environmental evidence only
    recommended_window: datetime | None = None  # May be None if personal feasibility unknown
    reason_codes: list[str] = []
    limitations: list[str] = []
    
    # G3: Personal context intelligence
    personal_context: PersonalContextRecord | None = None
    candidate_evaluations: list[dict[str, Any]] = []  # Feasibility evaluation for each candidate
    decision_state: str | None = None  # Machine-readable state from state machine
    natural_language_recommendation: str | None = None  # Final NL output
    timeline: PersonalEnvironmentalTimeline | None = None  # G3.9
