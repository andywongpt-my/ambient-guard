# G1 — Final Report

**Date:** 2026-09-07T16:30:00+08:00
**Commit:** 46f111c67f24de12afbbb726eac018787897c01a

---

## Status

**G1 = PASS**

All PASS criteria satisfied. The vertical slice is complete and running live.

---

## Real Bee Integration

- **Integration method:** MCP (JSON-RPC 2.0 over HTTP)
- **Endpoint:** `http://127.0.0.1:8790/mcp` (forwarded from container to host)
- **Auth:** Bearer token via `AMBIENT_GUARD_BEE_HTTP_TOKEN`
- **Source:** Real Bee todo id 28703772 ("Go jogging at 5 PM")
- **Timestamp:** 2026-09-07T08:20:56.893000

**Relevant files:**
- `backend/app/bee/client.py` — MCP backend implementation
- `backend/app/bee/models.py` — Pydantic models
- `backend/app/agent/normalize.py` — ContextIntent extraction

---

## Environmental Provider

- **Provider:** Open-Meteo (no API key required)
- **Fields retrieved:** temp_c, humidity, wind_kmh, precip_mm, uv, weather, pm25, pm10, ozone, no2, aqi
- **Timestamps preserved:** Yes (observed_at, fetched_at)
- **Units preserved:** Yes (°C, %, km/h, mm, index, wmo, µg/m³, AQI)
- **Source attribution:** Open-Meteo (CC BY 4.0)

**Live result proof:** `evidence/milestones/G1/live_assess_response.json`

---

## End-to-End Result

```
Bee todo "Go jogging at 5 PM"
        ↓
ContextIntent {activity=jogging, planned_time=17:00, location=Tuaran, confidence=1.0}
        ↓
Environmental observations (11 metrics from Open-Meteo forecast for 17:00)
        ↓
Recommendation: "Jogging at 17:00 is okay with care: AQI 119 is unhealthy for sensitive groups..."
        ↓
Evidence: AQI 119 forecast, severity=caution, source=open-meteo
```

**Redacted private data:**
- Precise coordinates coarsened to 6.183, 116.22 in evidence
- Address redacted in evidence files
- Bearer token never logged

---

## Tests

- **Test count:** 45 total
- **Result:** 44 passed, 1 skipped (live Bee test requires login)
- **Coverage:** Bee adapter, MCP backend, environmental, normalization, reasoning, timeline, health
- **Failure-path coverage:** Bee unavailable, API timeout, malformed response, missing data, location unavailable

---

## Privacy

**What Bee data was consumed:**
- today-context (recentConversations/activeTodos summaries)
- current location (GPS coordinates)
- Intent text from todo

**What was persisted:**
- **NOTHING.** Backend has no database code. All data held in-memory for single request.

**What was deliberately not persisted:**
- Raw Bee recordings
- Full transcripts
- Unrelated conversations
- Location history
- Normalized ContextIntent or Assessment

---

## Friction

| ID | Description | Severity | Outcome |
|----|-------------|----------|---------|
| FR-001 | Bee CLI not installed; login prerequisites not obvious | S3 | Resolved |
| FR-002 | `bee login --no-wait` does not finalize approved session | S2 | Resolved |
| FR-003 | docs.bee.computer/docs/cli intermittently failed | S1 | Resolved |
| FR-004 | `bee login` cannot persist on headless server (no keyring fallback) | S3 | Unresolved (token workaround) |
| FR-005 | `bee mcp serve-http` 403s on non-localhost Host | S2 | Resolved |
| FR-006 | MCP `bee_get_today` rejects CLI's `--context` argument | S1 | Resolved |
| FR-007 | `bee_search` hangs (server-side), breaking pipeline | S2 | Resolved (app-side resilience) |

---

## Evidence

- `evidence/milestones/G1/G1_report.md` — Full verification report
- `evidence/milestones/G1/live_assess_response.json` — Raw live API response
- `evidence/M1_bee_login.md` — Bee login verification
- `evidence/M1_bee_ingress.md` — Bee data ingress proof
- `evidence/M3_context_normalization.md` — Context normalization proof
- `evidence/M4_reasoning_slice.md` — Reasoning engine proof
- `evidence/M7_reliability_security_privacy.md` — Test suite + security/privacy review
- `evidence/screenshots/M6_demo_flow_live.gif` — Live demo GIF

---

## Commit

**Final commit:** `46f111c67f24de12afbbb726eac018787897c01a`

**Live site:** https://bee.andywongpt.com

---

## G1 PASS Criteria Checklist

| Criterion | Status |
|-----------|--------|
| Real Bee data was retrieved | ✅ PASS |
| No mock Bee data in final path | ✅ PASS |
| Bee adapter exists | ✅ PASS |
| Context normalization works | ✅ PASS |
| Real environmental data retrieved | ✅ PASS |
| Environmental evidence contains timestamps and units | ✅ PASS |
| Recommendation is grounded in retrieved evidence | ✅ PASS |
| Source traceability is preserved | ✅ PASS |
| Missing-data paths fail safely | ✅ PASS |
| Tests pass | ✅ PASS |
| Privacy review completed | ✅ PASS |
| Evidence captured | ✅ PASS |
| Relevant documentation updated | ✅ PASS |
| Git diff reviewed | ✅ PASS |

**G1 = PASS**
