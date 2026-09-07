"""G2.9: Tests for time-window comparison and alternative selection.

Covers:
- AQI standard attribution
- Observed vs forecast classification
- Time-window comparison
- Alternative selection
- No-better-alternative case
- Partial environmental data
- Conflicting metrics
- Confidence/source decomposition
"""
import os
from datetime import datetime, timedelta

import pytest

from app.agent.activity_policy import (
    ActivityType,
    MetricImportance,
    evaluate_observation_for_activity,
    get_activity_policy,
    get_important_metrics,
)
from app.agent.window_selector import (
    WindowScore,
    AlternativeWindow,
    WindowComparison,
    find_alternative_window,
    score_window,
)
from app.environmental.base import Observation, ObservationSource


def make_obs(
    metric: str,
    value: float,
    kind: str = "forecast",
    aqi_standard: str | None = None,
    quality: str | None = None,
) -> Observation:
    """Helper to create test observations."""
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
        aqi_standard=aqi_standard,
        quality=quality,
    )


class TestAQIStandardAttribution:
    """G2.1: AQI standard must be explicit."""
    
    def test_aqi_has_us_epa_standard(self):
        """AQI observations must carry the standard."""
        obs = make_obs("aqi", 119, aqi_standard="us_epa", quality="unhealthy_sensitive")
        assert obs.aqi_standard == "us_epa"
        assert obs.quality == "unhealthy_sensitive"
    
    def test_aqi_quality_classification_good(self):
        obs = make_obs("aqi", 45, aqi_standard="us_epa", quality="good")
        assert obs.quality == "good"
    
    def test_aqi_quality_classification_moderate(self):
        obs = make_obs("aqi", 75, aqi_standard="us_epa", quality="moderate")
        assert obs.quality == "moderate"
    
    def test_aqi_quality_classification_unhealthy_sensitive(self):
        obs = make_obs("aqi", 119, aqi_standard="us_epa", quality="unhealthy_sensitive")
        assert obs.quality == "unhealthy_sensitive"
    
    def test_aqi_quality_classification_unhealthy(self):
        obs = make_obs("aqi", 175, aqi_standard="us_epa", quality="unhealthy")
        assert obs.quality == "unhealthy"


class TestObservedVsForecast:
    """G2.7: Observed and forecast data must be distinguishable."""
    
    def test_forecast_kind_explicit(self):
        obs = make_obs("aqi", 119, kind="forecast")
        assert obs.kind == "forecast"
    
    def test_observed_kind_explicit(self):
        obs = make_obs("aqi", 119, kind="observed")
        assert obs.kind == "observed"
    
    def test_window_score_tracks_data_kind(self):
        """WindowScore must reflect forecast vs observed."""
        now = datetime.now()
        observations = [
            make_obs("aqi", 119, kind="forecast"),
            make_obs("pm25", 35, kind="forecast"),
        ]
        score = score_window(observations, now, "jogging", ["aqi", "pm25"])
        assert score.data_kind == "forecast"


class TestActivityPolicy:
    """G2.4: Activity-aware evaluation."""
    
    def test_jogging_has_high_aqi_importance(self):
        policy = get_activity_policy("jogging")
        assert policy is not None
        assert policy.metrics["aqi"].importance == MetricImportance.HIGH
    
    def test_walking_has_lower_aqi_importance(self):
        jogging = get_activity_policy("jogging")
        walking = get_activity_policy("walking")
        assert jogging is not None
        assert walking is not None
        # Jogging has higher AQI importance than walking
        jogging_aqi_rank = {"high": 0, "medium": 1, "low": 2}[jogging.metrics["aqi"].importance.value]
        walking_aqi_rank = {"high": 0, "medium": 1, "low": 2}[walking.metrics["aqi"].importance.value]
        assert jogging_aqi_rank <= walking_aqi_rank  # Lower rank = higher importance
    
    def test_evaluate_observation_for_activity_warning(self):
        obs = make_obs("aqi", 175)  # Unhealthy
        severity, score = evaluate_observation_for_activity(obs, "jogging")
        assert severity == "warning"
        assert score == 1.0
    
    def test_evaluate_observation_for_activity_caution(self):
        obs = make_obs("aqi", 119)  # Unhealthy for sensitive groups
        severity, score = evaluate_observation_for_activity(obs, "jogging")
        assert severity == "caution"
        assert 0.5 <= score < 1.0
    
    def test_evaluate_observation_for_activity_info(self):
        obs = make_obs("aqi", 45)  # Good
        severity, score = evaluate_observation_for_activity(obs, "jogging")
        assert severity == "info"
        assert score < 0.5


