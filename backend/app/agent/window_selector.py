"""G2.3/G2.5: Time-window comparison and alternative-time recommendation.

Evaluates environmental conditions across a configurable time window around
the planned activity, and determines whether a materially better window exists.

Key principles:
- Never assume later is always better
- Evaluate based on activity-specific importance weights
- Return "no better window found" when appropriate
- All decisions are reconstructable from structured evidence
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from app.agent.activity_policy import (
    ActivityType,
    MetricImportance,
    evaluate_observation_for_activity,
    get_activity_policy,
    get_important_metrics,
)
from app.environmental.base import Observation


@dataclass
class WindowScore:
    """Score for a single time window."""
    time: datetime
    score: float              # 0-1, lower is better
    severity: str             # "info" | "caution" | "warning"
    metrics: dict[str, Observation]
    metric_scores: dict[str, tuple[str, float]]  # metric -> (severity, score)
    data_kind: str            # "observed" | "forecast" | "mixed"
    missing_metrics: list[str]


@dataclass
class AlternativeWindow:
    """A candidate alternative time window."""
    time: datetime
    score: float
    severity: str
    improvement_vs_planned: float  # Negative = better
    better_metrics: list[str]      # Metrics that improved
    worse_metrics: list[str]       # Metrics that got worse
    conditions: dict[str, Observation]


@dataclass
class WindowComparison:
    """Complete comparison across the time window."""
    planned_time: datetime
    planned_score: WindowScore
    alternatives: list[AlternativeWindow]
    recommended_time: datetime | None
    recommendation: str | None
    reason_codes: list[str]
    limitations: list[str]


# Weights for metric importance in scoring
_IMPORTANCE_WEIGHTS = {
    MetricImportance.HIGH: 3.0,
    MetricImportance.MEDIUM: 2.0,
    MetricImportance.LOW: 1.0,
}

# Minimum improvement threshold to recommend an alternative (avoid trivial switches)
_MIN_IMPROVEMENT_THRESHOLD = 0.15  # 15% score improvement


def score_window(
    observations: list[Observation],
    time: datetime,
    activity: str | None,
    important_metrics: list[str],
) -> WindowScore:
    """Score a single time window based on activity-specific importance.
    
    Lower score = better conditions.
    """
    by_metric = {o.metric: o for o in observations}
    metric_scores: dict[str, tuple[str, float]] = {}
    total_weight = 0.0
    weighted_score = 0.0
    severity_rank = {"info": 0, "caution": 1, "warning": 2}
    worst_severity = "info"
    
    policy = get_activity_policy(activity)
    
    for metric in important_metrics:
        obs = by_metric.get(metric)
        if obs is None:
            continue
        
        severity, score = evaluate_observation_for_activity(obs, activity)
        if severity is None:
            continue
        
        metric_scores[metric] = (severity, score)
        
        # Get importance weight
        weight = 1.0
        if policy and metric in policy.metrics:
            weight = _IMPORTANCE_WEIGHTS.get(policy.metrics[metric].importance, 1.0)
        
        weighted_score += score * weight
        total_weight += weight
        
        # Track worst severity
        if severity_rank.get(severity, 0) > severity_rank.get(worst_severity, 0):
            worst_severity = severity
    
    # Normalize score to 0-1
    final_score = weighted_score / total_weight if total_weight > 0 else 0.0
    
    # Determine data kind
    kinds = {o.kind for o in observations}
    if len(kinds) == 1:
        data_kind = kinds.pop()
    else:
        data_kind = "mixed"
    
    # Check for missing important metrics
    missing = [m for m in important_metrics if m not in by_metric]
    
    return WindowScore(
        time=time,
        score=final_score,
        severity=worst_severity,
        metrics=by_metric,
        metric_scores=metric_scores,
        data_kind=data_kind,
        missing_metrics=missing,
    )


def find_alternative_window(
    planned_time: datetime,
    observe_func: Callable,  # (lat, lon, when) -> (list[Observation], errors)
    lat: float,
    lon: float,
    activity: str | None = None,
    window_hours: int = 3,   # Hours before and after planned time
    now: datetime | None = None,
) -> WindowComparison:
    """Find the best alternative time window around the planned activity.
    
    Args:
        planned_time: The originally planned activity time
        observe_func: Function to get observations for a time
        lat, lon: Location coordinates
        activity: Activity type (for policy-based scoring)
        window_hours: Hours to search before and after planned time
        now: Current time (for testing)
    
    Returns:
        WindowComparison with planned score, alternatives, and recommendation
    """
    now = now or datetime.now()
    important_metrics = get_important_metrics(activity)
    
    # Score the planned time
    planned_obs, planned_errors = observe_func(lat, lon, when=planned_time)
    planned_score = score_window(planned_obs, planned_time, activity, important_metrics)
    
    # Build list of candidate times (hourly intervals)
    candidates: list[datetime] = []
    for h in range(-window_hours, window_hours + 1):
        if h == 0:
            continue  # Skip planned time itself
        
        cand_time = planned_time + timedelta(hours=h)
        
        # Skip times in the past
        if cand_time < now:
            continue
        
        # Skip times too far in the future (forecast reliability decreases)
        hours_ahead = (cand_time - now).total_seconds() / 3600
        if hours_ahead > 48:
            continue
        
        candidates.append(cand_time)
    
    # Score each candidate
    alternatives: list[AlternativeWindow] = []
    for cand_time in candidates:
        cand_obs, _ = observe_func(lat, lon, when=cand_time)
        cand_score = score_window(cand_obs, cand_time, activity, important_metrics)
        
        # Calculate improvement
        improvement = cand_score.score - planned_score.score  # Negative = better
        
        # Only consider as alternative if meaningfully better
        if improvement >= -_MIN_IMPROVEMENT_THRESHOLD:
            continue
        
        # Identify which metrics improved/worsened
        better_metrics: list[str] = []
        worse_metrics: list[str] = []
        
        for metric in important_metrics:
            planned_ms = planned_score.metric_scores.get(metric)
            cand_ms = cand_score.metric_scores.get(metric)
            
            if planned_ms and cand_ms:
                if cand_ms[1] < planned_ms[1]:  # Lower score = better
                    better_metrics.append(metric)
                elif cand_ms[1] > planned_ms[1]:
                    worse_metrics.append(metric)
        
        alternatives.append(AlternativeWindow(
            time=cand_time,
            score=cand_score.score,
            severity=cand_score.severity,
            improvement_vs_planned=improvement,
            better_metrics=better_metrics,
            worse_metrics=worse_metrics,
            conditions=cand_score.metrics,
        ))
    
    # Sort alternatives by score (best first)
    alternatives.sort(key=lambda a: a.score)
    
    # Determine recommendation
    recommended_time: datetime | None = None
    recommendation: str | None = None
    reason_codes: list[str] = []
    limitations: list[str] = []
    
    if alternatives:
        best = alternatives[0]
        
        # Recommend alternative only if severity is also better or score significantly better
        severity_rank = {"info": 0, "caution": 1, "warning": 2}
        planned_rank = severity_rank.get(planned_score.severity, 0)
        best_rank = severity_rank.get(best.severity, 0)
        
        if best_rank < planned_rank or best.improvement_vs_planned < -_MIN_IMPROVEMENT_THRESHOLD:
            recommended_time = best.time
            
            # Build reason codes
            if best.better_metrics:
                reason_codes.append(f"better_conditions:{','.join(best.better_metrics)}")
            if best.severity != planned_score.severity:
                reason_codes.append(f"severity_improved:{planned_score.severity}->{best.severity}")
            
            # Build natural language recommendation
            when_str = best.time.strftime("%H:%M")
            if len(best.better_metrics) > 0:
                better_str = ", ".join(best.better_metrics)
                recommendation = f"Consider rescheduling to {when_str} when {better_str} conditions are forecast to improve."
            else:
                recommendation = f"Consider rescheduling to {when_str} for better environmental conditions."
    else:
        # No better window found
        reason_codes.append("no_better_window_in_range")
        limitations.append(f"No materially better time found within ±{window_hours}h window")
    
    # Add limitations for missing data
    if planned_score.missing_metrics:
        limitations.append(f"Missing data for: {', '.join(planned_score.missing_metrics)}")
    
    # Add limitation for forecast uncertainty
    if planned_score.data_kind == "forecast":
        hours_ahead = (planned_time - now).total_seconds() / 3600
        if hours_ahead > 24:
            limitations.append("Forecast >24h out; accuracy decreases with time")
    
    return WindowComparison(
        planned_time=planned_time,
        planned_score=planned_score,
        alternatives=alternatives[:5],  # Top 5 alternatives
        recommended_time=recommended_time,
        recommendation=recommendation,
        reason_codes=reason_codes,
        limitations=limitations,
    )
