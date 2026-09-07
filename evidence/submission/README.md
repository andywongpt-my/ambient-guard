# Ambient Guard — Judge Evidence Package

This directory indexes the strongest evidence for the Amazon Developer Hackathon submission.

---

## Quick Links

| What | Where | Description |
|------|-------|-------------|
| **Live Demo** | [bee.andywongpt.com](https://bee.andywongpt.com) | Production deployment with real Bee data |
| **Source Code** | [GitHub](https://github.com/andywongpt-my/ambient-guard) | MIT licensed, 27 PRs merged |
| **README** | [`README.md`](../../README.md) | Project overview and quick start |

---

## Certification Evidence

### G1: Bee Integration PASS
- **Location:** `../milestones/G1/`
- **Key evidence:**
  - `G1_certification.md` — Full certification report
  - Live Bee context retrieval verified
  - MCP integration confirmed

### G2: Environmental Layer PASS
- **Location:** `../milestones/G2/`
- **Key evidence:**
  - `G2_certification.md` — Full certification report
  - Open-Meteo integration verified
  - Air quality data flowing

### G3: Personal Context Intelligence PASS
- **Location:** `../milestones/G3/`
- **Key evidence:**
  - `G3_certification.md` — Full certification report
  - Personal feasibility engine working
  - Constraint extraction verified

### G4: Production Validation PASS
- **Location:** `../milestones/G4/`
- **Key evidence:**
  - `G4_certification.md` — Full certification report
  - `live_assess_response.json` — Real Bee + environmental response
  - `screenshots/` — Desktop and mobile UI
  - `backend_tests_final.txt` — 44 passed / 1 skipped
  - `playwright-results.txt` — E2E test results

---

## Architecture & Design

| Document | Location | Description |
|----------|----------|-------------|
| Architecture | [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) | System architecture, data flow, components |
| Design Spec | [`.kiro/specs/ambient-guard/design.md`](../../.kiro/specs/ambient-guard/design.md) | Detailed design document |
| Requirements | [`.kiro/specs/ambient-guard/requirements.md`](../../.kiro/specs/ambient-guard/requirements.md) | Requirements and acceptance criteria |

---

## Testing

| Evidence | Location | Description |
|----------|----------|-------------|
| Backend Tests | `../milestones/G4/backend_tests_final.txt` | 44 passed / 1 skipped |
| E2E Tests | `../milestones/G4/playwright-results.txt` | Playwright production validation |
| Test Code | `../../tests/` | Unit and integration tests |

---

## Production Deployment

| Evidence | Description |
|----------|-------------|
| **URL** | https://bee.andywongpt.com |
| **Mode** | `mcp` (live Bee data) |
| **Health** | `GET /health` returns `status: ok, bee_mode: mcp` |
| **Deployment Doc** | [`docs/DEPLOYMENT.md`](../../docs/DEPLOYMENT.md) |

---

## Bee Integration

| Evidence | Location |
|----------|----------|
| Live Bee response | `../milestones/G4/live_assess_response.json` |
| Bee client code | `../../backend/app/bee/` |
| Context normalizer | `../../backend/app/bee/normalizer.py` |
| MCP client | `../../backend/app/bee/client.py` |

**Key proof points:**
- Bee ref ID visible in responses (e.g., ref 28703772)
- Activity/planned_time extracted from Bee context
- Location sourced from Bee (with fallback)

---

## Environmental Data

| Evidence | Location |
|----------|----------|
| Environmental client | `../../backend/app/environmental/open_meteo.py` |
| Data sources doc | [`docs/ENVIRONMENTAL_DATA_SOURCES.md`](../../docs/ENVIRONMENTAL_DATA_SOURCES.md) |
| Live response | `../milestones/G4/live_assess_response.json` |

**Key proof points:**
- Open-Meteo attribution in every observation
- Forecast vs observation labels
- CAMS air quality via Open-Meteo API

---

## Reasoning Engine

| Evidence | Location |
|----------|----------|
| Reasoning engine | `../../backend/app/reasoning/engine.py` |
| Decision states | `../../backend/app/reasoning/decision_state.py` |
| Personal context | `../../backend/app/reasoning/personal_context.py` |
| G3 certification | `../milestones/G3/G3_certification.md` |

**Key proof points:**
- 8-state decision machine
- 15% material-improvement threshold
- Personal feasibility checking

---

## Privacy & Security

| Evidence | Location |
|----------|----------|
| Security doc | [`docs/SECURITY_AND_PRIVACY.md`](../../docs/SECURITY_AND_PRIVACY.md) |
| No persistent storage | Backend code review shows in-memory only |

**Key proof points:**
- No raw personal text persisted
- Context normalized to structured fields
- No authentication required (uses host Bee session)

---

## Kiro Crew / AWS Builder

| Evidence | Location |
|----------|----------|
| Kiro evidence doc | [`docs/AWS_BUILDER_KIRO.md`](../../docs/AWS_BUILDER_KIRO.md) |
| Specs | `.kiro/specs/ambient-guard/` |
| Friction log | [`FRICTION_LOG.md`](../../FRICTION_LOG.md) |

---

## Competition Compliance

| Track | Status | Evidence |
|-------|--------|----------|
| **Bee — Wearable AI** | ✅ Primary | Live Bee MCP integration, real personal context |
| **AWS Builder** | ✅ Mini | Kiro Crew development orchestration |
| **Open Source** | ✅ Mini | MIT license, public repo, documented |

See [`docs/COMPETITION_COMPLIANCE.md`](../../docs/COMPETITION_COMPLIANCE.md).

---

## Demo Materials

| Material | Location |
|----------|----------|
| Demo script | [`docs/DEMO_SCRIPT.md`](../../docs/DEMO_SCRIPT.md) |
| Recording plan | [`docs/DEMO_RECORDING_PLAN.md`](../../docs/DEMO_RECORDING_PLAN.md) |
| Screenshots | `../milestones/G4/screenshots/` |

---

## Submission Checklist

- [x] G1-G4 certifications complete
- [x] Production healthy at bee.andywongpt.com
- [x] Real Bee data flowing
- [x] Tests passing (44/1)
- [x] Documentation complete
- [x] README competition-ready
- [x] Demo script prepared
- [x] Friction log finalized
- [x] Product feedback documented
- [x] Devpost draft complete
- [x] Open source (MIT) license

---

## For Judges

**Fastest path to verify:**

1. Open [bee.andywongpt.com](https://bee.andywongpt.com) — see the live UI
2. Check `../milestones/G4/live_assess_response.json` — see real Bee + environmental data
3. Review `G4_certification.md` — see full validation
4. Browse `../../backend/app/` — see implementation

**Total time: ~10 minutes**

---

*This package was prepared for the Amazon Developer Hackathon submission.*
