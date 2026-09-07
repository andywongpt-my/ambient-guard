"""Reasoning engine (M4/G2/G3) — fuse ContextIntent + environmental Observations + personal context into one grounded recommendation.

Deterministic threshold rules produce Evidence items; the engine composes them into a
single recommendation and a reasoning summary. GUARDRAIL (FR-4.2): a recommendation is
only emitted with >=1 evidence item — an activity with no triggered thresholds yields an
"all clear" recommendation whose evidence is the reassuring observations themselves, so
the >=1 invariant always holds when data exists. If NO observations exist at all, the
engine raises so the API surfaces the gap rather than inventing advice.

G2 enhancements:
- Activity-aware evaluation via activity_policy
- Time-window comparison via window_selector
- Structured explanation data for full reconstructability

G3 enhancements:
- Personal context extraction and feasibility evaluation
- Decision state machine for explicit recommendation states
- Personal Environmental Timeline
- Context provenance and freshness tracking
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from app.agent.activity_policy import get_important_metrics
from app.agent.decision_state import (
    DecisionState,
    DecisionResult,
    determine_decision_state,
    format_decision_for_user,
)
from app.agent.models import ContextIntent
from app.agent.personal_context import (
    PersonalContext,
    PersonalFeasibility,
    extract_personal_context,
    evaluate_candidate_feasibility,
)
from app.agent.reasoning_models import (
    Assessment,
    AlternativeWindow,
    Evidence,
    PlannedWindow,
    Recommendation,
    PersonalContextRecord,
    PersonalConstraintRecord,
    TimelineEntry,
    PersonalEnvironmentalTimeline,
)
from app.agent.window_selector import find_alternative_window, score_window
from app.environmental.base import Observation

_OUTDOOR = {"jogging", "running", "walking", "cycling", "hiking", "swimming",
            "commute", "picnic", "gardening", "exercise"}

# metric -> list of (threshold, severity, note-template). First match per metric.
# Thresholds align with activity_policy.py and public health guidance.
_RULES: dict[str, list[tuple[float, str, str]]] = {
    "aqi":   [(150, "warning", "AQI {v:.0f} is unhealthy — limit sustained outdoor exertion"),
              (100, "caution", "AQI {v:.0f} is unhealthy for sensitive groups")],
    "pm25":  [(55.5, "warning", "PM2.5 {v:.0f} µg/m³ is unhealthy for exertion"),
              (35.5, "caution", "PM2.5 {v:.0f} µg/m³ is elevated (moderate)")],
    "pm10":  [(155, "warning", "PM10 {v:.0f} µg/m³ is unhealthy"),
              (55, "caution", "PM10 {v:.0f} µg/m³ is elevated")],
    "uv":    [(8, "warning", "UV index {v:.0f} is very high — sun protection strongly advised"),
              (6, "caution", "UV index {v:.0f} is high — wear sunscreen")],
    "temp_c":[(35, "warning", "Temperature {v:.0f}°C is very hot — heat stress risk"),
              (31, "caution", "Temperature {v:.0f}°C is hot")],
}


class ReasoningError(RuntimeError):
    pass


class ReasoningEngine:
    def assess(
        self,
        context: ContextIntent,
        observations: list[Observation],
        provider_errors: list[str] | None = None,
        *,
        observe_func: Callable | None = None,  # G2: for window comparison
        lat: float | None = None,
        lon: float | None = None,
        # G3: Personal context
        bee_today_context: dict | None = None,  # Raw Bee today context
    ) -> Assessment:
        """Assess environmental conditions with personal context intelligence.
        
        Args:
            context: Normalized user intent (activity, time, location)
            observations: Environmental observations for the planned time
            provider_errors: Errors from environmental data providers
            observe_func: Function to get observations for a specific time (G2)
            lat, lon: Location coordinates for alternative window search
            bee_today_context: Raw Bee today context dict for personal context extraction (G3)
        
        Returns:
            Assessment with recommendation, alternatives, and personal context evaluation
        """
        if not observations:
            raise ReasoningError("no environmental observations to reason over")

        now = datetime.now()
        by_metric = {o.metric: o for o in observations}
        activity = context.activity or "your activity"
        is_outdoor = (context.activity in _OUTDOOR) if context.activity else True

        evidence: list[Evidence] = []
        worst = "info"
        rank = {"info": 0, "caution": 1, "warning": 2}

        for metric, rules in _RULES.items():
            obs = by_metric.get(metric)
            if obs is None:
                continue
            for threshold, severity, tmpl in rules:
                if obs.value >= threshold:
                    evidence.append(Evidence(
                        observation=obs, note=tmpl.format(v=obs.value), severity=severity))
                    if rank[severity] > rank[worst]:
                        worst = severity
                    break  # only the highest matching tier per metric

        # Guardrail: ensure >=1 evidence item. If nothing tripped, cite the key
        # reassuring readings so the "all clear" is still grounded in data.
        if not evidence:
            for metric in ("aqi", "pm25", "uv", "temp_c"):
                obs = by_metric.get(metric)
                if obs is not None:
                    evidence.append(Evidence(
                        observation=obs,
                        note=f"{metric} {obs.value:.0f} {obs.unit} is within a comfortable range",
                        severity="info"))
                if len(evidence) >= 2:
                    break
        if not evidence:  # still nothing usable -> refuse (never ungrounded)
            raise ReasoningError("no usable observations to ground a recommendation")

        text, summary = self._compose(activity, is_outdoor, worst, evidence, context)
        
        # G2: Build planned window structure
        planned_window = self._build_planned_window(context.planned_time, by_metric)
        
        # G3: Extract personal context from Bee
        personal_context = extract_personal_context(bee_today_context, now)
        
        # G2/G3: Find alternative windows and evaluate personal feasibility
        alternatives: list[AlternativeWindow] = []
        environmentally_better_window: datetime | None = None
        recommended_window: datetime | None = None
        reason_codes: list[str] = []
        limitations: list[str] = []
        candidate_evaluations: list[dict[str, Any]] = []
        decision_state_value: str | None = None  # G4: Track decision state for UI
        
        if observe_func and lat is not None and lon is not None and context.planned_time:
            try:
                comparison = find_alternative_window(
                    planned_time=context.planned_time,
                    observe_func=observe_func,
                    lat=lat,
                    lon=lon,
                    activity=activity,
                )
                
                # G3: Evaluate personal feasibility for each alternative
                for alt in comparison.alternatives:
                    # Evaluate personal feasibility
                    feasibility = evaluate_candidate_feasibility(
                        candidate_time=alt.time,
                        personal_context=personal_context,
                        activity=activity,
                    )
                    
                    # Convert to output format
                    alternatives.append(AlternativeWindow(
                        time=alt.time,
                        severity=alt.severity,
                        improvement=alt.improvement_vs_planned,
                        better_metrics=alt.better_metrics,
                        worse_metrics=alt.worse_metrics,
                        aqi=alt.conditions.get("aqi").value if "aqi" in alt.conditions else None,
                        pm25=alt.conditions.get("pm25").value if "pm25" in alt.conditions else None,
                        uv=alt.conditions.get("uv").value if "uv" in alt.conditions else None,
                        temp_c=alt.conditions.get("temp_c").value if "temp_c" in alt.conditions else None,
                        # G3: Personal feasibility
                        personal_feasibility_status=feasibility.status.value,
                        personal_conflicts=[c.to_dict() for c in feasibility.conflicts],
                    ))
                    
                    # Store evaluation for output
                    candidate_evaluations.append({
                        "candidate_time": alt.time.isoformat(),
                        "environmental_score": alt.score,
                        "personal_feasibility": feasibility.to_dict(),
                    })
                
                reason_codes = comparison.reason_codes
                limitations = comparison.limitations
                
                # G3: Run decision state machine
                if comparison.recommended_time:
                    environmentally_better_window = comparison.recommended_time
                    
                    # Evaluate feasibility for the environmentally best window
                    best_feasibility = evaluate_candidate_feasibility(
                        candidate_time=comparison.recommended_time,
                        personal_context=personal_context,
                        activity=activity,
                    )
                    
                    # Determine final decision state
                    decision = determine_decision_state(
                        has_environmentally_better_window=True,
                        environmentally_better_time=comparison.recommended_time.strftime("%H:%M"),
                        personal_feasibility=best_feasibility,
                        personal_context=personal_context,
                        activity_is_certain=context.activity is not None,
                        has_environmental_data=True,
                        material_improvement_met=True,
                    )
                    
                    # G4: Track decision state for UI
                    decision_state_value = decision.state.value
                    
                    # Update recommendation based on decision state
                    reason_codes.extend(decision.reason_codes)
                    limitations.extend(decision.limitations)
                    
                    if decision.state == DecisionState.BETTER_WINDOW_AVAILABLE:
                        recommended_window = comparison.recommended_time
                        text = decision.natural_language
                    else:
                        # Do not recommend - update text accordingly
                        text = decision.natural_language
                else:
                    # No better window found
                    decision = determine_decision_state(
                        has_environmentally_better_window=False,
                        environmentally_better_time=None,
                        personal_feasibility=None,
                        personal_context=personal_context,
                        activity_is_certain=context.activity is not None,
                        has_environmental_data=True,
                        material_improvement_met=False,
                    )
                    decision_state_value = decision.state.value
                    reason_codes.extend(decision.reason_codes)
                
            except Exception as e:
                # Alternative-finding failure should not break the main assessment
                limitations.append(f"Alternative window analysis unavailable: {e}")
        
        # G3: Build personal context record (sanitized)
        personal_context_record = self._build_personal_context_record(personal_context)
        
        # G3: Build Personal Environmental Timeline
        timeline = self._build_timeline(
            context=context,
            planned_window=planned_window,
            alternatives=alternatives,
            personal_context=personal_context,
            now=now,
        )
        
        return Assessment(
            context=context,
            observations=observations,
            recommendation=Recommendation(
                text=text,
                reasoning_summary=summary,
                evidence=evidence,
                timestamps={
                    "planned_time": context.planned_time,
                    "assessed_at": now,
                },
                confidence=round(min(1.0, 0.5 + 0.1 * len(evidence)) * (context.confidence or 0.6), 2),
                decision_state=decision_state_value,
            ),
            provider_errors=provider_errors or [],
            # G2.6: Structured explanation data
            planned_window=planned_window,
            alternatives=alternatives,
            # G2.7: Distinguish environmentally-better from personally-recommended
            environmentally_better_window=environmentally_better_window,
            recommended_window=recommended_window,
            reason_codes=reason_codes,
            limitations=limitations,
            # G3: Personal context intelligence
            personal_context=personal_context_record,
            candidate_evaluations=candidate_evaluations,
            decision_state=decision_state_value,
            natural_language_recommendation=text,
            timeline=timeline,
        )
    
    @staticmethod
    def _build_planned_window(
        planned_time: datetime | None,
        by_metric: dict[str, Observation],
    ) -> PlannedWindow | None:
        """Build structured planned window data."""
        if not planned_time:
            return None
        
        aqi_obs = by_metric.get("aqi")
        uv_obs = by_metric.get("uv")
        temp_obs = by_metric.get("temp_c")
        pm25_obs = by_metric.get("pm25")
        humidity_obs = by_metric.get("humidity")
        
        # Determine severity from observations
        severity = "info"
        for metric, rules in _RULES.items():
            obs = by_metric.get(metric)
            if obs is None:
                continue
            for threshold, sev, _ in rules:
                if obs.value >= threshold:
                    if {"info": 0, "caution": 1, "warning": 2}.get(sev, 0) > \
                       {"info": 0, "caution": 1, "warning": 2}.get(severity, 0):
                        severity = sev
                    break
        
        # Determine data kind
        kinds = {o.kind for o in by_metric.values()}
        data_kind = "forecast" if "forecast" in kinds else "observed"
        
        return PlannedWindow(
            time=planned_time,
            severity=severity,
            aqi=aqi_obs.value if aqi_obs else None,
            pm25=pm25_obs.value if pm25_obs else None,
            uv=uv_obs.value if uv_obs else None,
            temp_c=temp_obs.value if temp_obs else None,
            humidity=humidity_obs.value if humidity_obs else None,
            data_kind=data_kind,
        )
    
    @staticmethod
    def _build_personal_context_record(
        personal_context: PersonalContext,
    ) -> PersonalContextRecord | None:
        """Build sanitized personal context record for output (G3.11)."""
        if not personal_context.constraints and not personal_context.preferences:
            return None
        
        # Convert constraints to records (sanitized - no raw text)
        constraint_records = [
            PersonalConstraintRecord(
                constraint_type=c.constraint_type.value,
                value=c.value.isoformat() if isinstance(c.value, datetime) else str(c.value),
                source_type=c.source_type,
                source_id=c.source_id,
                confidence=c.confidence.value,
            )
            for c in personal_context.constraints
        ]
        
        # Convert preferences
        preference_records = [p.to_dict() for p in personal_context.preferences]
        
        # Summarize freshness
        freshness_summary = {
            "sources_checked": len(personal_context.freshness),
            "stale_sources": sum(1 for f in personal_context.freshness if f.is_stale),
            "has_sufficient_context": personal_context.has_sufficient_context,
        }
        
        return PersonalContextRecord(
            constraints=constraint_records,
            preferences=preference_records,
            freshness=freshness_summary,
        )
    
    @staticmethod
    def _build_timeline(
        context: ContextIntent,
        planned_window: PlannedWindow | None,
        alternatives: list[AlternativeWindow],
        personal_context: PersonalContext,
        now: datetime,
    ) -> PersonalEnvironmentalTimeline:
        """Build Personal Environmental Timeline (G3.9)."""
        entries: list[TimelineEntry] = []
        
        # Add planned activity entry
        if planned_window:
            entries.append(TimelineEntry(
                time=planned_window.time,
                entry_type="planned",
                label=f"Planned {context.activity or 'activity'}",
                environmental_conditions={
                    "aqi": planned_window.aqi,
                    "pm25": planned_window.pm25,
                    "uv": planned_window.uv,
                    "temp_c": planned_window.temp_c,
                    "severity": planned_window.severity,
                },
                exposure_kind="outdoor" if context.activity in _OUTDOOR else "indoor",
                data_kind=planned_window.data_kind,
                uncertainty=[] if planned_window.data_kind == "observed" else ["forecast"],
            ))
        
        # Add alternative windows
        for alt in alternatives:
            conflict_str = ""
            if alt.personal_feasibility_status == "conflicting":
                conflict_str = " (personal conflict detected)"
            elif alt.personal_feasibility_status == "unknown":
                conflict_str = " (feasibility unknown)"
            
            entries.append(TimelineEntry(
                time=alt.time,
                entry_type="alternative",
                label=f"Alternative window{conflict_str}",
                environmental_conditions={
                    "aqi": alt.aqi,
                    "pm25": alt.pm25,
                    "uv": alt.uv,
                    "temp_c": alt.temp_c,
                    "severity": alt.severity,
                    "improvement": alt.improvement,
                },
                exposure_kind="outdoor" if context.activity in _OUTDOOR else "indoor",
                data_kind="forecast",
                uncertainty=["forecast", "personal_feasibility"] if alt.personal_feasibility_status != "feasible" else ["forecast"],
            ))
        
        # Add personal context entries (sanitized)
        for constraint in personal_context.constraints:
            if isinstance(constraint.value, datetime):
                entries.append(TimelineEntry(
                    time=constraint.value,
                    entry_type="bee_context",
                    label=f"Personal constraint: {constraint.constraint_type.value}",
                    bee_context=f"From {constraint.source_type}",  # Sanitized
                    exposure_kind=None,
                    data_kind=None,
                    uncertainty=[],
                ))
        
        # Sort by time
        entries.sort(key=lambda e: e.time)
        
        return PersonalEnvironmentalTimeline(
            entries=entries,
            date=now.strftime("%Y-%m-%d"),
            timezone=None,  # TODO: extract from Bee context
        )

    @staticmethod
    def _compose(activity, is_outdoor, worst, evidence, context) -> tuple[str, str]:
        when = context.planned_time.strftime("%H:%M") if context.planned_time else "your planned time"
        concerns = "; ".join(e.note for e in evidence if e.severity != "info")
        if worst == "info" or not is_outdoor:
            text = (f"Conditions for {activity} at {when} look acceptable. "
                    "No elevated environmental risks detected.")
        elif worst == "warning":
            text = (f"Consider rescheduling {activity} at {when} or moving it indoors: {concerns}. "
                    "If you go, keep it short and take precautions.")
        else:  # caution
            text = (f"{activity.capitalize()} at {when} is okay with care: {concerns}. "
                    "Take sensible precautions (hydration, sunscreen, lighter effort).")
        summary = (f"Assessed {activity} (outdoor={is_outdoor}) at {when} against "
                   f"{len(evidence)} environmental reading(s); worst severity: {worst}. "
                   "Framed as precautionary environmental guidance, not medical advice.")
        return text, summary
