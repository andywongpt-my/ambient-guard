# Milestone 7 — Reliability, Security & Privacy Review

Date: 2026-09-07 · Reviewer: Ambient Guard crew · Scope: backend/app, tests, deployment

## 1. Reliability — test suite

Full suite (mock mode, CI-safe): **44 passed, 1 skipped** (the live Bee test skips without a login).
Live Bee ingress test (cli mode, dev host): **passed**.

Coverage by layer (45 tests total):

| Area | Tests | Covers |
|------|-------|--------|
| Bee cli adapter | 6 | mock endpoint, factory, CLI-not-found, non-JSON, not-logged-in, live ingress |
| Bee MCP backend | 4 | structuredContent + text envelopes, RPC error, missing-token |
| Environmental | 6 | happy path, missing-metric skip, timeout, malformed, error surfacing, cache |
| Normalization | 15 | activity, 12h/24h/relative time + rollover, location recent/stale/fallback, no-inference, hero, todos-as-intent |
| Reasoning | 6 | warning/caution tiers, all-clear guardrail, no-obs refusal, full slice, search-resilience |
| Timeline | 3 | observed/forecast + estimate/direct-measurement labels, planned marking |
| Health | 1 | /health |

**Failure paths are explicitly tested**: Bee not-logged-in, CLI missing, non-JSON, MCP RPC error,
provider timeout/malformed, bee_search hang (best-effort), reasoning with zero observations.

## 2. Security review

| Check | Finding |
|-------|---------|
| Secrets in repo | NONE. Grep of backend for token/password/secret: only env reads (`os.getenv`) — no hardcoded values. Verified across all history in prior leak-checks. |
| Token handling | Bee MCP bearer token from `AMBIENT_GUARD_BEE_HTTP_TOKEN` (env only). Bee account token never leaves the OS keyring / Bee CLI; the app never reads it. |
| Token in logs | No `logging`/`print` of tokens or Bee content anywhere in backend. |
| MCP transport | `bee mcp serve-http` bound to 127.0.0.1 + bearer token (≥32 chars); localhost Host/Origin guard enforced (the app sends a loopback Host to satisfy it — never bypasses auth). |
| Backend exposure | Container bound to `127.0.0.1:18080`; public access only via Cloudflare Tunnel (TLS terminated by CF). Not directly internet-exposed. |
| CORS | `allow_origins=["*"]` — acceptable for a public read-only demo (no auth/cookies, GET/POST assessments only). FLAGGED: tighten to the known origin before any write endpoints or auth are added. |
| Input validation | FastAPI + Pydantic validate all query/body params (lat/lon floats, limit bounds). Provider responses validated (numeric coercion, missing-metric skip). |
| Dependencies | Pinned ranges in requirements.txt; all mainstream (fastapi, httpx, pydantic, uvicorn). |

## 3. Privacy review (data minimization)

| Question | Finding |
|----------|---------|
| What Bee data is consumed? | today-context (recentConversations/activeTodos summaries), current location, optional search — only what the normalizer needs for the decision. |
| What is stored? | **NOTHING.** The backend has NO database code (no sqlalchemy/psycopg/DATABASE_URL usage) — `DATABASE_URL` is set in compose but never read. All Bee data is held in-memory for the single request and discarded when the response returns. This is stronger than the original privacy doc, which said normalized results were stored "as needed"; corrected to "not persisted". |
| Raw recordings / transcripts persisted? | No. Raw Bee payloads pass through normalization and are dropped; only a redacted, coarsened form ever reaches disk (evidence files, hand-sanitized). |
| Location history | Only the current location is fetched per request; no history retained. |
| Exposure terminology | Timeline + reasoning label API-based readings as `estimate` / "estimated environmental exposure", never a personal measurement (exposure_kind=estimate). Reasoning summary explicitly states "precautionary environmental guidance, not medical advice". |
| Evidence redaction | All committed evidence (M1/M3/M6) has token, exact address, location id, and full-precision coords redacted/coarsened. |

## 4. Findings & actions

- ✅ No secrets, no logging of sensitive data, no persistence of Bee data.
- ✅ Failure paths tested; app degrades gracefully (provider errors surfaced; bee_search hang tolerated).
- ✅ **CORS tightened** (was `*`) to an explicit env-driven allow-list (default: the live origin +
  localhost), methods limited to GET/POST — resolved.
- ✅ **Unused DB removed** — the Postgres `db` service, `depends_on`, `DATABASE_URL`, and `pgdata`
  volume were dropped from compose; the app persists nothing. Re-add with a retention policy only
  when a real persistence need exists — resolved.
- ✅ SECURITY_AND_PRIVACY.md reconciled to match the implementation (no persistence).

Conclusion: Ambient Guard meets M7's reliability, security, and privacy bar for a hackathon
demo. The two 🟡 items are documented, non-blocking, and safe given the current read-only scope.
