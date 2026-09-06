# Ambient Guard — Risk Register

_Personal Environmental Agent · Amazon Developer Hackathon 2026_

**Legend** — Likelihood / Impact: Low · Medium · High. Status: Open · Mitigating · Closed.

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|----|------|------------|--------|------------|-------|--------|
| R1 | **Bee account/device availability for a live login.** The Fedora `meow` server has NO `bee` CLI installed and it is unknown whether it can hold a Bee login. Milestone 1 requires REAL Bee data at runtime — a README-only integration does NOT count. | High | High | Install and verify `bee` CLI + login on the dev machine first (known-good path). Spike a login on `meow` early; if it cannot hold a session, run the live component from the dev machine and treat `meow` as static-hosting only. Capture a recorded live-data run as fallback demo evidence. | Dev | Open |
| R2 | **Environmental provider free-tier coverage in the demo region.** | Medium | Medium | Default to **Open-Meteo** (no API key, global coverage). Keep provider behind an interface so a keyed provider can be swapped in later. | Dev | Mitigating |
| R3 | **Location fidelity.** `bee locations current` may be missing, stale, or coarse. | Medium | Medium | Prefer live Bee location; fall back to `AMBIENT_GUARD_DEFAULT_LOCATION`. Log which source was used so output is explainable. | Dev | Mitigating |
| R4 | **Provider rate limits / outages during the live demo.** | Medium | High | Short-TTL cache + explicit, visible fallback. **Never hide failures** — surface a clear "degraded/cached" state, never fake data. | Dev | Mitigating |
| R5 | **Privacy — Bee data may contain personal info.** Risk of over-collecting or persisting raw recordings/transcripts. | Medium | High | **Data minimization**: fetch only used fields. **No raw persistence** — hold only in-memory for the request. Document what is/ isn't stored. | Dev | Mitigating |
| R6 | **Port collisions on the deployment server.** `meow` already runs ~10 Docker containers + nginx. | Medium | Medium | Dedicated Docker Compose **project name** + a **non-standard upstream port**; nginx reverse-proxies the public route. Verify the port is free before deploy. | Dev | Mitigating |
| R7 | **Time / scope risk for a hackathon.** | High | High | Build the **smallest vertical slice first**: Bee data in → one environmental signal → one actionable output. Cut scope, not the live-data requirement. | Dev | Mitigating |
| R8 | **Bee API/CLI schema drift or undocumented behavior.** | Medium | Medium | Pin the `bee` CLI version; parse defensively; validate shape at the boundary; keep a thin adapter so a schema change is a one-file fix. Record the exact CLI version. | Dev | Open |
| R9 | **Secrets / credential leakage.** Bee session tokens or provider keys committed or logged. | Low | High | Keep secrets in env / untracked files; `.gitignore` credential files; scrub tokens from logs; never echo secret values. Required for the Open Source track. | Dev | Mitigating |
| R10 | **Demo-environment reproducibility.** "Works on my machine." | Medium | Medium | Containerize with a documented `docker compose up` path; pin dependency versions; document env vars + login step in README. | Dev | Open |
| R11 | **LLM/agent cost or latency during live use.** | Low | Medium | Cache environmental context; keep prompts tight; timeout with a graceful degraded response rather than a hang. | Dev | Open |

---

## Critical-path callout

**R1 is the make-or-break risk.** The primary track requires REAL Bee data consumed at
runtime that materially affects output. Resolve R1 (a verified live Bee login the app can
actually use) before investing in downstream features — everything else is moot if the app
cannot read live Bee data during judging.
