"""G3: Personal Context Intelligence — extract constraints, preferences, and feasibility.

This module transforms raw Bee context into structured personal constraints and preferences
that can be evaluated against environmental candidates. It implements the core G3 decision
model:

    Environmental Suitability → What environmental conditions suggest
    Personal Feasibility → Whether the alternative is compatible with user context
    Final Recommendation → Whether enough evidence exists to recommend to this user

Key principles (G3.3, G3.7):
- Do NOT convert unknown information into assumed feasibility
- If we don't know whether 23:00 is convenient, return "unknown", not "feasible"
- Never force a recommendation when personal feasibility is unknown or conflicting

Privacy-by-Design (G3.10):
- Only retrieve context relevant to the current decision (data minimization)
- Store the smallest normalized representation possible
- Document what is queried, transformed, retained, and discarded
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class ConstraintType(str, Enum):
    """Types of personal constraints that affect activity timing."""
    UNAVAILABLE_BEFORE = "unavailable_before"           # Cannot start before time X
    UNAVAILABLE_AFTER = "unavailable_after"             # Cannot start after time X
    LATEST_ACTIVITY_END = "latest_activity_end"         # Must end by time X
    FIXED_COMMITMENT = "fixed_commitment"               # Busy during time window
    PREFERRED_WINDOW = "preferred_window"               # Preference for time window


class PreferenceType(str, Enum):
    """Types of personal preferences (weaker than constraints)."""
    PREFERRED_ACTIVITY_WINDOW = "preferred_activity_window"
    TIME_PREFERENCE = "time_preference"


class FeasibilityStatus(str, Enum):
    """Personal feasibility evaluation result."""
    FEASIBLE = "feasible"                               # No conflicts detected
    CONFLICTING = "conflicting"                         # Conflicts with known constraints
    UNKNOWN = "unknown"                                 # Insufficient context to determine


class EvidenceLevel(str, Enum):
    """Confidence level for personal context evidence (G3.5)."""
    HIGH = "high"       # Explicit todo, explicit user statement, scheduled activity
    MEDIUM = "medium"   # Repeated recent routine with sufficient evidence
    LOW = "low"         # Inferred preference from isolated unrelated context


@dataclass
class PersonalConstraint:
    """A constraint on activity timing extracted from Bee context (G3.4)."""
    constraint_type: ConstraintType
    value: str | datetime                            # Time or window description
    source_type: str                                 # "bee_todo" | "bee_conversation" | "bee_summary"
    source_id: str | None = None                     # Bee ref id
    source_timestamp: datetime | None = None         # When the source was created
    confidence: EvidenceLevel = EvidenceLevel.HIGH
    raw_text: str | None = None                      # Sanitized original text (not persisted)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "constraint_type": self.constraint_type.value,
            "value": self.value.isoformat() if isinstance(self.value, datetime) else self.value,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "confidence": self.confidence.value,
        }


@dataclass
class PersonalPreference:
    """A preference (weaker than constraint) extracted from Bee context."""
    preference_type: PreferenceType
    value: str
    source_type: str
    source_id: str | None = None
    source_timestamp: datetime | None = None
    confidence: EvidenceLevel = EvidenceLevel.MEDIUM
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "preference_type": self.preference_type.value,
            "value": self.value,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "confidence": self.confidence.value,
        }


@dataclass
class ContextFreshness:
    """Tracks how stale personal context is (G3.12)."""
    source_type: str
    source_timestamp: datetime | None
    age_hours: float | None = None
    is_stale: bool = False
    staleness_reason: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "age_hours": self.age_hours,
            "is_stale": self.is_stale,
            "staleness_reason": self.staleness_reason,
        }


@dataclass
class PersonalFeasibility:
    """Evaluation of whether a candidate time window is personally feasible (G3.3)."""
    status: FeasibilityStatus
    candidate_time: datetime
    constraints: list[PersonalConstraint] = field(default_factory=list)
    conflicts: list[PersonalConstraint] = field(default_factory=list)
    preferences: list[PersonalPreference] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "candidate_time": self.candidate_time.isoformat(),
            "constraints": [c.to_dict() for c in self.constraints],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "preferences": [p.to_dict() for p in self.preferences],
            "evidence": self.evidence,
            "limitations": self.limitations,
        }


@dataclass
class PersonalContext:
    """Complete personal context extracted from Bee for environmental decision-making."""
    constraints: list[PersonalConstraint] = field(default_factory=list)
    preferences: list[PersonalPreference] = field(default_factory=list)
    freshness: list[ContextFreshness] = field(default_factory=list)
    has_sufficient_context: bool = False
    context_gap: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "constraints": [c.to_dict() for c in self.constraints],
            "preferences": [p.to_dict() for p in self.preferences],
            "freshness": [f.to_dict() for f in self.freshness],
            "has_sufficient_context": self.has_sufficient_context,
            "context_gap": self.context_gap,
        }


# Time expressions for constraint extraction
_TIME_PATTERNS = {
    "sleep": ["sleep", "bedtime", "turn in"],
    "dinner": ["dinner", "supper"],
    "lunch": ["lunch"],
    "breakfast": ["breakfast"],
    "work_end": ["finish work", "get off work", "end of work", "leave work", "off at"],
    "work_start": ["start work", "begin work", "get to work"],
}

# Activity keywords that might indicate constraints
_ACTIVITY_KEYWORDS = [
    "meeting", "appointment", "call", "class", "lesson", "session",
    "dinner", "lunch", "breakfast", "date", "party", "event",
]


def extract_constraints_from_todo(todo: dict, now: datetime) -> PersonalConstraint | None:
    """Extract a constraint from a Bee todo item (G3.4).
    
    Todos with specific times become FIXED_COMMITMENT constraints.
    Todos with alarm times become LATEST_ACTIVITY_END if they indicate sleep.
    """
    text = todo.get("text") or todo.get("title") or ""
    alarm_at = todo.get("alarm_at")
    todo_id = str(todo.get("id")) if todo.get("id") else None
    
    # Determine confidence based on whether this is explicitly scheduled
    confidence = EvidenceLevel.HIGH
    
    # Check for sleep-related todos -> latest_activity_end constraint
    text_lower = text.lower()
    if any(kw in text_lower for kw in _TIME_PATTERNS["sleep"]):
        if alarm_at:
            try:
                alarm_time = datetime.fromtimestamp(alarm_at / 1000)
                return PersonalConstraint(
                    constraint_type=ConstraintType.LATEST_ACTIVITY_END,
                    value=alarm_time,
                    source_type="bee_todo",
                    source_id=todo_id,
                    source_timestamp=datetime.fromtimestamp(alarm_at / 1000) if alarm_at else now,
                    confidence=confidence,
                    raw_text=text,  # Not persisted, used only for this extraction
                )
            except (TypeError, ValueError, OSError):
                pass
    
    # Check for explicit time in todo text
    # "Dinner at 7 PM" -> fixed commitment at 19:00
    import re
    time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?", text, re.IGNORECASE)
    if time_match:
        hour = int(time_match.group(1)) % 12
        minute = int(time_match.group(2) or 0)
        if time_match.group(3).lower() == "p":
            hour += 12
        
        # Use today's date
        commitment_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if commitment_time < now:
            commitment_time += timedelta(days=1)
        
        # Determine if this is a fixed commitment
        is_activity = any(kw in text_lower for kw in _ACTIVITY_KEYWORDS)
        if is_activity:
            return PersonalConstraint(
                constraint_type=ConstraintType.FIXED_COMMITMENT,
                value=commitment_time,
                source_type="bee_todo",
                source_id=todo_id,
                source_timestamp=now,
                confidence=confidence,
                raw_text=text,
            )
    
    return None


def extract_preferences_from_conversation(
    conversation: dict,
    now: datetime,
) -> list[PersonalPreference]:
    """Extract preferences from Bee conversation summaries (G3.4).
    
    Look for stated preferences like "I prefer running after work".
    These are weaker than constraints and have MEDIUM confidence.
    """
    preferences = []
    summary = conversation.get("summary") or conversation.get("short_summary") or ""
    conv_id = str(conversation.get("id")) if conversation.get("id") else None
    
    # Look for preference patterns
    # "I prefer X after Y" -> preferred_window
    import re
    pref_match = re.search(
        r"prefer \w+ (after|before|around) (\w+)",
        summary,
        re.IGNORECASE,
    )
    if pref_match:
        preferences.append(PersonalPreference(
            preference_type=PreferenceType.PREFERRED_ACTIVITY_WINDOW,
            value=f"{pref_match.group(1)} {pref_match.group(2)}",
            source_type="bee_conversation",
            source_id=conv_id,
            source_timestamp=datetime.fromtimestamp(conversation.get("start_time", 0) / 1000) if conversation.get("start_time") else now,
            confidence=EvidenceLevel.MEDIUM,
        ))
    
    return preferences


def evaluate_freshness(
    source_type: str,
    source_timestamp: datetime | None,
    now: datetime,
) -> ContextFreshness:
    """Evaluate how fresh personal context is (G3.12).
    
    Context from today: high relevance
    Context from weeks ago: lower relevance
    Old one-time todo: should not constrain today
    """
    age_hours = None
    is_stale = False
    staleness_reason = None
    
    if source_timestamp:
        age_hours = (now - source_timestamp).total_seconds() / 3600
        
        # Staleness thresholds
        if source_type == "bee_todo":
            # One-time todos older than 24h are stale
            if age_hours > 24:
                is_stale = True
                staleness_reason = "todo_older_than_24h"
        elif source_type == "bee_conversation":
            # Conversations older than 7 days are stale for preference extraction
            if age_hours > 168:  # 7 days
                is_stale = True
                staleness_reason = "conversation_older_than_7d"
        elif source_type == "bee_summary":
            # Daily summaries older than 3 days are stale
            if age_hours > 72:
                is_stale = True
                staleness_reason = "summary_older_than_3d"
    
    return ContextFreshness(
        source_type=source_type,
        source_timestamp=source_timestamp,
        age_hours=age_hours,
        is_stale=is_stale,
        staleness_reason=staleness_reason,
    )


def extract_personal_context(
    today_context: dict | None,
    now: datetime | None = None,
) -> PersonalContext:
    """Extract personal constraints and preferences from Bee context (G3.2).
    
    Data Minimization (G3.10):
    - Only extract constraints/preferences relevant to timing decisions
    - Do NOT retrieve entire conversations, unrelated todos, or raw summaries
    - Store only the normalized representation, not raw Bee content
    
    Args:
        today_context: Bee today context dict (from BeeTodayContext.model_dump())
        now: Current time for freshness evaluation
    
    Returns:
        PersonalContext with constraints, preferences, and freshness metadata
    """
    now = now or datetime.now()
    constraints: list[PersonalConstraint] = []
    preferences: list[PersonalPreference] = []
    freshness_records: list[ContextFreshness] = []
    
    if not today_context:
        return PersonalContext(
            constraints=[],
            preferences=[],
            freshness=[],
            has_sufficient_context=False,
            context_gap="no_bee_context_available",
        )
    
    # Extract from active todos (HIGH confidence)
    active_todos = today_context.get("activeTodos", [])
    for todo in active_todos:
        constraint = extract_constraints_from_todo(todo, now)
        if constraint:
            constraints.append(constraint)
            # Track freshness
            freshness_records.append(evaluate_freshness(
                "bee_todo",
                constraint.source_timestamp,
                now,
            ))
    
    # Extract from recent conversations (MEDIUM confidence for preferences)
    conversations = today_context.get("recentConversations", [])
    for conv in conversations[:3]:  # Only check recent 3 conversations (minimization)
        conv_prefs = extract_preferences_from_conversation(conv, now)
        preferences.extend(conv_prefs)
        for pref in conv_prefs:
            freshness_records.append(evaluate_freshness(
                "bee_conversation",
                pref.source_timestamp,
                now,
            ))
    
    # Check for daily summary (might contain routine info)
    daily_summary = today_context.get("dailySummary")
    if daily_summary and isinstance(daily_summary, str):
        # Only extract if it mentions routines/schedule
        # This is intentionally minimal - we don't persist the raw summary
        freshness_records.append(evaluate_freshness(
            "bee_summary",
            now,  # Daily summary is from today
            now,
        ))
    
    # Filter out stale constraints (G3.12)
    # Stale preferences can remain but with lower weight
    fresh_constraints = [
        c for c in constraints
        if not any(
            f.is_stale and f.source_type == c.source_type
            for f in freshness_records
        )
    ]
    
    # Determine if we have sufficient context
    has_sufficient = len(fresh_constraints) > 0 or len(preferences) > 0
    context_gap = None
    if not has_sufficient:
        context_gap = "no_relevant_constraints_or_preferences_found"
    
    return PersonalContext(
        constraints=fresh_constraints,
        preferences=preferences,
        freshness=freshness_records,
        has_sufficient_context=has_sufficient,
        context_gap=context_gap,
    )


def evaluate_candidate_feasibility(
    candidate_time: datetime,
    personal_context: PersonalContext,
    activity: str | None = None,
) -> PersonalFeasibility:
    """Evaluate whether a candidate time window is personally feasible (G3.3, G3.6).
    
    This is the core G3 decision: does the environmentally better window conflict with
    the user's known constraints?
    
    Key principles:
    - Unknown feasibility is a valid result (do not assume feasibility)
    - Conflicts are detected against constraints, not preferences
    - Preferences inform but do not block recommendations
    
    Args:
        candidate_time: The candidate alternative time
        personal_context: Extracted personal constraints and preferences
        activity: The planned activity (for context-aware evaluation)
    
    Returns:
        PersonalFeasibility with status, conflicts, and evidence
    """
    conflicts: list[PersonalConstraint] = []
    evidence: list[str] = []
    limitations: list[str] = []
    
    # Check each constraint against the candidate time
    for constraint in personal_context.constraints:
        if constraint.constraint_type == ConstraintType.FIXED_COMMITMENT:
            # Fixed commitment: check if candidate overlaps
            if isinstance(constraint.value, datetime):
                # 1-hour window around the commitment
                commitment_start = constraint.value - timedelta(hours=0.5)
                commitment_end = constraint.value + timedelta(hours=1.5)
                if commitment_start <= candidate_time <= commitment_end:
                    conflicts.append(constraint)
                    evidence.append(
                        f"Conflicts with commitment at {constraint.value.strftime('%H:%M')}"
                    )
        
        elif constraint.constraint_type == ConstraintType.LATEST_ACTIVITY_END:
            # Latest end: check if candidate is too late
            if isinstance(constraint.value, datetime):
                # Activity typically takes 1 hour, so latest start is 1h before end
                latest_start = constraint.value - timedelta(hours=1)
                if candidate_time >= latest_start:
                    conflicts.append(constraint)
                    evidence.append(
                        f"Too close to {constraint.value.strftime('%H:%M')} constraint"
                    )
        
        elif constraint.constraint_type == ConstraintType.UNAVAILABLE_BEFORE:
            # Cannot start before time X
            if isinstance(constraint.value, datetime):
                if candidate_time < constraint.value:
                    conflicts.append(constraint)
                    evidence.append(
                        f"Starts before available time {constraint.value.strftime('%H:%M')}"
                    )
        
        elif constraint.constraint_type == ConstraintType.UNAVAILABLE_AFTER:
            # Cannot start after time X
            if isinstance(constraint.value, datetime):
                if candidate_time > constraint.value:
                    conflicts.append(constraint)
                    evidence.append(
                        f"Starts after available time {constraint.value.strftime('%H:%M')}"
                    )
    
    # Determine feasibility status
    if conflicts:
        status = FeasibilityStatus.CONFLICTING
    elif not personal_context.has_sufficient_context:
        status = FeasibilityStatus.UNKNOWN
        limitations.append("Insufficient personal context to determine feasibility")
    else:
        status = FeasibilityStatus.FEASIBLE
        evidence.append("No conflicting personal commitments detected")
    
    return PersonalFeasibility(
        status=status,
        candidate_time=candidate_time,
        constraints=personal_context.constraints,
        conflicts=conflicts,
        preferences=personal_context.preferences,
        evidence=evidence,
        limitations=limitations,
    )
