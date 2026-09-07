# Ambient Guard — Competition Compliance Matrix

_Personal Environmental Agent · [Amazon Developer Hackathon 2026](https://amazonappdev2026.devpost.com/)_

**Targets**
- **Primary track** — Amazon Bee: Wearable AI
- **Mini challenge** — AWS Builder: Kiro Crew as a documented development integration
- **Mini challenge** — Open Source

**Status legend:** ✅ Met · 🟡 In progress · ⬜ Not started

| Requirement | Source | How Ambient Guard satisfies it | Evidence location | Status |
|-------------|--------|-------------------------------|-------------------|--------|
| Consume **REAL Bee data at runtime** that **materially affects output**; mocks allowed only for tests. | Primary track — *Amazon Bee: Wearable AI* | LIVE: the public deployment runs `AMBIENT_GUARD_BEE_MODE=mcp` — the containerized backend calls the host's `bee mcp serve-http` (real Bee account, id 50853) for today-context + current location; these drive the recommendation. Mocked Bee appears ONLY in tests (`mock` mode). | [bee.andywongpt.com](https://bee.andywongpt.com) live (bee_mode=mcp, real location); `evidence/M1_bee_ingress.md`; `bee/` adapter | ✅ |
| Document **Kiro Crew / Kiro Specs** usage as a development integration. | Mini challenge — *AWS Builder* | Built end-to-end with **Kiro Crew** (agent sessions + parallel sub-agents, monitor loops, persistent memory) and **Kiro Specs** (`.kiro/specs/ambient-guard/{requirements,design,tasks}.md` drove every milestone). Documented in README "Built with Kiro" + `docs/PRODUCT_FEEDBACK.md`, with 7 friction entries (FR-001–007) on the Bee toolchain. NOTE: the Kiro **Task Runner** was not used — development was interactive Crew sessions; stated honestly rather than claimed. | `.kiro/specs/`, README "Built with Kiro", `docs/PRODUCT_FEEDBACK.md`, `FRICTION_LOG.md` | ✅ |
| **Public GitHub repository.** | Mini challenge — *Open Source* | Repo published publicly on GitHub. | [github.com/andywongpt-my/ambient-guard](https://github.com/andywongpt-my/ambient-guard) | ✅ |
| **OSI-approved license.** | Mini challenge — *Open Source* | `LICENSE` (MIT) at repo root. | `LICENSE` | ✅ |
| **README** present and usable. | Mini challenge — *Open Source* | `README.md`: what it does, setup (incl. Bee login), env vars, `docker compose` run, "Built with Kiro". | `README.md` | ✅ |

---

## Evidence checklist

- [x] Recorded live run proving REAL Bee data changes the output — `evidence/screenshots/M6_demo_flow_live.gif` + live `bee.andywongpt.com` (bee_mode=mcp).
- [x] Bee adapter source with the exact `bee` CLI version pinned — `backend/app/bee/`, `@beeai/cli` 0.7.3 (FR-001).
- [x] Tests demonstrating mocks are confined to the test suite only — `AMBIENT_GUARD_BEE_MODE=mock` gates fixtures; live test is login-gated.
- [x] Kiro Specs files committed under `.kiro/specs/ambient-guard/`.
- [~] Kiro Task Runner artifacts — N/A, not used (interactive Crew sessions instead); stated honestly above.
- [x] "Built with Kiro" section in `README.md`.
- [x] Public GitHub repo URL recorded here: https://github.com/andywongpt-my/ambient-guard
- [x] `LICENSE` (OSI-approved) at repo root.
- [x] Full evidence map — [`evidence/INDEX.md`](../evidence/INDEX.md).

## Notes

- The single most important compliance item is **REAL Bee data at runtime** — see **R1** in `docs/RISK_REGISTER.md`. README-only Bee integration does NOT satisfy the primary track.
- Environmental provider defaults to **Open-Meteo** (no API key) to guarantee coverage — see **R2**.
