"""G3: Personal Context Intelligence tests.

Tests cover:
- Personal constraint extraction
- Personal preference extraction
- Feasibility evaluation
- Decision state machine
- Context freshness
- Conflict resolution
- Privacy minimization
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.agent.personal_context import (
    ConstraintType,
    PreferenceType,
    FeasibilityStatus,
    EvidenceLevel,
    PersonalConstraint,
    PersonalPreference,
    PersonalFeasibility,
    PersonalContext,
    ContextFreshness,
    extract_constraints_from_todo,
    extract_preferences_from_conversation,
    evaluate_freshness,
    extract_personal_context,
    evaluate_candidate_feasibility,
)
from app.agent.decision_state import (
    DecisionState,
    DecisionResult,
    determine_decision_state,
    format_decision_for_user,
)


# ============================================================================
# Constraint Extraction Tests (G3.4)
# ============================================================================

def test_extract_fixed_commitment_from_todo():
    """A todo with 'Dinner at 7 PM' becomes a FIXED_COMMITMENT constraint."""
    now = datetime.now().replace(hour=10, minute=0)
    todo = {
        "id": 123,
        "text": "Dinner with family at 7 PM",
    }
    
    constraint = extract_constraints_from_todo(todo, now)
    
    assert constraint is not None
    assert constraint.constraint_type == ConstraintType.FIXED_COMMITMENT
    assert constraint.source_type == "bee_todo"
    assert constraint.source_id == "123"
    assert constraint.confidence == EvidenceLevel.HIGH
    # Should be 19:00 today
    assert constraint.value.hour == 19


def test_extract_latest_activity_end_from_sleep_todo():
    """A todo mentioning sleep becomes a LATEST_ACTIVITY_END constraint."""
    now = datetime.now().replace(hour=10, minute=0)
    todo = {
        "id": 456,
        "text": "Go to sleep by 11 PM",
        "alarm_at": int((now.replace(hour=23, minute=0)).timestamp() * 1000),
    }
    
    constraint = extract_constraints_from_todo(todo, now)
    
    assert constraint is not None
    assert constraint.constraint_type == ConstraintType.LATEST_ACTIVITY_END
    assert constraint.confidence == EvidenceLevel.HIGH


def test_no_constraint_from_generic_todo():
    """A generic todo without timing info returns None."""
    now = datetime.now()
    todo = {
        "id": 789,
        "text": "Buy groceries",
    }
    
    constraint = extract_constraints_from_todo(todo, now)
    
    assert constraint is None


# ============================================================================
# Preference Extraction Tests (G3.4)
# ============================================================================

def test_extract_preference_from_conversation():
    """'I prefer running after work' becomes a preference."""
    now = datetime.now()
    conversation = {
        "id": 999,
        "summary": "I prefer running after work",
        "start_time": int(now.timestamp() * 1000),
    }
    
    preferences = extract_preferences_from_conversation(conversation, now)
    
    assert len(preferences) == 1
    assert preferences[0].preference_type == PreferenceType.PREFERRED_ACTIVITY_WINDOW
    assert preferences[0].confidence == EvidenceLevel.MEDIUM


def test_no_preference_from_irrelevant_conversation():
    """A conversation without preference patterns returns empty list."""
    now = datetime.now()
    conversation = {
        "id": 888,
        "summary": "The weather looks nice today",
        "start_time": int(now.timestamp() * 1000),
    }
    
    preferences = extract_preferences_from_conversation(conversation, now)
    
    assert len(preferences) == 0


# ============================================================================
# Context Freshness Tests (G3.12)
# ============================================================================

def test_freshness_of_today_context():
    """Context from today is not stale."""
    now = datetime.now()
    freshness = evaluate_freshness("bee_todo", now - timedelta(hours=2), now)
    
    assert freshness.is_stale is False
    assert freshness.age_hours == 2.0


def test_staleness_of_old_todo():
    """A todo older than 24h is stale."""
    now = datetime.now()
    old_time = now - timedelta(hours=30)
    freshness = evaluate_freshness("bee_todo", old_time, now)
    
    assert freshness.is_stale is True
    assert freshness.staleness_reason == "todo_older_than_24h"


def test_staleness_of_old_conversation():
    """A conversation older than 7 days is stale for preference extraction."""
    now = datetime.now()
    old_time = now - timedelta(days=8)
    freshness = evaluate_freshness("bee_conversation", old_time, now)
    
    assert freshness.is_stale is True
    assert freshness.staleness_reason == "conversation_older_than_7d"


# ============================================================================
# Feasibility Evaluation Tests (G3.3, G3.6)
# ============================================================================

def test_feasible_when_no_conflicts():
    """Candidate time with no conflicting constraints is FEASIBLE."""
    now = datetime.now().replace(hour=10, minute=0)
    candidate_time = now.replace(hour=17, minute=0)
    
    personal_context = PersonalContext(
        constraints=[],
        preferences=[],
        has_sufficient_context=True,
    )
    
    feasibility = evaluate_candidate_feasibility(candidate_time, personal_context, "jogging")
    
    assert feasibility.status == FeasibilityStatus.FEASIBLE
    assert len(feasibility.conflicts) == 0
    assert "No conflicting personal commitments detected" in feasibility.evidence


def test_conflicting_when_fixed_commitment():
    """Candidate time overlapping with a fixed commitment is CONFLICTING."""
    now = datetime.now().replace(hour=10, minute=0)
    candidate_time = now.replace(hour=19, minute=0)  # 7 PM
    
    # User has dinner at 7 PM
    dinner_constraint = PersonalConstraint(
        constraint_type=ConstraintType.FIXED_COMMITMENT,
        value=now.replace(hour=19, minute=0),
        source_type="bee_todo",
        source_id="123",
        confidence=EvidenceLevel.HIGH,
    )
    
    personal_context = PersonalContext(
        constraints=[dinner_constraint],
        has_sufficient_context=True,
    )
    
    feasibility = evaluate_candidate_feasibility(candidate_time, personal_context, "jogging")
    
    assert feasibility.status == FeasibilityStatus.CONFLICTING
    assert len(feasibility.conflicts) == 1
    assert "Conflicts with commitment" in feasibility.evidence[0]


def test_unknown_feasibility_when_no_context():
    """When personal context is insufficient, feasibility is UNKNOWN."""
    now = datetime.now().replace(hour=10, minute=0)
    candidate_time = now.replace(hour=19, minute=0)
    
    personal_context = PersonalContext(
        constraints=[],
        preferences=[],
        has_sufficient_context=False,
        context_gap="no_relevant_constraints_or_preferences_found",
    )
    
    feasibility = evaluate_candidate_feasibility(candidate_time, personal_context, "jogging")
    
    assert feasibility.status == FeasibilityStatus.UNKNOWN
    assert "Insufficient personal context" in feasibility.limitations[0]


def test_conflicting_when_too_late():
    """Candidate time after latest_activity_end is CONFLICTING."""
    now = datetime.now().replace(hour=10, minute=0)
    candidate_time = now.replace(hour=22, minute=30)  # 10:30 PM
    
    # User needs to sleep by 11 PM
    sleep_constraint = PersonalConstraint(
        constraint_type=ConstraintType.LATEST_ACTIVITY_END,
        value=now.replace(hour=23, minute=0),
        source_type="bee_todo",
        confidence=EvidenceLevel.HIGH,
    )
    
    personal_context = PersonalContext(
        constraints=[sleep_constraint],
        has_sufficient_context=True,
    )
    
    feasibility = evaluate_candidate_feasibility(candidate_time, personal_context, "jogging")
    
    assert feasibility.status == FeasibilityStatus.CONFLICTING


# ============================================================================
# Decision State Machine Tests (G3.8)
# ============================================================================

def test_state_keep_planned_time():
    """No better window found -> KEEP_PLANNED_TIME."""
    result = determine_decision_state(
        has_environmentally_better_window=False,
        environmentally_better_time=None,
        personal_feasibility=None,
        personal_context=None,
        activity_is_certain=True,
    )
    
    assert result.state == DecisionState.KEEP_PLANNED_TIME
    assert result.recommended_time is None


def test_state_better_window_available():
    """Environmentally better AND feasible -> BETTER_WINDOW_AVAILABLE."""
    now = datetime.now()
    feasibility = PersonalFeasibility(
        status=FeasibilityStatus.FEASIBLE,
        candidate_time=now.replace(hour=19, minute=0),
        evidence=["No conflicting personal commitments detected"],
    )
    personal_context = PersonalContext(
        constraints=[],
        has_sufficient_context=True,
    )
    
    result = determine_decision_state(
        has_environmentally_better_window=True,
        environmentally_better_time="19:00",
        personal_feasibility=feasibility,
        personal_context=personal_context,
        activity_is_certain=True,
    )
    
    assert result.state == DecisionState.BETTER_WINDOW_AVAILABLE
    assert result.recommended_time == "19:00"
    assert "Conditions appear better" in result.natural_language


def test_state_feasibility_unknown():
    """Environmentally better but unknown feasibility -> BETTER_WINDOW_BUT_PERSONAL_FEASIBILITY_UNKNOWN."""
    now = datetime.now()
    feasibility = PersonalFeasibility(
        status=FeasibilityStatus.UNKNOWN,
        candidate_time=now.replace(hour=19, minute=0),
        limitations=["Insufficient personal context"],
    )
    personal_context = PersonalContext(
        constraints=[],
        has_sufficient_context=False,
    )
    
    result = determine_decision_state(
        has_environmentally_better_window=True,
        environmentally_better_time="19:00",
        personal_feasibility=feasibility,
        personal_context=personal_context,
        activity_is_certain=True,
    )
    
    assert result.state == DecisionState.BETTER_WINDOW_BUT_PERSONAL_FEASIBILITY_UNKNOWN
    assert result.recommended_time is None
    assert "I don't have enough personal context" in result.natural_language


def test_state_conflicts_with_context():
    """Environmentally better but conflicts -> BETTER_WINDOW_CONFLICTS_WITH_CONTEXT."""
    now = datetime.now()
    constraint = PersonalConstraint(
        constraint_type=ConstraintType.FIXED_COMMITMENT,
        value=now.replace(hour=19, minute=0),
        source_type="bee_todo",
        confidence=EvidenceLevel.HIGH,
    )
    feasibility = PersonalFeasibility(
        status=FeasibilityStatus.CONFLICTING,
        candidate_time=now.replace(hour=19, minute=0),
        conflicts=[constraint],
        evidence=["Conflicts with commitment at 19:00"],
    )
    personal_context = PersonalContext(
        constraints=[constraint],
        has_sufficient_context=True,
    )
    
    result = determine_decision_state(
        has_environmentally_better_window=True,
        environmentally_better_time="19:00",
        personal_feasibility=feasibility,
        personal_context=personal_context,
        activity_is_certain=True,
    )
    
    assert result.state == DecisionState.BETTER_WINDOW_CONFLICTS_WITH_CONTEXT
    assert result.recommended_time is None
    assert "your Bee context indicates" in result.natural_language


def test_state_activity_uncertain():
    """Activity not determined -> ACTIVITY_CONTEXT_UNCERTAIN."""
    result = determine_decision_state(
        has_environmentally_better_window=True,
        environmentally_better_time="19:00",
        personal_feasibility=None,
        personal_context=None,
        activity_is_certain=False,
    )
    
    assert result.state == DecisionState.ACTIVITY_CONTEXT_UNCERTAIN


# ============================================================================
# Full Context Extraction Tests (G3.2)
# ============================================================================

def test_extract_personal_context_from_bee():
    """Extract constraints and preferences from Bee today context."""
    now = datetime.now().replace(hour=10, minute=0)
    
    bee_context = {
        "activeTodos": [
            {
                "id": 1,
                "text": "Dinner at 7 PM",
            },
            {
                "id": 2,
                "text": "Go to sleep by 11 PM",
                "alarm_at": int(now.replace(hour=23, minute=0).timestamp() * 1000),
            },
        ],
        "recentConversations": [
            {
                "id": 100,
                "summary": "I prefer running after work",
                "start_time": int(now.timestamp() * 1000),
            },
        ],
    }
    
    personal_context = extract_personal_context(bee_context, now)
    
    # Should extract dinner as fixed commitment
    assert len(personal_context.constraints) >= 1
    assert personal_context.has_sufficient_context is True
    
    # Should extract preference
    assert len(personal_context.preferences) >= 1


def test_no_bee_context():
    """No Bee context returns empty context with gap flag."""
    personal_context = extract_personal_context(None, datetime.now())
    
    assert personal_context.has_sufficient_context is False
    assert personal_context.context_gap == "no_bee_context_available"


# ============================================================================
# Conflict Resolution Tests (G3.13)
# ============================================================================

def test_explicit_commitment_overrides_preference():
    """An explicit commitment today takes precedence over a general preference."""
    now = datetime.now().replace(hour=10, minute=0)
    
    # User prefers running after work (preference)
    preference = PersonalPreference(
        preference_type=PreferenceType.PREFERRED_ACTIVITY_WINDOW,
        value="after work",
        source_type="bee_conversation",
        confidence=EvidenceLevel.MEDIUM,
    )
    
    # But has a dinner commitment at 7 PM today (constraint)
    constraint = PersonalConstraint(
        constraint_type=ConstraintType.FIXED_COMMITMENT,
        value=now.replace(hour=19, minute=0),
        source_type="bee_todo",
        confidence=EvidenceLevel.HIGH,
    )
    
    personal_context = PersonalContext(
        constraints=[constraint],
        preferences=[preference],
        has_sufficient_context=True,
    )
    
    # Candidate at 7 PM should conflict despite preference
    feasibility = evaluate_candidate_feasibility(
        now.replace(hour=19, minute=0),
        personal_context,
        "jogging",
    )
    
    assert feasibility.status == FeasibilityStatus.CONFLICTING


# ============================================================================
# Privacy Minimization Tests (G3.10)
# ============================================================================

def test_no_raw_text_in_constraint_dict():
    """PersonalConstraint.to_dict() does not expose raw_text."""
    constraint = PersonalConstraint(
        constraint_type=ConstraintType.FIXED_COMMITMENT,
        value=datetime.now().replace(hour=19, minute=0),
        source_type="bee_todo",
        source_id="123",
        confidence=EvidenceLevel.HIGH,
        raw_text="Dinner with family at 7 PM",  # This should NOT be in to_dict()
    )
    
    d = constraint.to_dict()
    
    assert "raw_text" not in d
    assert d["constraint_type"] == "fixed_commitment"
    assert d["source_type"] == "bee_todo"


def test_minimal_extraction_from_conversations():
    """Only the first 3 conversations are checked (minimization)."""
    now = datetime.now()
    
    bee_context = {
        "activeTodos": [],
        "recentConversations": [
            {"id": i, "summary": f"Conversation {i}", "start_time": int(now.timestamp() * 1000)}
            for i in range(10)
        ],
    }
    
    personal_context = extract_personal_context(bee_context, now)
    
    # Should only process first 3 conversations
    # No preferences should be extracted (no "prefer" keyword in summaries)
    assert len(personal_context.preferences) == 0
    assert len(personal_context.freshness) <= 3


# ============================================================================
# Integration: G3 Decision Output Format Tests
# ============================================================================

def test_decision_result_to_dict():
    """DecisionResult serializes correctly."""
    now = datetime.now()
    feasibility = PersonalFeasibility(
        status=FeasibilityStatus.FEASIBLE,
        candidate_time=now.replace(hour=19, minute=0),
        evidence=["No conflicts"],
    )
    
    result = DecisionResult(
        state=DecisionState.BETTER_WINDOW_AVAILABLE,
        recommended_time="19:00",
        reason_codes=["environmentally_better", "personally_feasible"],
        natural_language="Conditions appear better around 19:00.",
        personal_feasibility=feasibility,
        limitations=[],
    )
    
    d = result.to_dict()
    
    assert d["state"] == "better_window_available"
    assert d["recommended_time"] == "19:00"
    assert "personally_feasible" in d["reason_codes"]
    assert d["personal_feasibility"]["status"] == "feasible"
