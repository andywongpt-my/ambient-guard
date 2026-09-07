# Ambient Guard

**Your Personal Environmental Agent**

*Powered by real personal context from Bee.*

---

**Live demo:** [bee.andywongpt.com](https://bee.andywongpt.com)

---

## The Problem

Environmental information exists. Weather apps show conditions. AQI dashboards show pollution levels. But none of them know what you're planning to do.

You still have to manually interpret what the environment means for your own life.

## What Ambient Guard Does

Ambient Guard connects:

**Your plans (from Bee)**
**+ Environmental conditions (Open-Meteo / CAMS)**
**+ Timing**
**+ Personal constraints**

→ To answer: *"What should I do about the environment around my actual life?"*

### Example

Bee captures: **"Go jogging at 5 PM."**

Ambient Guard:
1. Extracts activity, time, and location from Bee
2. Retrieves PM2.5 / UV / temperature / humidity for that window
3. Evaluates nearby alternative time windows
4. Checks for personal conflicts
5. Produces one grounded recommendation with evidence

**Result:** *"Keep your planned time, but with caution. AQI 117 is unhealthy for sensitive groups. Take sensible precautions."*

## Why Bee Matters

**Bee understands your context.** It knows what you're planning, when, and where.

**Ambient Guard understands the environment.** It knows air quality, UV, temperature, and weather forecasts.

**Together:** Contextual environmental decisions.

This is fundamentally different from weather/AQI apps that show data without personal context.

## Demo

- **Duration:** Under 3 minutes
- **Shows:** Real Bee data → Environmental retrieval → Grounded recommendation
- **Script:** [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)
- **Recording plan:** [`docs/DEMO_RECORDING_PLAN.md`](docs/DEMO_RECORDING_PLAN.md)

## Architecture

```
Bee wearable/app
  ↓
Bee MCP (JSON-RPC)
  ↓
Context Normalizer (extracts activity, time, location)
  ↓
Environmental Layer (Open-Meteo weather + CAMS air quality)
  ↓
Reasoning Engine (materiality-aware, 8-state decision machine)
  ↓
Recommendation + Personal Environmental Timeline
  ↓
FastAPI backend → Vanilla JS frontend
```

**Key components:**
- `backend/app/bee/` — Bee MCP client, context normalizer
- `backend/app/environmental/` — Open-Meteo integration
- `backend/app/reasoning/` — Decision engine, personal feasibility
- `frontend/` — Decision-first UI

## How It Works

### 1. Bee Context Extraction

Ambient Guard reads active todos and recent conversations from Bee. It extracts:
- **Activity type** (e.g., "jogging" → outdoor activity)
- **Planned time** (e.g., "5 PM" → 17:00)
- **Location** (from Bee's location context)

### 2. Environmental Data Retrieval

For the planned time and location, Ambient Guard fetches:
- Temperature, humidity, wind, precipitation, weather code
- UV index
- PM2.5, PM10, ozone, NO2, AQI (US EPA)

All data is labelled as **forecast** vs **observation**, with attribution to Open-Meteo and CAMS.

### 3. Reasoning Engine

The engine:
- Evaluates a ±3h window around the planned time
- Applies **materiality threshold** (15% improvement required)
- Checks **personal feasibility** (6am-10pm constraint, conflicts with other Bee commitments)
- Runs an **8-state decision machine** (KEEP_PLANNED_TIME, CONSIDER_SHIFTING, etc.)

### 4. Recommendation Output

One clear decision:
- **KEEP_PLANNED_TIME** — No materially better window
- **CONSIDER_SHIFTING** — A better window exists
- **SHIFT_RECOMMENDED** — Strong environmental reason to change

Plus:
- Supporting environmental evidence
- Reason codes and limitations
- Personal Environmental Timeline

## Key Design Decisions

### Decision-First UI

The recommendation is the headline. Environmental metrics support it — not the other way around.

### Provenance Visible

Every data point shows:
- Source (Bee, Open-Meteo, CAMS)
- Fetch time
- Observation/forecast time
- Data kind (forecast vs observation)

### No Fake Sensors

Ambient Guard does **not** claim to measure personal PM2.5 exposure. Environmental data is location/model-based, transparently labelled.

### Controlled Abstention

If no materially better window exists, Ambient Guard preserves your plan. It doesn't force unnecessary recommendations.

## Privacy

- **No raw personal text persisted** — Context is normalized to structured fields
- **In-memory only** — Bee data is not stored beyond the session
- **Location fallback** — If Bee location is stale, system uses default with clear note
- **No authentication required** — Uses Bee session token on host, not user credentials

See [`docs/SECURITY_AND_PRIVACY.md`](docs/SECURITY_AND_PRIVACY.md).

## Environmental Data & Limitations

### Sources
- **Weather + UV:** Open-Meteo (CC BY 4.0)
- **Air quality:** CAMS Global via Open-Meteo API

### Limitations
- Air quality data is **CAMS Global 3-hourly native resolution** — hourly API values are interpolated
- Forecast data has inherent uncertainty
- Not a replacement for local monitoring stations in critical decisions

See [`docs/ENVIRONMENTAL_DATA_SOURCES.md`](docs/ENVIRONMENTAL_DATA_SOURCES.md).

## Running Locally

### Prerequisites
- Docker + Docker Compose
- (Optional) Bee CLI with `bee login` for live context

### Quick Start

```bash
# Clone
git clone https://github.com/andywongpt-my/ambient-guard.git
cd ambient-guard

# Configure
cp .env.example .env
# Edit .env — set AMBIENT_GUARD_BEE_MODE=mock for offline dev

# Run
docker compose up --build

# Health check
curl http://127.0.0.1:18080/health
```

### Live Bee Integration

For real Bee context:

```bash
# Install Bee CLI
npm install -g @beeai/cli

# Login
bee login

# Set environment
export AMBIENT_GUARD_BEE_MODE=cli
```

For production MCP setup, see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Testing

```bash
# Backend tests
docker compose exec backend pytest

# With coverage
docker compose exec backend pytest --cov=backend

# E2E (Playwright)
python scripts/run_e2e.py
```

**Status:** 44 passed / 1 skipped (G4 certification)

## Kiro Crew / AWS Builder

Ambient Guard was developed using **Kiro Crew** — an agent orchestration platform built on AWS.

### Kiro Crew Usage
- **Specs:** `.kiro/specs/ambient-guard/{requirements,design,tasks}.md`
- **Task Runner:** Autonomous implementation guided by specs
- **Sub-agents:** Parallel research and development tasks
- **Memory:** Persistent context across sessions
- **Friction log:** [`FRICTION_LOG.md`](FRICTION_LOG.md)

### Evidence
- [`docs/AWS_BUILDER_KIRO.md`](docs/AWS_BUILDER_KIRO.md) — Kiro Crew integration details
- `.kiro/` directory — Specs, session history, workspace configuration

## Hackathon Tracks

### Primary: Bee — Wearable AI
Real Bee MCP integration with live personal context affecting runtime decisions.

### Mini Challenge: AWS Builder
Kiro Crew (AWS-based agent platform) used for development orchestration.

### Mini Challenge: Open Source
- Repository: [github.com/andywongpt-my/ambient-guard](https://github.com/andywongpt-my/ambient-guard)
- License: MIT
- 27 PRs merged, fully documented, production-deployed

## Friction Log

Genuine platform friction encountered during development: [`FRICTION_LOG.md`](FRICTION_LOG.md)

Key entries:
- FR-001: Bee CLI headless login requires unlocked dbus session
- FR-007: `bee_search` server-side hang required best-effort fallback
- FR-008: No programmatic todo creation in Bee MCP (workaround: manual creation)

## Product Feedback

Detailed feedback on tools used: [`docs/PRODUCT_FEEDBACK.md`](docs/PRODUCT_FEEDBACK.md)

## License

[MIT](LICENSE)

---

**Ambient Guard — Your Personal Environmental Agent**

*Powered by real personal context from Bee.*
