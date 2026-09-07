"""Environmental timeline builder (M5) tests."""
from __future__ import annotations

from datetime import datetime

from app.agent.timeline import build_timeline
from app.environmental.base import Observation, ObservationSource

NOW = datetime(2026, 9, 7, 12, 0, 0)


def _obs(metric, value, kind, provider="open-meteo"):
    return Observation(metric=metric, value=value, unit="x", kind=kind,
                       source=ObservationSource(provider=provider, fetched_at=NOW))


def _fake_observe(lat, lon, when=None):
    # observed for the current/first hour, forecast for future hours
    kind = "observed" if when and when <= NOW else "forecast"
    return [_obs("aqi", 100, kind), _obs("uv", 5, kind), _obs("temp_c", 30, kind),
            _obs("pm25", 20, kind)], []


def test_timeline_labels_and_length():
    entries = build_timeline(_fake_observe, 6.18, 116.22, hours=4, now=NOW)
    assert len(entries) == 5                       # hours+1
    assert entries[0].data_kind == "observed"      # h=0 at NOW
    assert entries[1].data_kind == "forecast"      # future hour
    # all API-based -> estimate exposure, never direct-measurement
    assert all(e.exposure_kind == "estimate" for e in entries)
    assert entries[0].sources == ["open-meteo"]


def test_timeline_marks_planned_hour():
    planned = NOW.replace(hour=15)                 # 3h ahead
    entries = build_timeline(_fake_observe, 6.18, 116.22, hours=6, now=NOW, planned_time=planned)
    marked = [e for e in entries if e.is_planned]
    assert len(marked) == 1
    assert marked[0].time.hour == 15


def test_direct_measurement_when_sensor_source():
    def sensor_observe(lat, lon, when=None):
        return [_obs("pm25", 12, "direct-measurement", provider="ble-sensor")], []
    entries = build_timeline(sensor_observe, 6.18, 116.22, hours=1, now=NOW)
    assert entries[0].exposure_kind == "direct-measurement"
