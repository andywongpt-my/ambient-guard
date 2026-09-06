"""Reasoning engine (M4) + full /api/v1/assess vertical-slice tests."""
from __future__ import annotations

from datetime import datetime

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.agent.models import ContextIntent, SourceRef
from app.agent.reasoning import ReasoningEngine, ReasoningError
from app.environmental.base import Observation, ObservationSource
from app.environmental.open_meteo import _AIR_URL, _FORECAST_URL
from app.main import app

NOW = datetime(2026, 9, 7, 12, 0, 0)


def _obs(metric, value, unit="x", kind="forecast"):
    return Observation(metric=metric, value=value, unit=unit, kind=kind,
                       source=ObservationSource(provider="open-meteo", fetched_at=NOW))


def _intent(activity="jogging", conf=0.9):
    return ContextIntent(activity=activity, planned_time=NOW.replace(hour=17),
                         intent_text="jog at 5 PM",
                         source_ref=SourceRef(provider="bee"), confidence=conf)


def test_warning_when_aqi_and_uv_high():
    obs = [_obs("aqi", 165, "AQI"), _obs("uv", 8, "index"), _obs("temp_c", 33, "°C")]
    a = ReasoningEngine().assess(_intent(), obs)
    assert len(a.recommendation.evidence) >= 1
    assert any(e.severity == "warning" for e in a.recommendation.evidence)
    assert "reschedul" in a.recommendation.text.lower() or "indoor" in a.recommendation.text.lower()
    assert "not medical" in a.recommendation.reasoning_summary.lower()


def test_all_clear_still_has_evidence_guardrail():
    # Nothing trips a threshold -> still >=1 evidence (reassuring readings).
    obs = [_obs("aqi", 20, "AQI"), _obs("uv", 2, "index"), _obs("temp_c", 24, "°C")]
    a = ReasoningEngine().assess(_intent(), obs)
    assert len(a.recommendation.evidence) >= 1
    assert all(e.severity == "info" for e in a.recommendation.evidence)
    assert "acceptable" in a.recommendation.text.lower()


def test_no_observations_refuses():
    with pytest.raises(ReasoningError):
        ReasoningEngine().assess(_intent(), [])


def test_caution_tier():
    obs = [_obs("pm25", 40, "µg/m³"), _obs("uv", 6, "index")]
    a = ReasoningEngine().assess(_intent(), obs)
    sevs = {e.severity for e in a.recommendation.evidence}
    assert "caution" in sevs and "warning" not in sevs


@respx.mock
def test_full_assess_slice_mock(monkeypatch):
    monkeypatch.setenv("AMBIENT_GUARD_BEE_MODE", "mock")  # mock Bee -> hero jog fixture
    respx.get(_FORECAST_URL).mock(return_value=httpx.Response(200, json={
        "hourly": {"time": ["2026-09-07T17:00"], "temperature_2m": [33.0],
                   "relative_humidity_2m": [70], "uv_index": [8.0], "weather_code": [2]}}))
    respx.get(_AIR_URL).mock(return_value=httpx.Response(200, json={
        "hourly": {"time": ["2026-09-07T17:00"], "pm2_5": [60.0], "us_aqi": [165]}}))
    r = TestClient(app).post("/api/v1/assess", json={})
    assert r.status_code == 200, r.text
    a = r.json()["assessment"]
    assert a["context"]["activity"] == "jogging"
    assert len(a["recommendation"]["evidence"]) >= 1          # guardrail
    assert a["recommendation"]["text"]
    assert any(o["metric"] == "aqi" for o in a["observations"])
