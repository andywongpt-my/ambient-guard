# Milestone 1.2 — Bee data enters the app (sanitized)

Date: 2026-09-07 (Asia/Kuching) · Bee CLI @beeai/cli 0.7.3 · backend AMBIENT_GUARD_BEE_MODE=cli

## What this proves
Real Bee data reaches Ambient Guard through the FastAPI layer, not just the CLI.
`GET /api/v1/bee/context` calls the `CliBeeClient` which shells out to `bee ... --json`.

## Test run
```
$ AMBIENT_GUARD_BEE_MODE=cli pytest tests/test_bee_adapter.py::test_live_bee_ingress -s
1 passed in 3.31s
```

## Live payload returned by the app (via the API, token/id/precision redacted)
```json
{
  "location": {
    "id": "<REDACTED>",
    "latitude": 6.183, "longitude": 116.22,
    "address": "<REDACTED street>, Tuaran, Sabah, Malaysia",
    "created_at": "<epoch ms>", "updated_at": "<epoch ms>"
  },
  "age_ms": 43717,        // ~44s old — freshly live, not a fixture
  "is_recent": true,
  "recent_threshold_ms": 1800000,
  "timezone": "Asia/Kuching"
}
```
This differs from the M1_bee_login.md capture (which was ~1.6h stale) — confirming a
live call each time, not cached data.

## Full suite (mock mode, CI-safe)
```
$ AMBIENT_GUARD_BEE_MODE=mock pytest -q
7 passed, 1 skipped   # live test skipped without a Bee login
```
Failure-path coverage: CLI-not-found, non-JSON output, and not-logged-in all raise
BeeError (surfaced as HTTP 502), never silent empty context.
