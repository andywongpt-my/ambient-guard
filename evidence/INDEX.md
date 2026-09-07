# Ambient Guard — Evidence Index

A single map of captured evidence to the milestone / competition claim it supports.
All evidence is sanitized (tokens redacted, addresses/coords coarsened).

| Evidence | Milestone / Claim | What it proves |
|----------|-------------------|----------------|
| [`evidence/M1_bee_login.md`](M1_bee_login.md) | M1.1 · Bee live login | `@beeai/cli` 0.7.3 installed; `bee login` verified as Andy Wong (id 50853); `bee today`/`locations current` return real data |
| [`evidence/M1_bee_ingress.md`](M1_bee_ingress.md) | M1.2 · Real Bee data enters the app | `GET /api/v1/bee/context` returns live location (fresh `age_ms`) via the cli backend; failure paths raise, never silent-empty |
| [`evidence/M3_context_normalization.md`](M3_context_normalization.md) | M3 · Context normalization | Live Bee context → ContextIntent; no-inference guarantee shown (activity/time honestly null when absent) |
| [`evidence/M4_reasoning_slice.md`](M4_reasoning_slice.md) | M4 · Reasoning + closed slice | Hero recommendation with 3 source-attributed evidence items; ≥1-evidence guardrail; not-medical framing |
| [`evidence/screenshots/M6_demo_ui.png`](screenshots/M6_demo_ui.png) | M6 · Demo UI | Full-page render of all 5 panels (context, conditions, recommendation, evidence, timeline) |
| [`evidence/screenshots/M6_demo_flow.gif`](screenshots/M6_demo_flow.gif) / `.mp4` | M6 · Demo flow (local) | Interactive flow: load → assess → scroll → intent override → re-assess |
| [`evidence/screenshots/M6_demo_flow_live.gif`](screenshots/M6_demo_flow_live.gif) / `.mp4` | M6 · Demo flow (LIVE) | Same flow against `bee.andywongpt.com` in `bee_mode=mcp` — real Bee location + live Open-Meteo |
| [`evidence/M6_demo_ui.md`](M6_demo_ui.md) | M6 · Captions | Describes the screenshots/GIFs and how they were produced (`scripts/shot.py`, `scripts/record.py`) |
| [`evidence/M7_reliability_security_privacy.md`](M7_reliability_security_privacy.md) | M7 · Reliability/security/privacy | 44 passed/1 skipped (+ live); security + privacy findings (no secrets, no persistence) |

## Live proof (not a file — verify anytime)
- **Public URL:** [bee.andywongpt.com](https://bee.andywongpt.com) — `POST /api/v1/assess` returns
  `bee_mode=mcp`, `activity=jogging` (from real Bee todo id 28703772), grounded recommendation
  with `open-meteo` evidence. This is the primary-track proof: REAL Bee → context → environment → recommendation.

## Reproduce
```bash
# UI screenshot
python scripts/shot.py <out-dir> https://bee.andywongpt.com/
# demo GIF
python scripts/record.py <out-dir> https://bee.andywongpt.com/   # then ffmpeg palettegen -> gif
# tests
AMBIENT_GUARD_BEE_MODE=mock pytest -q          # 44 passed, 1 skipped
AMBIENT_GUARD_BEE_MODE=cli  pytest -q tests/test_bee_adapter.py::test_live_bee_ingress
```
