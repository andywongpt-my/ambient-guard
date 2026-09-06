# Ambient Guard — Requirements

Status: Draft v0.1 · Owner: Ambient Guard crew · Last updated: 2026-09-06

## 1. Product summary

Ambient Guard is a **Personal Environmental Agent powered by Bee**. It fuses personal
context captured by a Bee wearable (or Apple Watch running Bee) with real environmental
data (air quality, weather, UV, heat, optional pollen) to answer:

> "Given what the user is doing, where they are, when they plan to do it, and the
> environmental conditions around them, what should they know or consider doing?"

It is **not** a medical diagnosis system. Recommendations are informational / precautionary.

## 2. Actors

- **User** — owns a Bee device / Apple Watch running Bee; wants contextual guidance.
- **Bee CLI/MCP** — source of personal context (conversations, today summary, todos, location).
- **Environmental providers** — external APIs (air quality, weather, UV, pollen).
- **Ambient Guard backend** — reasoning + API.
- **Frontend** — demo UI (timeline + recommendation + evidence).

## 3. Functional requirements (EARS)

### FR-1 Bee context ingestion (Milestone 1 — highest priority)
- FR-1.1 WHEN the system requests current context, the Bee Integration Layer SHALL invoke
  the local Bee CLI (`bee today`, `bee search`, `bee locations current`) and return raw context.
- FR-1.2 WHERE the Bee CLI is not authenticated, the system SHALL surface an explicit
  "Bee not connected" error rather than silently returning empty context.
- FR-1.3 The system SHALL support both stdio MCP (`bee mcp serve`) and CLI-subprocess paths,
  selected by configuration.
- FR-1.4 The live demo path SHALL use real Bee data; mocks SHALL be confined to tests and
  local dev, gated behind an explicit `AMBIENT_GUARD_BEE_MODE=mock` flag.

### FR-2 Context normalization
- FR-2.1 WHEN raw Bee context is received, the system SHALL extract a structured
  `ContextIntent { activity, planned_time, location, intent_text, source_ref, confidence }`.
- FR-2.2 The system SHALL preserve `source_ref` (Bee conversation/summary id + timestamp) for traceability.
- FR-2.3 WHERE an attribute cannot be determined, the system SHALL mark it `null` with reduced
  confidence rather than inventing a value.

### FR-3 Environmental data retrieval
- FR-3.1 WHEN given a location and time window, the Environmental Layer SHALL retrieve
  PM2.5, PM10, AQI, UV index, temperature, humidity, weather, and (where available) pollen.
- FR-3.2 Each observation SHALL carry `source`, `observed_at`, `location`, `unit`, and a
  `kind` of `observed | forecast | estimate`.
- FR-3.3 WHEN a provider times out or returns malformed data, the system SHALL record the
  failure explicitly and continue with remaining providers (no silent hiding).
- FR-3.4 The system SHALL normalize units and attribute every value to its source.

### FR-4 Environmental reasoning
- FR-4.1 WHEN context + environmental observations are available, the Reasoning Engine SHALL
  produce a `Recommendation { text, reasoning_summary, evidence[], timestamps, confidence }`.
- FR-4.2 Every recommendation SHALL be supported by at least one retrieved evidence item; a
  recommendation with zero evidence SHALL NOT be emitted.
- FR-4.3 The reasoning output SHALL be explainable — a judge/user can see WHY.

### FR-5 Environmental timeline
- FR-5.1 The system SHALL produce a timeline of activities/locations with associated
  environmental conditions, labelled `observed | forecast | estimate | direct-measurement`.

### FR-6 API + UI
- FR-6.1 The backend SHALL expose a REST API returning context, environmental data,
  recommendation, evidence, and timeline for the hero scenario.
- FR-6.2 The UI SHALL present these five elements clearly for a sub-3-minute demo.

### FR-7 Exposure terminology
- FR-7.1 Absent a physical personal sensor, the system SHALL use "estimated environmental
  exposure" / "nearby environmental conditions" and SHALL NOT claim to have measured the
  exact air the user inhaled.

## 4. Non-functional requirements
- NFR-1 Privacy: data minimization — consume only Bee context needed for the decision; do
  not persist raw recordings, unrelated conversations, or full location history.
- NFR-2 Security: no secrets in repo; Bee HTTP MCP token ≥32 chars; providers keyed via env.
- NFR-3 Reliability: provider timeouts, retries, and fallbacks are explicit and tested.
- NFR-4 Observability: structured logs with source attribution; health checks.
- NFR-5 Reproducibility: live Bee integration demonstrable and captured under `evidence/`.
- NFR-6 Deployment: runs on the `meow` dedicated server via Docker Compose behind a reverse proxy.

## 5. Acceptance criteria (hero scenario)
Given Bee context "I plan to jog at 5 PM", the system SHALL:
1. Extract `activity=jogging`, `planned_time≈17:00`, and a relevant location from real Bee data.
2. Retrieve PM2.5/UV/temperature/humidity/weather for that location + time window with source attribution.
3. Produce one grounded recommendation with a reasoning summary and ≥1 evidence item.
4. Render context + conditions + recommendation + evidence + timeline in the UI.
5. Have the live Bee→recommendation path exercised end-to-end with captured evidence.

## 6. Out of scope for V1
Noise, indoor CO2/VOC, hyperlocal PM2.5, BLE sensors, smart-home actions. Documented as future work.

## 7. Open questions / risks (see docs/RISK_REGISTER.md)
- R1 Bee account/device availability for a live login on the dev machine and/or server.
- R2 Which environmental providers have free tiers with the needed coverage in the demo region.
- R3 Location fidelity from Bee (`bee locations current`) vs. user-supplied location fallback.
