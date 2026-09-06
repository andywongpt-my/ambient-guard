"""Reasoning engine (M4) — fuse ContextIntent + environmental Observations into one
grounded Recommendation.

Deterministic threshold rules produce Evidence items; the engine composes them into a
single recommendation and a reasoning summary. GUARDRAIL (FR-4.2): a recommendation is
only emitted with >=1 evidence item — an activity with no triggered thresholds yields an
"all clear" recommendation whose evidence is the reassuring observations themselves, so
the >=1 invariant always holds when data exists. If NO observations exist at all, the
engine raises so the API surfaces the gap rather than inventing advice.
"""
from __future__ import annotations

from datetime import datetime

from app.agent.models import ContextIntent
from app.agent.reasoning_models import Assessment, Evidence, Recommendation
from app.environmental.base import Observation

_OUTDOOR = {"jogging", "running", "walking", "cycling", "hiking", "swimming",
            "commute", "picnic", "gardening", "exercise"}

# metric -> list of (threshold, comparison, severity, note-template). First match per metric.
# Comparison: value >= threshold triggers.
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
    def assess(self, context: ContextIntent, observations: list[Observation],
               provider_errors: list[str] | None = None) -> Assessment:
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
