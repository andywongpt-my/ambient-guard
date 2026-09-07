# Ambient Guard — Devpost Submission Draft

## Project Name

Ambient Guard

## Tagline

Your Personal Environmental Agent — Powered by real personal context from Bee.

---

## Project Description

### Inspiration

Environmental information is everywhere. Weather apps show conditions. AQI dashboards show pollution levels. UV indices warn about sun exposure.

But none of them know what you're planning to do.

You see the numbers, but you still have to interpret what they mean for your own life:

*"Is 5 PM a good time for my jog?"*
*"Should I shift my outdoor task to tomorrow?"*
*"What do these conditions mean for my kid's soccer practice?"*

Ambient Guard was built to answer that question automatically — by connecting your plans (from Bee) with environmental conditions (from Open-Meteo and CAMS).

### What It Does

Ambient Guard is a **Personal Environmental Agent** that:

1. **Reads your plans from Bee** — Active todos, recent conversations, and location context
2. **Retrieves environmental conditions** — Temperature, UV, PM2.5, AQI, humidity, weather for your planned time and location
3. **Evaluates alternatives** — Checks nearby time windows for materially better conditions
4. **Checks personal feasibility** — Ensures recommendations respect your constraints (no "go jogging at midnight" suggestions)
5. **Delivers one clear decision** — KEEP PLANNED TIME, CONSIDER SHIFTING, or SHIFT RECOMMENDED — with supporting evidence

**Example:**

Bee captures: *"Go jogging at 5 PM."*

Ambient Guard:
- Extracts: jogging (outdoor activity), 17:00, your location
- Fetches: AQI 117, PM2.5 26 µg/m³, UV 2.2, temp 29.8°C
- Evaluates: ±3h window, no materially better time
- Returns: **"Keep your planned time, but with caution. AQI 117 is unhealthy for sensitive groups. Take sensible precautions."**

### How We Built It

**Architecture:**

```
Bee wearable/app → Bee MCP (JSON-RPC) → Context Normalizer
                                              ↓
Open-Meteo / CAMS → Environmental Layer
                                              ↓
                                    Reasoning Engine
                                              ↓
                                    Recommendation + Timeline
                                              ↓
                                    FastAPI → Vanilla JS UI
```

**Key components:**

- **Bee Integration** (`backend/app/bee/`): MCP client that reads active todos, recent conversations, and location from Bee. Context normalizer extracts activity type, planned time, and intent text.

- **Environmental Layer** (`backend/app/environmental/`): Open-Meteo API integration for weather, UV, and air quality forecasts. All data labelled as forecast vs observation with full provenance.

- **Reasoning Engine** (`backend/app/reasoning/`): Deterministic decision logic with 15% material-improvement threshold, 8-state decision machine, and personal feasibility checking.

- **Frontend** (`frontend/`): Decision-first UI where the recommendation is the headline, not the metrics. Bee provenance visible immediately. Environmental evidence accessible via drawer.

**Tech stack:**
- Python + FastAPI (backend)
- Vanilla JS + HTML/CSS (frontend)
- Open-Meteo API (weather + air quality)
- Docker Compose (deployment)
- Cloudflare Tunnel (public HTTPS)

**Development:**
Built using **Kiro Crew** — an AWS-based agent orchestration platform that provided spec-driven development, persistent memory across sessions, and autonomous task execution.

### Challenges We Ran Into

1. **Headless Bee login** — Bee CLI requires an OS keyring over D-Bus, which doesn't exist on a headless server. Worked around by running the live Bee component on a desktop host.

2. **Container-to-host MCP** — Bee MCP's HTTP transport 403s on non-localhost Host headers, blocking container access. Fixed by overriding the Host header to 127.0.0.1.

3. **Bee search hangs** — The `bee_search` MCP tool intermittently times out with 0 bytes. Made it best-effort in the app pipeline so the rest of the flow continues.

4. **Environmental data granularity** — CAMS air quality is 3-hourly native resolution, not truly hourly. Documented clearly and avoided over-precise claims.

### Accomplishments That We're Proud Of

- **Real Bee integration** — Not a mock. Live Bee data flows through the entire pipeline and affects real recommendations.

- **Decision-first design** — Users see the recommendation first, not a wall of metrics. The environmental data supports the decision.

- **Controlled abstention** — The system doesn't force recommendations. If no materially better window exists, it correctly preserves your plan.

