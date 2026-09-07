"""Context normalization (M3) tests."""
from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.agent.normalize import _extract_activity, _extract_time, normalize
from app.bee.models import (
    BeeConversation,
    BeeCurrentLocation,
    BeeLocation,
    BeeSearchResult,
    BeeTodayContext,
)
from app.main import app

NOW = datetime(2026, 9, 7, 12, 0, 0)  # noon, so "5 PM" is later today


def _today(summary: str, cid: int = 1) -> BeeTodayContext:
    return BeeTodayContext(
        recentConversations=[BeeConversation(id=cid, summary=summary, short_summary=summary)]
    )


def _loc(lat=6.18, lon=116.22, recent=True, addr="Tuaran, Sabah", updated=1788700000000):
    return BeeCurrentLocation(
        location=BeeLocation(id=1, latitude=lat, longitude=lon, address=addr, updated_at=updated),
        age_ms=60000 if recent else 5_000_000,
        is_recent=recent,
        recent_threshold_ms=1_800_000,
    )


# --- activity ---------------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("I plan to jog at 5 PM", "jogging"),
    ("going for a run later", "running"),
    ("cycling this evening", "cycling"),
    ("morning walk", "walking"),
    ("just reading a book", None),
])
def test_activity_extraction(text, expected):
    activity, _ = _extract_activity(text)
    assert activity == expected


# --- time -------------------------------------------------------------------
def test_time_12h_pm():
    assert _extract_time("jog at 5 PM", NOW) == NOW.replace(hour=17, minute=0)


def test_time_24h():
    assert _extract_time("run at 17:30", NOW) == NOW.replace(hour=17, minute=30)


def test_time_rolls_to_tomorrow_when_past():
    # 6 AM already passed at noon -> next day
    got = _extract_time("jog at 6 AM", NOW)
    assert got.day == NOW.day + 1 and got.hour == 6


def test_time_relative_hours():
    assert _extract_time("jogging in 2 hours", NOW) == NOW.replace(hour=14)


def test_time_absent():
    assert _extract_time("go jogging sometime", NOW) is None


# --- location (R3) ----------------------------------------------------------
def test_location_recent_used():
    intent = normalize(_today("jog at 5 PM"), _loc(recent=True), now=NOW)
    assert intent.location == "Tuaran, Sabah"
    assert intent.location_is_recent is True
    assert intent.latitude == pytest.approx(6.18)


def test_location_stale_falls_back():
    intent = normalize(_today("jog at 5 PM"), _loc(recent=False), now=NOW,
                        default_location="Kota Kinabalu")
    assert intent.location == "Kota Kinabalu"
    assert intent.location_is_recent is False
    assert any("stale" in n for n in intent.notes)


def test_location_stale_no_fallback_stays_none():
    intent = normalize(_today("jog at 5 PM"), _loc(recent=False), now=NOW, default_location=None)
    assert intent.location is None


def test_default_location_coords_when_no_bee_location():
    # No Bee location at all + "lat,lon" fallback -> coords flow (so assess can run).
    from app.bee.models import BeeCurrentLocation
    empty_loc = BeeCurrentLocation(location=None, is_recent=False)
    intent = normalize(_today("jog at 5 PM"), empty_loc, now=NOW, default_location="6.183,116.22")
    assert intent.location == "6.183,116.22"
    assert intent.latitude == pytest.approx(6.183)
    assert intent.longitude == pytest.approx(116.22)


def test_default_location_coords_when_bee_stale():
    intent = normalize(_today("jog at 5 PM"), _loc(recent=False), now=NOW, default_location="1.5,103.6")
    assert intent.latitude == pytest.approx(1.5)
    assert intent.longitude == pytest.approx(103.6)


# --- no unsupported inference (FR-2.3) --------------------------------------
def test_no_inference_when_context_empty():
    intent = normalize(BeeTodayContext(), _loc(recent=True), now=NOW, default_location=None)
    assert intent.activity is None
    assert intent.planned_time is None
    assert intent.intent_text == ""
    assert intent.confidence < 0.3


# --- hero scenario ----------------------------------------------------------
def test_hero_scenario_full_extraction():
    search = BeeSearchResult(results=[{"id": 42, "short_summary": "Andy plans to jog at 5 PM."}])
    intent = normalize(_today("unrelated", cid=1), _loc(recent=True), search, now=NOW)
    assert intent.activity == "jogging"
    assert intent.planned_time == NOW.replace(hour=17, minute=0)
    assert intent.location == "Tuaran, Sabah"
    assert intent.source_ref.ref_id == "42"        # search hit wins over conversation
    assert intent.confidence >= 0.9                # intent+activity+time+location
    assert intent.source_ref.provider == "bee"


def test_active_todo_as_intent_source_with_alarm():
    # No conversation/search intent; a real Bee todo "Go jogging at 5 PM" with an
    # alarm_at drives both activity and planned_time.
    from datetime import timezone
    alarm_ms = int(datetime(2026, 9, 7, 17, 0, tzinfo=timezone.utc).timestamp() * 1000)
    today = BeeTodayContext(activeTodos=[{"id": 99, "text": "Go jogging at 5 PM", "alarm_at": alarm_ms}])
    intent = normalize(today, _loc(recent=True), now=NOW)
    assert intent.activity == "jogging"
    assert intent.planned_time is not None
    assert intent.source_ref.ref_id == "99"
    assert any("todo alarm" in n or "planned_time parsed" in n for n in intent.notes)


# --- endpoint (mock mode) ---------------------------------------------------
def test_context_endpoint_mock(monkeypatch):
    monkeypatch.setenv("AMBIENT_GUARD_BEE_MODE", "mock")
    r = TestClient(app).get("/api/v1/context")
    assert r.status_code == 200
    ctx = r.json()["context"]
    assert ctx["activity"] == "jogging"
    assert ctx["source_ref"]["provider"] == "bee"
    assert ctx["confidence"] > 0
