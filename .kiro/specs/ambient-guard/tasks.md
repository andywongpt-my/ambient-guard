# Ambient Guard — Tasks

Status: Draft v0.1 · Last updated: 2026-09-06
Legend: [ ] todo · [~] in progress · [x] done · (M#) milestone

## Milestone 0 — Repository baseline
- [x] 0.1 (M0) Repo skeleton (backend/frontend/bee/environmental/agent/tests/docs/evidence/scripts)
- [x] 0.2 (M0) Kiro specs: requirements.md, design.md, tasks.md
- [x] 0.3 (M0) Docs skeleton: ARCHITECTURE, DEMO_PLAN, COMPETITION_COMPLIANCE, PRODUCT_FEEDBACK, SECURITY_AND_PRIVACY, RISK_REGISTER
- [x] 0.4 (M0) FRICTION_LOG.md, README.md, LICENSE (MIT/Apache-2.0), .gitignore, .env.example
- [x] 0.5 (M0) Python project: requirements + requirements-dev, pytest.ini, ruff; scripts/test.sh; 2 tests green
- [x] 0.6 (M0) docker-compose.yml baseline (backend + db) with health checks + restart policy + log rotation; non-conflicting host ports for meow
- [x] 0.7 (M0) git init + first commit (bea2328). Push to a feature branch once a GitHub remote is created.

## Milestone 1 — Live Bee integration (HIGHEST PRIORITY)
- [x] 1.1 (M1) Install Bee CLI (@beeai/cli 0.7.3) on dev host; `bee login` verified as Andy Wong (id 50853); sanitized evidence in evidence/M1_bee_login.md
- [x] 1.2 (M1) Bee adapter `cli` backend: `bee today --context`, `bee search --query`, `bee locations current` (all --json); wired to GET /api/v1/bee/context
- [x] 1.3 (M1) Bee adapter `mcp` backend: JSON-RPC 2.0 over HTTP to `bee mcp serve-http` (bee_get_today/bee_get_current_location/bee_search); 4 respx tests
- [x] 1.4 (M1) `mock` backend + fixtures (real shapes), gated by AMBIENT_GUARD_BEE_MODE; failure-path tests (not-found/bad-json/not-logged-in)
- [x] 1.5 (M1) Integration test proving real Bee data enters the app pipeline (test_live_bee_ingress, cli mode); evidence in evidence/M1_bee_ingress.md
- [ ] 1.6 (M1) DO NOT mark done until live integration demonstrated + evidence stored

## Milestone 2 — Environmental data layer
- [x] 2.1 (M2) Provider protocol + Observation model (metric/value/unit/kind/source)
- [x] 2.2 (M2) Open-Meteo weather+UV provider (no key) — temp/humidity/wind/precip/uv/weather_code
- [x] 2.3 (M2) Open-Meteo air-quality — PM2.5/PM10/O3/NO2/US-AQI
- [x] 2.4 (M2) Cross-cutting: timeout, retry, validation, unit normalization, source attribution, TTL cache; GET /api/v1/environment
- [x] 2.5 (M2) Failure-path tests (timeout, malformed, missing-metric skip, error surfacing, cache) — 6 tests, respx-mocked

## Milestone 3 — Context normalization
- [x] 3.1 (M3) ContextIntent extraction (activity/time/location/intent) with source_ref + confidence — GET /api/v1/context
- [x] 3.2 (M3) Traceability (notes + source_ref) + no unsupported inference; 16 tests incl. hero scenario + live verify

## Milestone 4 — Reasoning engine
- [x] 4.1 (M4) Threshold rules (AQI/UV/heat/PM2.5/PM10) → tiered evidence (caution/warning)
- [x] 4.2 (M4) Recommendation synthesis with mandatory evidence linkage + guardrail (≥1 evidence; refuses with 0 obs)
- [x] 4.3 (M4) Explainability (reasoning_summary + per-evidence notes); 5 reasoning tests

## First vertical slice (spans M1–M4) — CLOSED
- [x] POST /api/v1/assess: Bee → ContextIntent → environment → one grounded recommendation (evidence/M4_reasoning_slice.md)

## Milestone 5 — Environmental timeline
- [x] 5.1 (M5) Timeline builder (app/agent/timeline.py): per-entry data_kind (observed|forecast from the observation) + exposure_kind (estimate|direct-measurement), planned-hour marking; GET /api/v1/timeline?planned=; UI shows Data/Exposure columns + planned row. 3 tests.

## Milestone 6 — UX
- [x] 6.1 (M6) Zero-build single-page demo UI (backend/static/index.html): 5 panels — context · conditions · recommendation · evidence · timeline. Served at GET / and /ui.
- [x] 6.2 (M6) Wired to POST /api/v1/assess + GET /api/v1/timeline; CORS enabled. (Next.js rewrite deferred — static UI chosen for a zero-dependency, memory-safe demo; upgrade path noted in design.md.)

## Milestone 7 — Reliability
- [x] 7.1 (M7) Full suite 44 passed/1 skipped (+ live Bee test passes); failure/timeout/malformed/E2E covered; security + privacy review done (evidence/M7_reliability_security_privacy.md). Findings: no secrets, no logging of sensitive data, NO persistence of Bee data; 2 non-blocking notes (CORS *, unused DB).

## Milestone 8 — Competition readiness
- [x] 8.1 (M8) Public repo + MIT license + README + ARCHITECTURE; compliance matrix finalized (all 3 tracks Met, Task Runner honestly marked N/A); PRODUCT_FEEDBACK completed; FRICTION_LOG FR-001–007
- [x] 8.2 (M8) Demo script reconciled to the live product; evidence/INDEX.md maps all evidence; live site verified (bee_mode=mcp)

## First vertical slice (spans M1–M4)
REAL BEE DATA → CONTEXT EXTRACTION → ENVIRONMENTAL DATA → REASONING → ONE GROUNDED RECOMMENDATION
Target: `POST /api/v1/assess` returns a grounded recommendation from real Bee context.