- **Privacy-by-design** — No raw personal text persisted. Context is normalized to structured fields. In-memory only.

- **Production deployed** — Live at [bee.andywongpt.com](https://bee.andywongpt.com) with real Bee data.

- **Open source** — MIT licensed, fully documented, 27 PRs merged.

### What We Learned

- **Bee + environment = powerful combination** — Bee understands the user's context. Environmental APIs understand the surrounding conditions. Together they enable genuinely personalized recommendations.

- **Provenance matters** — Users need to know where data comes from. Every environmental reading shows its source, fetch time, and observation time.

- **Materiality threshold is important** — Tiny improvements (5% AQI reduction) aren't worth recommending. The 15% threshold avoids noise.

- **Headless auth is a real pain point** — For wearable AI to integrate with server-side applications, headless/agent-friendly auth flows are essential.

### What's Next for Ambient Guard

**Future possibilities** (not currently implemented):

- BLE PM2.5 sensor integration for personal exposure tracking
- Indoor CO2/VOC sensing
- Noise exposure monitoring
- Pollen data integration
- Smart-home environmental actions (air purifier control)
- Alexa+ integration for voice queries
- Hyperlocal sensing networks

---

## Built With

**Core:**
- Bee MCP — Real personal context integration
- Python — Backend language
- FastAPI — Web framework
- Open-Meteo — Weather and air quality data
- CAMS (via Open-Meteo) — Air quality forecasts
- Docker — Containerization
- Docker Compose — Orchestration

**Frontend:**
- Vanilla JavaScript — No framework overhead
- HTML5 / CSS3 — Responsive design

**Development:**
- Kiro Crew — Agent orchestration, spec-driven development
- Playwright — E2E testing

**Deployment:**
- Fedora Server — Host OS
- Cloudflare Tunnel — Public HTTPS without port forwarding

---

## AWS Builder (Mini Challenge)

Ambient Guard was developed using **Kiro Crew** — an agent orchestration platform built on AWS infrastructure.

### Kiro Crew Integration

**What Kiro Crew provided:**

1. **Spec-driven development** — Three core specs (`requirements.md`, `design.md`, `tasks.md`) defined the project upfront and guided all implementation.

2. **Task Runner** — Autonomous agent execution of well-defined tasks (milestones M0-M8).

3. **Persistent memory** — Context and state survived across sessions, enabling multi-day development without re-explaining the project.

4. **Subagents** — Parallel execution for research and investigation tasks.

5. **Friction logging** — Structured capture of platform issues for feedback.

**Evidence:**
- Specs: `.kiro/specs/ambient-guard/`
- Session history: Kiro Crew workspace memory
- Documentation: `docs/AWS_BUILDER_KIRO.md`

**AWS infrastructure used by Kiro Crew:**
- Agent orchestration (Lambda / Fargate)
- State and memory storage (DynamoDB / S3)
- Session management

**Note:** Ambient Guard itself runs on a dedicated Fedora server, not AWS runtime. Kiro Crew was the development orchestration layer.

---

## Open Source (Mini Challenge)

- **Project URL:** [github.com/andywongpt-my/ambient-guard](https://github.com/andywongpt-my/ambient-guard)
- **License:** MIT
- **GitHub username:** andywongpt-my
- **Description:** Personal Environmental Agent integrating real Bee context with environmental forecasts
- **Why it matters:** Demonstrates how wearable AI (Bee) can power contextual environmental decisions — a new category of application beyond weather dashboards

**Repository stats:**
- 27 PRs merged
- Full documentation (requirements, design, architecture, deployment)
- Test suite (44 backend tests, Playwright E2E)
- Production deployed with real Bee data

---

## Links

- **Live demo:** [bee.andywongpt.com](https://bee.andywongpt.com)
- **GitHub:** [github.com/andywongpt-my/ambient-guard](https://github.com/andywongpt-my/ambient-guard)
- **Demo script:** `docs/DEMO_SCRIPT.md`
- **Architecture:** `docs/ARCHITECTURE.md`

---

## Video Demo

(2:30-2:50 video showing real Bee integration and decision flow)

*To be recorded per `docs/DEMO_RECORDING_PLAN.md`*

---

## Team

- Andy Wong (@andywongpt-my) — Developer

---

## Acknowledgments

- Bee team for the MCP integration surface
- Open-Meteo for free, open environmental data
- Kiro Crew for the development orchestration platform
