from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "bee_mode" in body


def test_assess_stub_echoes():
    r = client.post("/api/v1/assess", json={"intent_override": "jog at 5 PM"})
    assert r.status_code == 200
    body = r.json()
    assert body["stub"] is True
    assert body["echo"]["intent_override"] == "jog at 5 PM"
