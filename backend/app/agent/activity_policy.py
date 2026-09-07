"""G2.4: Activity-aware environmental evaluation policy.

Determines which environmental metrics matter most for each activity type,
and provides activity-specific thresholds and recommendations.

Keep V1 conservative and explainable. This is NOT medical diagnosis.

## Threshold Sources

### US EPA AQI (Official)
- Good: 0-50
- Moderate: 51-100
- Unhealthy for Sensitive Groups: 101-150
- Unhealthy: 151-200
- Source: https://www.airnow.gov/aqi/aqi-basics/

### WHO Air Quality Guidelines (Official)
- PM2.5 24-hour: 15 µg/m³
- PM10 24-hour: 45 µg/m³
- Source: https://www.who.int/publications/i/item/9789240034228

### UV Index (Official - EPA)
- Low: 0-2
- Moderate: 3-5
- High: 6-7
- Very High: 8-10
- Extreme: 11+
- Source: https://www.epa.gov/sunsafety/uv-index-scale-0

### Heat Index (Official - NWS)
- Caution: 27-32°C (apparent temp)
- Extreme Caution: 32-38°C
- Danger: 38-46°C
- Source: https://www.weather.gov/safety/heat

### Ambient Guard Heuristics (Product-Specific)
- Metric importance weights: HIGH=3x, MEDIUM=2x, LOW=1x
- Minimum improvement threshold: 15% score reduction
- Activity-specific exertion levels
- These are NOT health standards; they are product design choices.

"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.environmental.base import Observation


class ActivityType(str, Enum):
    JOGGING = "jogging"
    RUNNING = "running"
    WALKING = "walking"
    CYCLING = "cycling"
    HIKING = "hiking"
    SWIMMING = "swimming"
    EXERCISE = "exercise"
    COMMUTE = "commute"
    PICNIC = "picnic"
    GARDENING = "gardening"
    OUTDOOR_WORK = "outdoor_work"


class MetricImportance(str, Enum):
    """How important a metric is for an activity (1-3 scale)."""
    LOW = "low"          # Nice to know, rarely decisive
    MEDIUM = "medium"    # Relevant but not primary concern
    HIGH = "high"        # Primary concern for this activity


@dataclass
class MetricPolicy:
    """Policy for a single environmental metric for an activity."""
    importance: MetricImportance
    caution_threshold: float | None    # Trigger caution
    warning_threshold: float | None    # Trigger warning
    ideal_range: tuple[float, float] | None = None  # (min, max) ideal values
    notes: str | None = None


@dataclass
class ActivityPolicy:
    """Complete environmental policy for an activity type."""
    activity: ActivityType
    is_outdoor: bool
    exertion_level: str  # "low" | "moderate" | "high"
    metrics: dict[str, MetricPolicy]
    description: str
    health_note: str | None = None


# Activity-specific policies based on public health guidance
# Sources documented inline; thresholds are conservative estimates

_ACTIVITY_POLICIES: dict[ActivityType, ActivityPolicy] = {
    ActivityType.JOGGING: ActivityPolicy(
        activity=ActivityType.JOGGING,
        is_outdoor=True,
        exertion_level="high",
        metrics={
            "aqi": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=100,  # Unhealthy for sensitive groups (US EPA)
                warning_threshold=150,  # Unhealthy for everyone (US EPA)
                ideal_range=(0, 50),
                notes="Sustained cardio increases particulate intake; AQI critical for joggers",
            ),
            "pm25": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=35.5,  # WHO 24-hr guideline is 15 µg/m³; moderate begins 35.5
                warning_threshold=55.5,  # US EPA "Unhealthy for Sensitive Groups"
                notes="PM2.5 penetrates deep into lungs during heavy breathing",
            ),
            "uv": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=6,     # High (EPA)
                warning_threshold=8,     # Very high (EPA)
                ideal_range=(0, 5),
                notes="Sun exposure during extended outdoor exercise",
            ),
            "temp_c": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=31,    # Hot conditions
                warning_threshold=35,    # Very hot - heat stress risk (NWS)
                ideal_range=(10, 25),
                notes="Heat stress risk increases with sustained exertion",
            ),
            "humidity": MetricPolicy(
                importance=MetricImportance.LOW,
                caution_threshold=80,
                warning_threshold=None,
                notes="High humidity amplifies heat stress",
            ),
            "wind_kmh": MetricPolicy(
                importance=MetricImportance.LOW,
                caution_threshold=None,
                warning_threshold=40,    # Strong winds
                notes="Strong winds can affect running comfort",
            ),
            "precip_mm": MetricPolicy(
                importance=MetricImportance.LOW,
                caution_threshold=None,
                warning_threshold=5,     # Moderate rain
                notes="Rain affects comfort and visibility",
            ),
        },
        description="Sustained outdoor cardio exercise",
        health_note="Consult healthcare provider for personalized exercise guidance",
    ),
    
    ActivityType.RUNNING: ActivityPolicy(
        activity=ActivityType.RUNNING,
        is_outdoor=True,
        exertion_level="high",
        metrics={
            "aqi": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=100,
                warning_threshold=150,
                ideal_range=(0, 50),
            ),
            "pm25": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=35.5,
                warning_threshold=55.5,
            ),
            "uv": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=6,
                warning_threshold=8,
            ),
            "temp_c": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=31,
                warning_threshold=35,
                ideal_range=(10, 25),
            ),
        },
        description="High-intensity outdoor cardio",
        health_note="Higher intensity than jogging; same environmental concerns apply",
    ),
    
    ActivityType.WALKING: ActivityPolicy(
        activity=ActivityType.WALKING,
        is_outdoor=True,
        exertion_level="low",
        metrics={
            "aqi": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=150,   # Lower sensitivity than jogging
                warning_threshold=200,
            ),
            "pm25": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=55.5,
                warning_threshold=150,
            ),
            "uv": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=6,
                warning_threshold=8,
            ),
            "temp_c": MetricPolicy(
                importance=MetricImportance.LOW,
                caution_threshold=35,
                warning_threshold=40,
            ),
        },
        description="Low-intensity outdoor activity",
        health_note="Lower exertion reduces respiratory exposure intensity",
    ),
    
    ActivityType.CYCLING: ActivityPolicy(
        activity=ActivityType.CYCLING,
        is_outdoor=True,
        exertion_level="moderate",
        metrics={
            "aqi": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=100,
                warning_threshold=150,
            ),
            "pm25": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=35.5,
                warning_threshold=55.5,
            ),
            "uv": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=6,
                warning_threshold=8,
            ),
            "temp_c": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=31,
                warning_threshold=35,
            ),
            "wind_kmh": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=20,
                warning_threshold=40,
                notes="Headwind significantly affects cycling effort",
            ),
        },
        description="Moderate to high intensity outdoor cardio",
    ),
    
    ActivityType.HIKING: ActivityPolicy(
        activity=ActivityType.HIKING,
        is_outdoor=True,
        exertion_level="moderate",
        metrics={
            "aqi": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=100,
                warning_threshold=150,
            ),
            "uv": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=6,
                warning_threshold=8,
                notes="Extended outdoor exposure; sun protection critical",
            ),
            "temp_c": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=30,
                warning_threshold=35,
            ),
        },
        description="Extended outdoor activity, often in varied terrain",
    ),
    
    ActivityType.EXERCISE: ActivityPolicy(
        activity=ActivityType.EXERCISE,
        is_outdoor=True,
        exertion_level="moderate",
        metrics={
            "aqi": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=100,
                warning_threshold=150,
            ),
            "pm25": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=35.5,
                warning_threshold=55.5,
            ),
            "uv": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=6,
                warning_threshold=8,
            ),
            "temp_c": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=31,
                warning_threshold=35,
            ),
        },
        description="General outdoor exercise",
    ),
    
    ActivityType.COMMUTE: ActivityPolicy(
        activity=ActivityType.COMMUTE,
        is_outdoor=True,
        exertion_level="low",
        metrics={
            "aqi": MetricPolicy(
                importance=MetricImportance.LOW,
                caution_threshold=200,
                warning_threshold=300,
            ),
            "precip_mm": MetricPolicy(
                importance=MetricImportance.MEDIUM,
                caution_threshold=2,
                warning_threshold=10,
            ),
            "temp_c": MetricPolicy(
                importance=MetricImportance.LOW,
                caution_threshold=35,
                warning_threshold=40,
            ),
        },
        description="Brief outdoor exposure during commute",
    ),
    
    ActivityType.OUTDOOR_WORK: ActivityPolicy(
        activity=ActivityType.OUTDOOR_WORK,
        is_outdoor=True,
        exertion_level="moderate",
        metrics={
            "aqi": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=100,
                warning_threshold=150,
            ),
            "uv": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=6,
                warning_threshold=8,
                notes="Extended exposure; OSHA guidance applies",
            ),
            "temp_c": MetricPolicy(
                importance=MetricImportance.HIGH,
                caution_threshold=30,
                warning_threshold=35,
                notes="Heat illness prevention critical for outdoor work",
            ),
        },
        description="Extended outdoor occupational activity",
        health_note="OSHA heat illness prevention guidelines may apply",
    ),
}


def get_activity_policy(activity: str | None) -> ActivityPolicy | None:
    """Get the environmental policy for an activity type."""
    if not activity:
        return None
    try:
        at = ActivityType(activity.lower())
        return _ACTIVITY_POLICIES.get(at)
    except ValueError:
        # Unknown activity - return a conservative default
        return ActivityPolicy(
            activity=ActivityType.EXERCISE,
            is_outdoor=True,
            exertion_level="moderate",
            metrics={
                "aqi": MetricPolicy(
                    importance=MetricImportance.MEDIUM,
                    caution_threshold=100,
                    warning_threshold=150,
                ),
            },
            description="Unknown activity - using conservative defaults",
        )


def get_important_metrics(activity: str | None) -> list[str]:
    """Get the list of important metrics for an activity, sorted by importance."""
    policy = get_activity_policy(activity)
    if not policy:
        return ["aqi", "pm25", "uv", "temp_c"]
    
    # Sort metrics by importance (HIGH > MEDIUM > LOW)
    importance_order = {MetricImportance.HIGH: 0, MetricImportance.MEDIUM: 1, MetricImportance.LOW: 2}
    sorted_metrics = sorted(
        policy.metrics.items(),
        key=lambda x: importance_order.get(x[1].importance, 3)
    )
    return [m for m, _ in sorted_metrics]


def evaluate_observation_for_activity(
    obs: Observation, activity: str | None
) -> tuple[str | None, float]:
    """Evaluate an observation against activity policy.
    
    Returns:
        (severity, score) where score is 0-1 (0=ideal, 1=warning)
    """
    policy = get_activity_policy(activity)
    if not policy:
        return None, 0.0
    
    metric_policy = policy.metrics.get(obs.metric)
    if not metric_policy:
        return None, 0.0
    
    # Check thresholds
    if metric_policy.warning_threshold and obs.value >= metric_policy.warning_threshold:
        return "warning", 1.0
    if metric_policy.caution_threshold and obs.value >= metric_policy.caution_threshold:
        # Scale between caution and warning
        if metric_policy.warning_threshold:
            range_size = metric_policy.warning_threshold - metric_policy.caution_threshold
            score = min(1.0, (obs.value - metric_policy.caution_threshold) / range_size * 0.5 + 0.5)
        else:
            score = 0.5
        return "caution", score
    
    # Within acceptable range
    if metric_policy.ideal_range:
        low, high = metric_policy.ideal_range
        if low <= obs.value <= high:
            return "info", 0.0
    
    return "info", 0.0
