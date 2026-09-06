# Ambient Guard

**A Personal Environmental Agent powered by Bee.**

Ambient Guard fuses personal context from an Amazon Bee wearable with real environmental
data to answer the question a plain air-quality app can't:

> "What does the environment mean for what I'm about to do?"

It is **not** a medical system — recommendations are informational / precautionary
environmental guidance.

## Hero use case

Bee captures: **"I plan to jog at 5 PM."** Ambient Guard extracts the activity, time, and
location, retrieves PM2.5 / UV / temperature / humidity / weather for that window, reasons
over the combination, and produces **one grounded recommendation with supporting evidence** —
e.g. *"Your 5 PM run overlaps with elevated particulate levels and high UV; conditions
improve later — consider shifting it."*

## Architecture (short)

```
Apple Watch + Bee → Bee CLI/MCP → Bee Integration Layer → Context Normalization → ContextIntent
Environmental providers (Open-Meteo weather+UV / air-quality, OpenAQ, optional pollen) → Environmental Layer
   → Reasoning Engine (guardrail: ≥1 evidence) → Recommendation + Timeline → FastAPI → Next.js UI
```

Full detail: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Tech stack

Python + FastAPI · React/Next.js · PostgreSQL · Docker Compose behind nginx.

## Quick start (dev)

```bash
cp .env.example .env         # fill in as needed; AMBIENT_GUARD_BEE_MODE=mock works offline
docker compose up --build    # backend :8080, frontend, postgres
# health: curl http://127.0.0.1:8080/health
```

### Live Bee integration

The competition-critical path uses **real** Bee data (mocks are for tests only):

```bash
# on the host running the backend:
bee login                    # authenticate the Bee CLI
bee mcp status               # verify
export AMBIENT_GUARD_BEE_MODE=cli   # or mcp
```

See [`.kiro/specs/ambient-guard/design.md`](.kiro/specs/ambient-guard/design.md) for the
backend selection (`cli` | `mcp` | `mock`).

## Built with Kiro

Ambient Guard is developed with **Kiro Crew** (agent orchestration + sub-agents),
**Kiro Specs** (`.kiro/specs/ambient-guard/{requirements,design,tasks}.md`), and the
**Kiro Task Runner**. Development friction is logged in [`FRICTION_LOG.md`](FRICTION_LOG.md)
and tooling feedback in [`docs/PRODUCT_FEEDBACK.md`](docs/PRODUCT_FEEDBACK.md).

## Docs

| Doc | Purpose |
|-----|---------|
| [`.kiro/specs/ambient-guard/requirements.md`](.kiro/specs/ambient-guard/requirements.md) | Requirements + acceptance criteria |
| [`.kiro/specs/ambient-guard/design.md`](.kiro/specs/ambient-guard/design.md) | Architecture + data models + API |
| [`.kiro/specs/ambient-guard/tasks.md`](.kiro/specs/ambient-guard/tasks.md) | Ordered implementation tasks |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System architecture |
| [`docs/DEMO_PLAN.md`](docs/DEMO_PLAN.md) | Sub-3-minute demo script |
| [`docs/COMPETITION_COMPLIANCE.md`](docs/COMPETITION_COMPLIANCE.md) | Compliance matrix |
| [`docs/RISK_REGISTER.md`](docs/RISK_REGISTER.md) | Risks (R1 = live Bee login) |
| [`docs/SECURITY_AND_PRIVACY.md`](docs/SECURITY_AND_PRIVACY.md) | Data minimization + security |
| [`docs/MILESTONE_EXECUTION_PLAN.md`](docs/MILESTONE_EXECUTION_PLAN.md) | M0–M8 plan |

## License

[MIT](LICENSE).
