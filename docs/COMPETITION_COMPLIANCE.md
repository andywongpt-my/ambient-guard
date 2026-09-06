# Ambient Guard — Competition Compliance Matrix

_Personal Environmental Agent · [Amazon Developer Hackathon 2026](https://amazonappdev2026.devpost.com/)_

**Targets**
- **Primary track** — Amazon Bee: Wearable AI
- **Mini challenge** — AWS Builder: Kiro Crew as a documented development integration
- **Mini challenge** — Open Source

**Status legend:** ✅ Met · 🟡 In progress · ⬜ Not started

| Requirement | Source | How Ambient Guard satisfies it | Evidence location | Status |
|-------------|--------|-------------------------------|-------------------|--------|
| Consume **REAL Bee data at runtime** that **materially affects output**; mocks allowed only for tests. | Primary track — *Amazon Bee: Wearable AI* | App calls the `bee` CLI/MCP (e.g. `bee today`, `bee locations current`) at request time; live context/location feed the reasoning and change the output. Mocked Bee responses appear ONLY in tests, gated by `AMBIENT_GUARD_BEE_MODE=mock`. | Live-data run recording + logs; `bee/` adapter; test fixtures labeled as mocks | 🟡 |
| Document **Kiro Crew / Kiro Specs / Kiro Task Runner** usage as a development integration. | Mini challenge — *AWS Builder* | Built with Kiro Crew (agent sessions + sub-agents), Kiro Specs (`.kiro/specs/ambient-guard/`), and Kiro Task Runner; documented with concrete references. | `.kiro/specs/`, `README.md` "Built with Kiro", `docs/PRODUCT_FEEDBACK.md` | 🟡 |
| **Public GitHub repository.** | Mini challenge — *Open Source* | Repo published publicly on GitHub. | GitHub repo URL (add once created) | ⬜ |
| **OSI-approved license.** | Mini challenge — *Open Source* | `LICENSE` (MIT) at repo root. | `LICENSE` | 🟡 |
| **README** present and usable. | Mini challenge — *Open Source* | `README.md`: what it does, setup (incl. Bee login), env vars, `docker compose` run, "Built with Kiro". | `README.md` | 🟡 |

---

## Evidence checklist (fill in as work lands)

- [ ] Recorded live run proving REAL Bee data changes the output (screen capture + logs).
- [ ] Bee adapter source in `bee/` with the exact `bee` CLI version pinned.
- [ ] Tests demonstrating mocks are confined to the test suite only.
- [ ] Kiro Specs files committed under `.kiro/specs/ambient-guard/`.
- [ ] Kiro Task Runner artifacts / references committed.
- [ ] "Built with Kiro" section in `README.md`.
- [ ] Public GitHub repo URL recorded here.
- [ ] `LICENSE` (OSI-approved) at repo root.

## Notes

- The single most important compliance item is **REAL Bee data at runtime** — see **R1** in `docs/RISK_REGISTER.md`. README-only Bee integration does NOT satisfy the primary track.
- Environmental provider defaults to **Open-Meteo** (no API key) to guarantee coverage — see **R2**.
