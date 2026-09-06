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
- [ ] 1.3 (M1) Bee adapter `mcp` backend (stdio) as alternate path
- [x] 1.4 (M1) `mock` backend + fixtures (real shapes), gated by AMBIENT_GUARD_BEE_MODE; failure-path tests (not-found/bad-json/not-logged-in)
- [x] 1.5 (M1) Integration test proving real Bee data enters the app pipeline (test_live_bee_ingress, cli mode); evidence in evidence/M1_bee_ingress.md
- [ ] 1.6 (M1) DO NOT mark done until live integration demonstrated + evidence stored

## Milestone 2 — Environmental data layer
- [ ] 2.1 (M2) Provider protocol + Observation model
- [ ] 2.2 (M2) Open-Meteo weather+UV provider (no key)
- [ ] 2.3 (M2) Air-quality provider (Open-Meteo air-quality / OpenAQ) — PM2.5/PM10/AQI/O3/NO2
- [ ] 2.4 (M2) Cross-cutting: timeout, retry, validation, unit normalization, source attribution, cache
- [ ] 2.5 (M2) Failure-path tests (timeout, malformed, rate-limit) — failures surfaced not hidden

## Milestone 3 — Context normalization
- [x] 3.1 (M3) ContextIntent extraction (activity/time/location/intent) with source_ref + confidence — GET /api/v1/context
- [x] 3.2 (M3) Traceability (notes + source_ref) + no unsupported inference; 16 tests incl. hero scenario + live verify

## Milestone 4 — Reasoning engine
- [ ] 4.1 (M4) Threshold rules (AQI/UV/heat/PM2.5) → candidate concerns
- [ ] 4.2 (M4) Recommendation synthesis with mandatory evidence linkage + guardrail (≥1 evidence)
- [ ] 4.3 (M4) Explainability output; reasoning tests

## Milestone 5 — Environmental timeline
- [ ] 5.1 (M5) Timeline builder labelling observed/forecast/estimate/direct-measurement

## Milestone 6 — UX
- [ ] 6.1 (M6) Next.js demo screen: context · conditions · recommendation · evidence · timeline
- [ ] 6.2 (M6) Wire to /api/v1/assess + /api/v1/timeline

## Milestone 7 — Reliability
- [ ] 7.1 (M7) Complete unit/integration/failure/E2E suites; security + privacy review

## Milestone 8 — Competition readiness
- [ ] 8.1 (M8) Public repo, license, README, ARCHITECTURE, compliance matrix, feedback, friction log
- [ ] 8.2 (M8) Demo script + evidence + sub-3-minute demo plan

## First vertical slice (spans M1–M4)
REAL BEE DATA → CONTEXT EXTRACTION → ENVIRONMENTAL DATA → REASONING → ONE GROUNDED RECOMMENDATION
Target: `POST /api/v1/assess` returns a grounded recommendation from real Bee context.
