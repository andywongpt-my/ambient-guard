"""G7 Guard Mode — Data models for persistent guard state.

This module implements the data model for proactive environmental monitoring:
- Guard: A monitored upcoming activity
- GuardAssessment: Snapshot of decision at a point in time
- GuardAlert: Material change notification

Privacy-by-design: Only normalized, minimal data is persisted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4
import hashlib
import json


class GuardStatus(str, Enum):
    """Guard lifecycle states."""
    DISCOVERED = "discovered"
    ACTIVE = "active"
    UNCHANGED = "unchanged"
    MATERIAL_CHANGE_DETECTED = "material_change_detected"
    ALERT_READY = "alert_ready"
    ACKNOWLEDGED = "acknowledged"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    INSUFFICIENT_DATA = "insufficient_data"


class AlertChangeType(str, Enum):
    """Types of material changes that trigger alerts."""
    DECISION_STATE_CHANGE = "decision_state_change"
    SEVERITY_ESCALATION = "severity_escalation"
    SEVERITY_IMPROVEMENT = "severity_improvement"
    BETTER_WINDOW_APPEARED = "better_window_appeared"
    BETTER_WINDOW_DISAPPEARED = "better_window_disappeared"
    PERSONAL_CONFLICT_INTRODUCED = "personal_conflict_introduced"
    PERSONAL_CONFLICT_REMOVED = "personal_conflict_removed"
    ENVIRONMENTAL_THRESHOLD_CROSSED = "environmental_threshold_crossed"
    FORECAST_CONFIDENCE_CHANGE = "forecast_confidence_change"


# Guard-worthy activities (G7.11)
GUARD_WORTHY_ACTIVITIES = {
    "jogging", "running", "walking", "cycling", "hiking",
    "swimming", "outdoor_exercise", "outdoor_work", "outdoor_commute",
    "picnic", "gardening", "outdoor_family_activity",
}

# Minimum context confidence for guard creation
MIN_GUARD_CONFIDENCE = 0.7

# Default reassessment interval (minutes)
DEFAULT_REASSESSMENT_INTERVAL_MINUTES = 45

# Guard expiration: grace period after planned time (hours)
GUARD_EXPIRATION_GRACE_HOURS = 2

# Retention period after expiration (days)
GUARD_RETENTION_DAYS = 7


@dataclass
class Guard:
    """A monitored upcoming activity with environmental decision tracking."""
    
    guard_id: str
    activity: str
    planned_time: datetime
    status: GuardStatus
    
    # Location (normalized)
    location_lat: float | None = None
    location_lon: float | None = None
    location_name: str | None = None
    
    # Bee source reference (hashed, not raw text)
    bee_source_type: str | None = None  # 'bee_todo' | 'bee_conversation'
    bee_source_reference_hash: str | None = None
    
    # Lifecycle timestamps
    created_at: datetime | None = None
    expires_at: datetime | None = None
    last_assessed_at: datetime | None = None
    next_assessment_at: datetime | None = None
    
    # Assessment tracking
    assessment_count: int = 0
    
    # Additional metadata (JSONB)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        activity: str,
        planned_time: datetime,
        location_lat: float | None = None,
        location_lon: float | None = None,
        location_name: str | None = None,
        bee_source_type: str | None = None,
        bee_source_reference: str | None = None,
    ) -> "Guard":
        """Create a new guard with defaults."""
        now = datetime.utcnow()
        guard_id = str(uuid4())
        
        # Hash the Bee source reference for privacy (don't store raw text)
        bee_source_hash = None
        if bee_source_reference:
            bee_source_hash = hashlib.sha256(bee_source_reference.encode()).hexdigest()
        
        # Calculate expiration: planned_time + grace period
        expires_at = planned_time + timedelta(hours=GUARD_EXPIRATION_GRACE_HOURS)
        
        return cls(
            guard_id=guard_id,
            activity=activity,
            planned_time=planned_time,
            status=GuardStatus.DISCOVERED,
            location_lat=location_lat,
            location_lon=location_lon,
            location_name=location_name,
            bee_source_type=bee_source_type,
            bee_source_reference_hash=bee_source_hash,
            created_at=now,
            expires_at=expires_at,
        )
    
    def is_expired(self) -> bool:
        """Check if guard has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_guard_worthy(self) -> bool:
        """Check if activity qualifies for guard monitoring."""
        activity_lower = self.activity.lower()
        return any(
            worthy in activity_lower or activity_lower in worthy
            for worthy in GUARD_WORTHY_ACTIVITIES
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize for API response."""
        return {
            "guard_id": self.guard_id,
            "activity": self.activity,
            "planned_time": self.planned_time.isoformat() if self.planned_time else None,
            "status": self.status.value,
            "location": {
                "lat": self.location_lat,
                "lon": self.location_lon,
                "name": self.location_name,
            } if self.location_lat is not None else None,
            "bee_source_type": self.bee_source_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_assessed_at": self.last_assessed_at.isoformat() if self.last_assessed_at else None,
            "next_assessment_at": self.next_assessment_at.isoformat() if self.next_assessment_at else None,
            "assessment_count": self.assessment_count,
        }


@dataclass
class GuardAssessment:
    """Snapshot of a guard's decision at a specific point in time."""
    
    guard_id: str
    assessment_number: int
    decision_state: str
    assessed_at: datetime
    
    # Decision components
    severity: str | None = None  # 'info' | 'caution' | 'warning'
    environmental_summary: dict[str, Any] = field(default_factory=dict)
    candidate_windows: list[dict[str, Any]] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    
    # Personal context (G3)
    personal_constraints: list[dict[str, Any]] = field(default_factory=list)
    personal_feasibility: dict[str, Any] | None = None
    
    # Data quality tracking
    data_quality: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        guard_id: str,
        assessment_number: int,
        decision_state: str,
        severity: str | None = None,
        environmental_summary: dict[str, Any] | None = None,
        candidate_windows: list[dict[str, Any]] | None = None,
        reason_codes: list[str] | None = None,
        personal_constraints: list[dict[str, Any]] | None = None,
        personal_feasibility: dict[str, Any] | None = None,
        data_quality: dict[str, Any] | None = None,
    ) -> "GuardAssessment":
        """Create a new assessment with timestamp."""
        return cls(
            guard_id=guard_id,
            assessment_number=assessment_number,
            decision_state=decision_state,
            assessed_at=datetime.utcnow(),
            severity=severity,
            environmental_summary=environmental_summary or {},
            candidate_windows=candidate_windows or [],
            reason_codes=reason_codes or [],
            personal_constraints=personal_constraints or [],
            personal_feasibility=personal_feasibility,
            data_quality=data_quality or {},
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize for API response."""
        return {
            "guard_id": self.guard_id,
            "assessment_number": self.assessment_number,
            "decision_state": self.decision_state,
            "severity": self.severity,
            "assessed_at": self.assessed_at.isoformat(),
            "environmental_summary": self.environmental_summary,
            "candidate_windows": self.candidate_windows,
            "reason_codes": self.reason_codes,
            "personal_constraints": self.personal_constraints,
            "personal_feasibility": self.personal_feasibility,
            "data_quality": self.data_quality,
        }


@dataclass
class GuardAlert:
    """Notification of a material decision change for a guard."""
    
    guard_id: str
    previous_state: str
    new_state: str
    change_type: AlertChangeType
    reason_codes: list[str]
    evidence: dict[str, Any]
    
    # Metadata
    alert_id: str | None = None
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    created_at: datetime | None = None
    
    @classmethod
    def create(
        cls,
        guard_id: str,
        previous_state: str,
        new_state: str,
        change_type: AlertChangeType,
        reason_codes: list[str],
        evidence: dict[str, Any],
    ) -> "GuardAlert":
        """Create a new alert with timestamp."""
        from uuid import uuid4
        now = datetime.utcnow()
        return cls(
            alert_id=str(uuid4()),
            guard_id=guard_id,
            previous_state=previous_state,
            new_state=new_state,
            change_type=change_type,
            reason_codes=reason_codes,
            evidence=evidence,
            created_at=now,
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize for API response."""
        return {
            "alert_id": self.alert_id,
            "guard_id": self.guard_id,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "change_type": self.change_type.value,
            "reason_codes": self.reason_codes,
            "evidence": self.evidence,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def hash_bee_reference(reference: str) -> str:
    """Hash a Bee reference for privacy-safe storage."""
    return hashlib.sha256(reference.encode()).hexdigest()