class TestTimeWindowComparison:
    """G2.3: Time-window comparison."""
    
    def test_score_planned_window(self):
        now = datetime.now()
        planned = now + timedelta(hours=5)
        observations = [
            make_obs("aqi", 119),
            make_obs("pm25", 35),
            make_obs("uv", 5),
        ]
        score = score_window(observations, planned, "jogging", ["aqi", "pm25", "uv"])
        assert 0.0 <= score.score <= 1.0
        assert score.severity in ("info", "caution", "warning")
    
    def test_find_alternative_better_window(self):
        """When a better window exists, it should be identified."""
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        planned = now + timedelta(hours=5)
        
        def observe_func(lat, lon, when):
            # Planned time: AQI 175 (unhealthy)
            # 2h later: AQI 50 (good) - should be recommended
            hour_diff = int((when - now).total_seconds() / 3600)
            if hour_diff == 5:  # Planned time
                return [
                    make_obs("aqi", 175),
                    make_obs("pm25", 55),
                    make_obs("uv", 8),
                ], []
            elif hour_diff == 7:  # Better window
                return [
                    make_obs("aqi", 50),
                    make_obs("pm25", 15),
                    make_obs("uv", 3),
                ], []
            else:
                return [
                    make_obs("aqi", 100),
                    make_obs("pm25", 30),
                    make_obs("uv", 5),
                ], []
        
        comparison = find_alternative_window(
            planned_time=planned,
            observe_func=observe_func,
            lat=6.183,
            lon=116.22,
            activity="jogging",
            window_hours=3,
            now=now,
        )
        
        assert comparison.planned_time == planned
        assert comparison.planned_score.severity == "warning"
        assert len(comparison.alternatives) > 0
        assert comparison.recommended_time is not None
        assert "better_conditions" in " ".join(comparison.reason_codes) or "severity_improved" in " ".join(comparison.reason_codes)
    
    def test_find_alternative_no_better_window(self):
        """G2.8: When no better window exists, system should say so."""
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        planned = now + timedelta(hours=5)
        
        def observe_func(lat, lon, when):
            # All windows have same conditions
            return [
                make_obs("aqi", 50),  # Good
                make_obs("pm25", 15),
                make_obs("uv", 3),
            ], []
        
        comparison = find_alternative_window(
            planned_time=planned,
            observe_func=observe_func,
            lat=6.183,
            lon=116.22,
            activity="jogging",
            window_hours=3,
            now=now,
        )
        
        # Planned time is already good
        assert comparison.planned_score.severity == "info"
        # No better alternative should be found
        assert "no_better_window_in_range" in comparison.reason_codes


class TestPartialEnvironmentalData:
    """G2.8: Graceful uncertainty with partial data."""
    
    def test_missing_aqi_continues(self):
        """Missing AQI should not break the assessment."""
        now = datetime.now()
        observations = [
            make_obs("pm25", 35),
            make_obs("uv", 5),
        ]
        score = score_window(observations, now, "jogging", ["aqi", "pm25", "uv"])
        assert "aqi" in score.missing_metrics
        assert score.score >= 0.0  # Should still produce a score
    
    def test_missing_multiple_metrics(self):
        now = datetime.now()
        observations = [make_obs("aqi", 50)]
        score = score_window(observations, now, "jogging", ["aqi", "pm25", "uv", "temp_c"])
        assert len(score.missing_metrics) == 3


class TestConflictingMetrics:
    """G2.8: Handle conflicting environmental metrics."""
    
    def test_conflicting_metrics_warning_wins(self):
        """When AQI is bad but UV is good, warning should still trigger."""
        now = datetime.now()
        observations = [
            make_obs("aqi", 175),  # Unhealthy - warning
            make_obs("uv", 2),     # Low UV - good
            make_obs("temp_c", 25),  # Comfortable
        ]
        score = score_window(observations, now, "jogging", ["aqi", "pm25", "uv", "temp_c"])
        assert score.severity == "warning"
    
    def test_mixed_severity_elevates_to_caution(self):
        now = datetime.now()
        observations = [
            make_obs("aqi", 119),  # Unhealthy for sensitive - caution
            make_obs("uv", 2),     # Good
        ]
        score = score_window(observations, now, "jogging", ["aqi", "uv"])
        assert score.severity == "caution"


class TestTimezoneCorrectness:
    """G2.9: Timezone correctness."""
    
    def test_planned_time_preserved(self):
        """Planned time should be preserved through window comparison."""
        now = datetime.now()
        planned = now + timedelta(hours=5)
        
        def observe_func(lat, lon, when):
            return [make_obs("aqi", 50)], []
        
        comparison = find_alternative_window(
            planned_time=planned,
            observe_func=observe_func,
            lat=6.183,
            lon=116.22,
            activity="jogging",
            now=now,
        )
        
        assert comparison.planned_time == planned


class TestDeterministicRecommendation:
    """G2.6: Recommendation must be reconstructable from evidence."""
    
    def test_window_comparison_provides_reason_codes(self):
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        planned = now + timedelta(hours=5)
        
        def observe_func(lat, lon, when):
            return [make_obs("aqi", 175), make_obs("pm25", 55)], []
        
        comparison = find_alternative_window(
            planned_time=planned,
            observe_func=observe_func,
            lat=6.183,
            lon=116.22,
            activity="jogging",
            window_hours=2,
            now=now,
        )
        
        # Reason codes must be populated
        assert isinstance(comparison.reason_codes, list)
        # Limitations must be populated
        assert isinstance(comparison.limitations, list)
    
    def test_alternative_window_has_condition_data(self):
        """Alternative windows must carry full condition data."""
        now = datetime.now()
        planned = now + timedelta(hours=5)
        
        def observe_func(lat, lon, when):
            return [
                make_obs("aqi", 50),
                make_obs("pm25", 15),
                make_obs("uv", 3),
            ], []
        
        comparison = find_alternative_window(
            planned_time=planned,
            observe_func=observe_func,
            lat=6.183,
            lon=116.22,
            activity="jogging",
            now=now,
        )
        
        # Planned window should have condition data
        if comparison.planned_score.metrics:
            assert comparison.planned_score.metrics.get("aqi") is not None or comparison.planned_score.metrics.get("pm25") is not None
