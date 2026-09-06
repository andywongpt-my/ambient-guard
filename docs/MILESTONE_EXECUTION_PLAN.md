# Ambient Guard — Milestone Execution Plan (M0–M8)

**Project:** Ambient Guard — Personal Environmental Agent powered by Bee
**Event:** Amazon Developer Hackathon 2026

## Guiding Principle — Vertical Slice First

**Immediately after M0, the focus is the smallest end-to-end vertical slice:**

```
REAL BEE DATA → CONTEXT EXTRACTION → ENVIRONMENTAL DATA → REASONING → ONE GROUNDED RECOMMENDATION
```

Prove this thin path with **real Bee data** before broadening any layer. M1 is the
highest-priority milestone and gates everything downstream — do not mark it done until real
Bee data has demonstrably entered the app with reproducible evidence.

---

## M0 — Repository Baseline
- **Next actions:** repo skeleton, license, dependency management, lint/format, test/build commands, Docker baseline, `docs/` skeleton, config scaffolding for secrets.
- **Dependencies:** none.
- **DoD:** repo builds and runs an empty app; config loads secrets from env; a contributor can clone and start in one documented command.

## M1 — Live Bee Integration *(HIGHEST PRIORITY — gates everything)*
- **Next actions:** (1) install `bee` CLI + `bee login`; (2) implement `cli` adapter (`bee today`/`search`/`locations current`); (3) pull real captured entries incl. the hero line; (4) surface raw Bee payload in-app with source badge + timestamp; (5) capture reproducible evidence (recording + saved payload + screenshot).
- **Dependencies:** M0.
- **DoD:** **Real Bee data demonstrably visible in the running app, with captured, reproducible evidence.** Not "the client compiles." **Do not mark done until demonstrated.**

## M2 — Environmental Data Layer
- **Next actions:** provider abstraction for PM2.5/PM10/AQI/UV/temp/humidity/weather + forecast; source attribution, timestamps, unit normalization, validation; timeout/error/rate-limit handling; fallback + cache; tag observed/forecast/estimate.
- **Dependencies:** M0 (can develop parallel to M1).
- **DoD:** all metrics return normalized, source-attributed, timestamped values for the hero location; failure/timeout/rate-limit paths tested; fallback + cache verified.

## M3 — Context Normalization
- **Next actions:** map raw Bee context → activity/planned_time/location/intent with per-field traceability; enforce no unsupported inference; validate hero extraction.
- **Dependencies:** M1 (needs real payloads).
- **DoD:** hero context extracts correctly with traceability; no field populated beyond source support; unit-tested against real Bee samples.

## M4 — Reasoning Engine
- **Next actions:** combine context + observations + time + location → structured recommendation {text, reasoning_summary, evidence[], timestamps, confidence}; threshold rules; guardrail requiring ≥1 evidence item.
- **Dependencies:** M2 + M3.
- **DoD:** hero scenario yields exactly one grounded recommendation with evidence referencing real timestamped observations + confidence; none emitted without evidence. **Closes the vertical slice.**

## M5 — Environmental Timeline
- **Next actions:** hourly timeline now→planned time and beyond; label observed/forecast/estimate/direct-measurement; mark 17:00; labels from provider metadata.
- **Dependencies:** M2.
- **DoD:** timeline renders the hero day, correctly labeled + timestamped, planned time marked, labels traceable.

## M6 — UX (Sub-3-Minute Demo UI)
- **Next actions:** five panels in mandatory order (context → conditions → recommendation → evidence → timeline); legible badges/timestamps/confidence; clean first load.
- **Dependencies:** M1–M5.
- **DoD:** clean UI presents the full hero flow end-to-end, legibly, under 3 minutes, with real attributed data.

## M7 — Reliability
- **Next actions:** unit tests (extraction, normalization, thresholds); provider tests + malformed-response; integration + E2E over the slice; failure-path/timeout tests; security + privacy review.
- **Dependencies:** M1–M4 (+M5/M6 for E2E).
- **DoD:** suite covers unit/provider/integration/failure/timeout/malformed/E2E and passes in CI; security + privacy reviews completed.

## M8 — Competition Readiness
- **Next actions:** public repo + OSS license; README + architecture docs; compliance matrix; product feedback + friction log; demo script + captured evidence.
- **Dependencies:** M0–M7.
- **DoD:** submission-ready public repo with all docs, evidence, and a rehearsed sub-3-minute demo.

---

## Dependency Summary

```
M0 ──┬──> M1 (HIGHEST) ──> M3 ──┐
     └──> M2 ─────────────┐     ├──> M4 (closes vertical slice)
                          └─────┘
M2 ──> M5
M1..M5 ──> M6
M1..M4 (+M5,M6 for E2E) ──> M7
M0..M7 ──> M8
```

**Critical path to first working demo:** M0 → M1 → (M2 ∥ M3) → M4. Everything after
hardens and packages that slice. Do not advance past M1 on paper — advance only after real
Bee data is demonstrably in the app.
