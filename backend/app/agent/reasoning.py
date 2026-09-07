"""Reasoning engine (M4/G2) — fuse ContextIntent + environmental Observations into one
grounded Recommendation with alternative-time analysis.

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
"""
from __future__ import annotations

from datetime import datetime

from app.agent.activity_policy import get_important_metrics
from app.agent.models import ContextIntent
from app.agent.reasoning_models import (
    Assessment,
    AlternativeWindow,
    Evidence,
    PlannedWindow,
    Recommendation,
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
        observe_func=None,  # G2: for window comparison
        lat: float | None = None,
        lon: float | None = None,
    ) -> Assessment:
        if not observations:
            raise ReasoningError("no environmental observations to reason over")

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
        
        # G2: Find alternative windows if we have the necessary context
        alternatives: list[AlternativeWindow] = []
        environmentally_better_window: datetime | None = None
        recommended_window: datetime | None = None
        reason_codes: list[str] = []
        limitations: list[str] = []
        
        if observe_func and lat is not None and lon is not None and context.planned_time:
            try:
                comparison = find_alternative_window(
                    planned_time=context.planned_time,
                    observe_func=observe_func,
                    lat=lat,
                    lon=lon,
                    activity=activity,
                )
                
                # Convert to output format
                for alt in comparison.alternatives:
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
                    ))
                
                reason_codes = comparison.reason_codes
                limitations = comparison.limitations
                
                # G2.7: Distinguish environmentally-better from personally-recommended
                if comparison.recommended_time:
                    environmentally_better_window = comparison.recommended_time
                    reason_codes.append("environmentally_better_window_found")
                    
                    # Personal recommendation requires feasibility knowledge
                    # Check if the recommended time is within reasonable hours (6am-10pm)
                    rec_hour = comparison.recommended_time.hour
                    if 6 <= rec_hour <= 22:
                        # Reasonable time for outdoor activity
                        recommended_window = comparison.recommended_time
                        reason_codes.append("personal_recommendation_feasible")
                    else:
                        # Late night or early morning - not practical for most users
                        limitations.append(
                            f"Environmentally better window at {comparison.recommended_time.strftime('%H:%M')} "
                            "may not be practical for outdoor activity"
                        )
                        reason_codes.append("personal_recommendation_not_feasible")
                
                # G2.5: Enhance recommendation text if alternative exists
                if comparison.recommendation:
                    # Use "environmental conditions appear more favorable" language
                    # rather than "you should exercise at..."
                    if recommended_window:
                        text = comparison.recommendation + " " + text
                    elif environmentally_better_window:
                        # Environmentally better but not personally recommended
                        when_str = environmentally_better_window.strftime("%H:%M")
                        text = f"Environmental conditions appear more favorable later around {when_str}. " + text
                    
            except Exception as e:
                # Alternative-finding failure should not break the main assessment
                limitations.append(f"Alternative window analysis unavailable: {e}")
        
        return Assessment(
            context=context,
            observations=observations,
            recommendation=Recommendation(
                text=text,
                reasoning_summary=summary,
                evidence=evidence,
                timestamps={
                    "planned_time": context.planned_time,
                    "assessed_at": datetime.now(),
                },
                confidence=round(min(1.0, 0.5 + 0.1 * len(evidence)) * (context.confidence or 0.6), 2),
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
