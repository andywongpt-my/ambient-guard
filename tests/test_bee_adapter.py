"""Bee integration layer tests.

- Mock-backend tests run everywhere (CI-safe).
- The live test runs ONLY when AMBIENT_GUARD_BEE_MODE=cli AND `bee` is on PATH,
  so CI stays green without a Bee login while a dev host can prove real ingress.
"""
from __future__ import annotations

import json
import os
import shutil

import pytest
from fastapi.testclient import TestClient

from app.bee import BeeError, get_bee_client
from app.bee.client import CliBeeClient, MockBeeClient
from app.main import app


@pytest.fixture(autouse=True)
def _mock_mode(monkeypatch):
    # Default every test to mock mode; the live test overrides explicitly.
    monkeypatch.setenv("AMBIENT_GUARD_BEE_MODE", "mock")


def test_factory_selects_backends(monkeypatch):
    monkeypatch.setenv("AMBIENT_GUARD_BEE_MODE", "mock")
    assert isinstance(get_bee_client(), MockBeeClient)
    assert isinstance(get_bee_client("cli"), CliBeeClient)
    with pytest.raises(BeeError):
        get_bee_client("mcp")           # reserved, not yet implemented
    with pytest.raises(BeeError):
        get_bee_client("bogus")


def test_mock_context_endpoint_returns_real_shape():
    client = TestClient(app)
    r = client.get("/api/v1/bee/context", params={"query": "jog"})
    assert r.status_code == 200
    body = r.json()
    assert body["bee_mode"] == "mock"
    # today-context carries the hero jog utterance
    convs = body["today_context"]["recentConversations"]
    assert any("jog" in (c.get("short_summary") or "").lower() for c in convs)
    # location shape is present and typed
    assert body["current_location"]["location"]["latitude"] == pytest.approx(6.183)
    assert body["current_location"]["is_recent"] is True
    # search returned a hit
    assert body["search"]["results"][0]["short_summary"].lower().startswith("andy plans to jog")


def test_cli_backend_not_found_raises(monkeypatch):
    # A CLI client pointed at a missing binary must raise BeeError, not hang.
    c = CliBeeClient(bee_bin="definitely-not-a-real-bee-binary-xyz")
    with pytest.raises(BeeError, match="not found"):
        c.today_context()


def test_cli_backend_bad_json_raises(monkeypatch, tmp_path):
    # Simulate a `bee` that prints non-JSON: adapter must raise, not crash.
    class _Proc:
        returncode = 0
        stdout = "not json at all"
        stderr = ""

    def fake_run(*a, **k):
        return _Proc()

    monkeypatch.setattr("app.bee.client.shutil.which", lambda _b: "/fake/bee")
    monkeypatch.setattr("app.bee.client.subprocess.run", fake_run)
    with pytest.raises(BeeError, match="non-JSON"):
        CliBeeClient().today_context()


def test_cli_backend_not_logged_in_raises(monkeypatch):
    class _Proc:
        returncode = 1
        stdout = ""
        stderr = "Not logged in."

    monkeypatch.setattr("app.bee.client.shutil.which", lambda _b: "/fake/bee")
    monkeypatch.setattr("app.bee.client.subprocess.run", lambda *a, **k: _Proc())
    with pytest.raises(BeeError, match="not authenticated"):
        CliBeeClient().today_context()


@pytest.mark.skipif(
    os.getenv("AMBIENT_GUARD_BEE_MODE") != "cli" or shutil.which("bee") is None,
    reason="live Bee test: set AMBIENT_GUARD_BEE_MODE=cli with `bee login` done",
)
def test_live_bee_ingress(monkeypatch):
    monkeypatch.setenv("AMBIENT_GUARD_BEE_MODE", "cli")
    client = TestClient(app)
    r = client.get("/api/v1/bee/context")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["bee_mode"] == "cli"
    # Real location payload must carry the is_recent / age_ms envelope fields.
    loc = body["current_location"]
    assert "is_recent" in loc and "age_ms" in loc
    print("LIVE bee context:", json.dumps(body["current_location"], indent=2)[:400])
