"""G3: Recommendation State Machine — explicit decision states for personal environmental recommendations.

This module implements the G3.8 state machine that determines whether an environmentally
better window should become a personal recommendation.

Key principles:
- Environmental improvement alone is NOT sufficient for personal recommendation
- Personal feasibility must be explicitly evaluated
- Unknown feasibility means no recommendation, not assumed feasibility
- States are machine-readable; natural language derives from states

State Machine:

    KEEP_PLANNED_TIME
    → No better environmental window found

    BETTER_WINDOW_AVAILABLE
    → Environmentally better AND personally feasible

    BETTER_WINDOW_BUT_PERSONAL_FEASIBILITY_UNKNOWN
    → Environmentally better but insufficient personal context

    BETTER_WINDOW_CONFLICTS_WITH_CONTEXT
    → Environmentally better but conflicts with user constraints

    NO_MATERIALLY_BETTER_WINDOW
    → Better window exists but doesn't meet material improvement threshold

    INSUFFICIENT_ENVIRONMENTAL_DATA
    → Cannot determine environmental suitability

    INSUFFICIENT_PERSONAL_CONTEXT
    → Cannot determine personal feasibility (different from "no conflicts found")

    ACTIVITY_CONTEXT_UNCERTAIN
    → The original activity/intent is unclear

"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass

from app.agent.personal_context import (
    FeasibilityStatus,
    PersonalFeasibility,
    PersonalContext,
)


class DecisionState(str, Enum):
    """Machine-readable decision states for recommendations (G3.8)."""
    
    # No environmental improvement found
    KEEP_PLANNED_TIME = "keep_planned_time"
    NO_MATERIALLY_BETTER_WINDOW = "no_materially_better_window"
    
    # Environmental improvement found, feasibility varies
    BETTER_WINDOW_AVAILABLE = "better_window_available"                       # Feasible
    BETTER_WINDOW_BUT_PERSONAL_FEASIBILITY_UNKNOWN = "better_window_feasibility_unknown"
    BETTER_WINDOW_CONFLICTS_WITH_CONTEXT = "better_window_conflicts_with_context"
    
    # Insufficient data
    INSUFFICIENT_ENVIRONMENTAL_DATA = "insufficient_environmental_data"
    INSUFFICIENT_PERSONAL_CONTEXT = "insufficient_personal_context"
    
    # Intent unclear
    ACTIVITY_CONTEXT_UNCERTAIN = "activity_context_uncertain"


@dataclass
class DecisionResult:
    """Complete decision result from the state machine."""
    state: DecisionState
    recommended_time: str | None  # ISO format or None
    reason_codes: list[str]
    natural_language: str
    personal_feasibility: PersonalFeasibility | None
    limitations: list[str]
    
    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "recommended_time": self.recommended_time,
            "reason_codes": self.reason_codes,
            "natural_language": self.natural_language,
            "personal_feasibility": self.personal_feasibility.to_dict() if self.personal_feasibility else None,
            "limitations": self.limitations,
        }


def determine_decision_state(
    # Environmental assessment
    has_environmentally_better_window: bool,
    environmentally_better_time: str | None,
    # Personal feasibility
    personal_feasibility: PersonalFeasibility | None,
    personal_context: PersonalContext | None,
    # Intent context
    activity_is_certain: bool,
    # Additional context
    has_environmental_data: bool = True,
    material_improvement_met: bool = True,
) -> DecisionResult:
    """Run the state machine to determine the final recommendation (G3.8).
    
    The state machine enforces:
    1. Environmental improvement is necessary but not sufficient
    2. Personal feasibility must be FEASIBLE for recommendation
    3. UNKNOWN feasibility -> no recommendation (not assumed feasibility)
    4. CONFLICTING -> definitely no recommendation
    
    Args:
        has_environmentally_better_window: Whether G2 found a better window
        environmentally_better_time: The better window time (ISO or None)
        personal_feasibility: Feasibility evaluation from personal_context module
        personal_context: Extracted personal constraints/preferences
        activity_is_certain: Whether the user's intent is clear
        has_environmental_data: Whether we have environmental observations
        material_improvement_met: Whether the improvement meets threshold
    
    Returns:
        DecisionResult with state, recommendation, and reasoning
    """
    reason_codes: list[str] = []
    limitations: list[str] = []
    
    # Step 1: Check if we have sufficient environmental data
    if not has_environmental_data:
        return DecisionResult(
            state=DecisionState.INSUFFICIENT_ENVIRONMENTAL_DATA,
            recommended_time=None,
            reason_codes=["no_environmental_observations"],
            natural_language="Unable to assess environmental conditions due to missing data.",
            personal_feasibility=None,
            limitations=["Environmental data unavailable"],
        )
    
    # Step 2: Check if activity context is clear
    if not activity_is_certain:
        return DecisionResult(
            state=DecisionState.ACTIVITY_CONTEXT_UNCERTAIN,
            recommended_time=None,
            reason_codes=["activity_not_determined"],
            natural_language="I couldn't determine what activity you're planning. Please specify the activity for personalized recommendations.",
            personal_feasibility=None,
            limitations=["Activity context unclear"],
        )
    
    # Step 3: Check if there's an environmentally better window
    if not has_environmentally_better_window:
        return DecisionResult(
            state=DecisionState.KEEP_PLANNED_TIME,
            recommended_time=None,
            reason_codes=["no_better_environmental_window"],
            natural_language="No clearly better environmental window was found within the search range. Your planned time looks reasonable from an environmental perspective.",
            personal_feasibility=None,
            limitations=[],
        )
    
    # Step 4: Check if material improvement threshold is met
    if not material_improvement_met:
        return DecisionResult(
            state=DecisionState.NO_MATERIALLY_BETTER_WINDOW,
            recommended_time=None,
            reason_codes=["improvement_below_threshold"],
            natural_language="A slightly better environmental window exists, but the improvement is not significant enough to warrant a recommendation to reschedule.",
            personal_feasibility=None,
            limitations=["Improvement below 15% threshold"],
        )
    
    # Step 5: Evaluate personal feasibility
    # This is the core G3 decision point
    if personal_feasibility is None or personal_context is None:
        # No personal context was provided
        return DecisionResult(
            state=DecisionState.BETTER_WINDOW_BUT_PERSONAL_FEASIBILITY_UNKNOWN,
            recommended_time=None,
            reason_codes=["environmentally_better", "no_personal_context"],
            natural_language=f"Environmental conditions appear more favorable around {environmentally_better_time}. I don't have enough personal context to determine whether that time fits your schedule.",
            personal_feasibility=None,
            limitations=["Personal context not provided"],
        )
    
    # Step 6: Check feasibility status
    if personal_feasibility.status == FeasibilityStatus.CONFLICTING:
        # Conflicts detected
        conflict_desc = "; ".join(personal_feasibility.evidence) if personal_feasibility.evidence else "conflicting commitments"
        return DecisionResult(
            state=DecisionState.BETTER_WINDOW_CONFLICTS_WITH_CONTEXT,
            recommended_time=None,
            reason_codes=["environmentally_better", "personal_conflict"] + [f"conflict:{c.constraint_type.value}" for c in personal_feasibility.conflicts],
            natural_language=f"Environmental conditions improve around {environmentally_better_time}, but your Bee context indicates {conflict_desc}.",
            personal_feasibility=personal_feasibility,
            limitations=personal_feasibility.limitations,
        )
    
    if personal_feasibility.status == FeasibilityStatus.UNKNOWN:
        # Insufficient personal context to determine feasibility
        return DecisionResult(
            state=DecisionState.BETTER_WINDOW_BUT_PERSONAL_FEASIBILITY_UNKNOWN,
            recommended_time=None,
            reason_codes=["environmentally_better", "feasibility_unknown"],
            natural_language=f"Environmental conditions appear more favorable around {environmentally_better_time}. I don't have enough personal context to determine whether that time works for you.",
            personal_feasibility=personal_feasibility,
            limitations=personal_feasibility.limitations,
        )
    
    # Step 7: Feasible - can recommend
    if personal_feasibility.status == FeasibilityStatus.FEASIBLE:
        evidence_str = " ".join(personal_feasibility.evidence) if personal_feasibility.evidence else "no conflicts detected"
        return DecisionResult(
            state=DecisionState.BETTER_WINDOW_AVAILABLE,
            recommended_time=environmentally_better_time,
            reason_codes=["environmentally_better", "personally_feasible"] + personal_feasibility.evidence,
            natural_language=f"Conditions appear better around {environmentally_better_time}, and {evidence_str}. Consider rescheduling if convenient.",
            personal_feasibility=personal_feasibility,
            limitations=[],
        )
    
    # Fallback (should not reach here)
    return DecisionResult(
        state=DecisionState.INSUFFICIENT_PERSONAL_CONTEXT,
        recommended_time=None,
        reason_codes=["unexpected_feasibility_status"],
        natural_language="Unable to determine personal feasibility for the recommended time.",
        personal_feasibility=personal_feasibility,
        limitations=["Unexpected state"],
    )


def format_decision_for_user(decision: DecisionResult) -> str:
    """Format the decision for user-facing output (G3.7 cases).
    
    Maps the decision state to one of the four G3.7 output cases:
    - Case A: Better and feasible
    - Case B: Better environmentally, feasibility unknown
    - Case C: Better environmentally, but conflicts
    - Case D: No environmental improvement
    """
    if decision.state == DecisionState.BETTER_WINDOW_AVAILABLE:
        return decision.natural_language
    elif decision.state == DecisionState.BETTER_WINDOW_BUT_PERSONAL_FEASIBILITY_UNKNOWN:
        return decision.natural_language
    elif decision.state == DecisionState.BETTER_WINDOW_CONFLICTS_WITH_CONTEXT:
        return decision.natural_language
    elif decision.state in (DecisionState.KEEP_PLANNED_TIME, DecisionState.NO_MATERIALLY_BETTER_WINDOW):
        return decision.natural_language
    else:
        return decision.natural_language
