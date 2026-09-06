# Ambient Guard — Design

Status: Draft v0.1 · Last updated: 2026-09-06

## 1. Architecture overview

```
Apple Watch + Bee
   │  (real personal context)
   ▼
Bee CLI / MCP  ──►  Bee Integration Layer  ──►  Context Normalization Layer
                                                        │
Environmental providers                                 │  ContextIntent
  Air-quality (OpenAQ / provider)  ─┐                    ▼
  Weather (Open-Meteo)             ─┼──►  Environmental Layer  ──►  Reasoning Engine
  UV (Open-Meteo air-quality)      ─┤        (normalized obs)          │
  Pollen (optional)                ─┘                                   ▼
                                                          Recommendation + Timeline
                                                                     │
                                                            FastAPI  ──►  React/Next UI
```

The Bee path (left) is the competition-critical spine and is built first (Milestone 1).

## 2. Component design

### 2.1 Bee Integration Layer (`bee/`)
- Adapter with two backends selected by `AMBIENT_GUARD_BEE_MODE`:
  - `cli` (default live): shells out to the local `bee` CLI (`bee today`, `bee search --json`,
    `bee locations current`). Parses JSON output.
  - `mcp`: talks to `bee mcp serve` (stdio) or `serve-http` (127.0.0.1 + bearer token).
  - `mock`: fixture-backed, **tests/dev only**, gated by explicit env value.
- Never persists raw Bee payloads; passes through to normalization and discards.
- Auth relies on prior `bee login` on the host (no token stored in the app for stdio/CLI).

### 2.2 Context Normalization Layer (`agent/context/`)
- Input: raw Bee context. Output: `ContextIntent`.
- Extraction strategy: rule/keyword pass first (activity verbs, time expressions), LLM-assisted
  extraction optional and clearly bounded. Every field keeps `source_ref` + `confidence`.

### 2.3 Environmental Layer (`environmental/`)
- `Provider` protocol: `fetch(location, window) -> list[Observation]`.
- Concrete providers (V1 default, free tiers, no key where possible):
  - **Open-Meteo** weather + air-quality + UV (`https://open-meteo.com`) — no API key, generous free tier.
  - **OpenAQ** (`https://openaq.org`) as an air-quality cross-source (optional).
  - Pollen: Open-Meteo pollen endpoint where region-supported.
- Cross-cutting: timeout, retry-with-backoff, response validation, source attribution,
  unit normalization, optional short TTL cache. Failures recorded, never hidden.

### 2.4 Reasoning Engine (`agent/reasoning/`)
- Deterministic rule scaffold + LLM synthesis. Thresholds (AQI/UV/heat) drive candidate
  concerns; the engine assembles `Recommendation` with mandatory evidence linkage.
- Guardrail: refuses to emit a recommendation lacking evidence (FR-4.2).

### 2.5 API (`backend/`)
FastAPI. Endpoints:
- `GET  /health` → liveness/readiness (+ Bee connectivity probe).
- `POST /api/v1/assess` → body `{ location?, time?, intent_override? }`; pulls Bee context if
  not overridden, runs the full pipeline, returns the assessment object below.
- `GET  /api/v1/timeline` → environmental timeline for the day.

### 2.6 Frontend (`frontend/`)
Next.js. Single demo screen: Bee context card · conditions · recommendation · evidence · timeline.

## 3. Data models (Pydantic)

```python
class SourceRef(BaseModel):
    provider: str            # "bee" | "open-meteo" | ...
    ref_id: str | None
    observed_at: datetime
    location: str | None

class ContextIntent(BaseModel):
    activity: str | None
    planned_time: datetime | None
    location: str | None
    intent_text: str
    source_ref: SourceRef
    confidence: float        # 0..1

class Observation(BaseModel):
    metric: str              # "pm25" | "aqi" | "uv" | "temp_c" | "humidity" | ...
    value: float
    unit: str
    kind: Literal["observed", "forecast", "estimate", "direct-measurement"]
    source: SourceRef

class Evidence(BaseModel):
    observation: Observation
    note: str

class Recommendation(BaseModel):
    text: str
    reasoning_summary: str
    evidence: list[Evidence]     # len >= 1 enforced
    timestamps: dict[str, datetime]
    confidence: float

class Assessment(BaseModel):
    context: ContextIntent
    observations: list[Observation]
    recommendation: Recommendation
    timeline: list[TimelineEntry]
    provider_errors: list[str]   # explicit, not hidden
```

## 4. Configuration
- `AMBIENT_GUARD_BEE_MODE = cli | mcp | mock`
- `AMBIENT_GUARD_BEE_HTTP_TOKEN` (only for mcp-http)
- `AMBIENT_GUARD_DEFAULT_LOCATION` (fallback when Bee location unavailable — R3)
- Provider keys via env; none committed. `.env.example` documents all keys.

## 5. Deployment (meow server)
- `docker-compose.yml`: `backend` (FastAPI/uvicorn), `db` (Postgres), `frontend`, optional `worker`.
- Reverse proxy: **nginx** (already installed on meow) OR a Caddy container. Chosen: reuse the
  server's existing nginx as the TLS terminator, proxy to the compose network on a dedicated
  upstream port to avoid colliding with the ~10 containers already running.
- Health checks + `restart: unless-stopped` + json-file log rotation.
- Bee CLI must be installed + `bee login` completed on the host that runs the `cli`/`mcp` backend.
  Deployment note (R1): if the server cannot hold a Bee login, the live backend runs on the dev
  host and the server hosts the UI + a recorded/live-proxied assessment — decision tracked in RISK_REGISTER.

## 6. Testing strategy
- Unit: normalization, each provider (mocked HTTP), reasoning thresholds, evidence guardrail.
- Integration: Bee adapter against recorded fixtures; provider layer against VCR-style cassettes.
- Failure-path: provider timeout, malformed JSON, Bee-not-connected.
- E2E: full hero scenario (`mock` in CI, live run captured to `evidence/` for the demo).
