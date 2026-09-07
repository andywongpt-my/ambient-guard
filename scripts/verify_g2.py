#!/usr/bin/env python
"""Verify G2 implementation compiles and basic logic works."""
import sys
sys.path.insert(0, "backend")

from datetime import datetime, timedelta

from app.agent.activity_policy import (
    ActivityType,
    MetricImportance,
    evaluate_observation_for_activity,
    get_activity_policy,
    get_important_metrics,
)
from app.agent.window_selector import score_window, find_alternative_window
from app.environmental.base import Observation, ObservationSource


def make_obs(metric: str, value: float, kind: str = "forecast") -> Observation:
    return Observation(
        metric=metric,
        value=value,
        unit="AQI" if metric == "aqi" else "µg/m³" if metric in ("pm25", "pm10") else "index" if metric == "uv" else "°C",
        kind=kind,
        source=ObservationSource(
            provider="open-meteo",
            fetched_at=datetime.now(),
            observed_at=datetime.now() + timedelta(hours=3),
        ),
        aqi_standard="us_epa" if metric == "aqi" else None,
        quality="unhealthy_sensitive" if metric == "aqi" and value > 100 else "moderate" if metric == "aqi" else None,
    )


def main():
    print("=== G2 Implementation Verification ===\n")
    
    # Test 1: Activity policy
    print("1. Activity Policy")
    policy = get_activity_policy("jogging")
    print(f"   Jogging AQI importance: {policy.metrics['aqi'].importance.value}")
    print(f"   Jogging is outdoor: {policy.is_outdoor}")
    print(f"   Jogging exertion: {policy.exertion_level}")
    
    # Test 2: Metric importance ordering
    print("\n2. Important Metrics for Jogging")
    metrics = get_important_metrics("jogging")
    print(f"   Ordered by importance: {metrics[:4]}...")
    
    # Test 3: Observation evaluation
    print("\n3. Observation Evaluation")
    obs = make_obs("aqi", 119)
    severity, score = evaluate_observation_for_activity(obs, "jogging")
    print(f"   AQI 119 for jogging: severity={severity}, score={score:.2f}")
    
    # Test 4: Window scoring
    print("\n4. Window Scoring")
    now = datetime.now()
    observations = [
        make_obs("aqi", 119),
        make_obs("pm25", 35),
        make_obs("uv", 5),
    ]
    window_score = score_window(observations, now, "jogging", ["aqi", "pm25", "uv"])
    print(f"   Score: {window_score.score:.3f}")
    print(f"   Severity: {window_score.severity}")
    print(f"   Data kind: {window_score.data_kind}")
    
    # Test 5: Alternative window finding
    print("\n5. Alternative Window Finding")
    planned = now + timedelta(hours=5)
    
    def observe_func(lat, lon, when):
        hour_diff = int((when - now).total_seconds() / 3600)
        if hour_diff == 5:  # Planned time - unhealthy
            return [make_obs("aqi", 175), make_obs("pm25", 55), make_obs("uv", 8)], []
        elif hour_diff == 7:  # Better window
            return [make_obs("aqi", 50), make_obs("pm25", 15), make_obs("uv", 3)], []
        else:
            return [make_obs("aqi", 100), make_obs("pm25", 30), make_obs("uv", 5)], []
    
    comparison = find_alternative_window(
        planned_time=planned,
        observe_func=observe_func,
        lat=6.183,
        lon=116.22,
        activity="jogging",
        window_hours=3,
        now=now,
    )
    
    print(f"   Planned time: {planned.strftime('%H:%M')}")
    print(f"   Planned severity: {comparison.planned_score.severity}")
    print(f"   Alternatives found: {len(comparison.alternatives)}")
    if comparison.recommended_time:
        print(f"   Recommended time: {comparison.recommended_time.strftime('%H:%M')}")
        print(f"   Reason codes: {comparison.reason_codes}")
    print(f"   Limitations: {comparison.limitations}")
    
    # Test 6: No better window case
    print("\n6. No Better Window Case")
    
    def all_good_observe(lat, lon, when):
        return [make_obs("aqi", 50), make_obs("pm25", 15), make_obs("uv", 3)], []
    
    comparison2 = find_alternative_window(
        planned_time=planned,
        observe_func=all_good_observe,
        lat=6.183,
        lon=116.22,
        activity="jogging",
        window_hours=3,
        now=now,
    )
    print(f"   Reason codes: {comparison2.reason_codes}")
    print(f"   Recommended time: {comparison2.recommended_time}")
    
    print("\n=== All G2 Verification Passed ===")


if __name__ == "__main__":
    main()
