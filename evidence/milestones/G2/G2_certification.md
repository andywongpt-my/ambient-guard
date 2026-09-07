# G2 Certification Report: Environmental Intelligence & Alternative-Time Reasoning

**Status: PASS**

**Date:** 2026-09-07
**Commit:** 2197736 (main)
**PR:** [#22](https://github.com/andywongpt-my/ambient-guard/pull/22)

---

## Certification Criteria Checklist

### 1. Production Deployment Succeeds
- **Status: PASS**
- Deployed to meow server via `docker compose -p ambient-guard up -d --build`
- Health endpoint returns `{"status":"ok","bee_mode":"mcp"}`
- Live assess endpoint returns G2-enhanced responses

### 2. Full G1+G2 Regression Passes
- **Status: PASS**
- Test results: 67 passed, 1 skipped, 1 warning
- No failures in G1 or G2 test suites
- Test command: `python -m pytest tests/ -v`

### 3. Live Bee G2 Path Succeeds
- **Status: PASS**
- Live endpoint: `https://bee.andywongpt.com/api/v1/assess`
- Response includes:
  - `planned_window` with environmental data
  - `reason_codes` populated
  - `limitations` populated
  - `data_kind` field (observed/forecast)
- Evidence saved: `evidence/milestones/G2/live/assess_response.json`

### 4. AQI Standard Remains Explicit
- **Status: PASS**
- AQI uses US EPA standard explicitly
- Field: `aqi_standard: "us_epa"` on AQI observations
- Source: Open-Meteo's `us_aqi` field

### 5. Observed vs Forecast Remains Explicit
- **Status: PASS**
- Every observation has `kind` field: "observed" or "forecast"
- `data_kind` field on planned_window summarizes overall data type
- Logic: `obs_at > fetched_at` → "forecast", else "observed"

### 6. Upstream Environmental Resolution Documented
- **Status: PASS**
- Document: `docs/ENVIRONMENTAL_DATA_SOURCES.md`
- CAMS Global air quality: 3-hourly native resolution
- Hourly values are interpolated (not native resolution)
- Weather: hourly native resolution

### 7. Time Alignment Is Explicit
- **Status: PASS**
- User planned time snaps to nearest hour for environmental lookup
- Documented in `docs/ENVIRONMENTAL_DATA_SOURCES.md`
- Timezone preserved via Open-Meteo `timezone=auto` param

### 8. Material Improvement Policy Exists
- **Status: PASS**
- Threshold: 15% score improvement required
- Policy: `window_selector._MIN_IMPROVEMENT_THRESHOLD = 0.15`
- Documented in code docstring and ENVIRONMENTAL_DATA_SOURCES.md
- Prevents trivial recommendations from minor variations

### 9. False Precision Prevented
- **Status: PASS**
- Language uses "appears more favorable" not "better"
- Limitations field discloses interpolation caveat
- Do not claim hourly precision for 3-hourly air quality data

### 10. Environmentally-Better and Personally-Recommended Windows Distinguished
- **Status: PASS**
- `environmentally_better_window`: Best environmental conditions found
- `recommended_window`: Personal recommendation with feasibility check
- Feasibility: Only recommend windows in reasonable hours (6am-10pm)
- If user's planned time is in reasonable hours, it's preferred

### 11. Attribution Complete
- **Status: PASS**
- All observations carry `source.attribution: "Open-Meteo (CC BY 4.0)"`
- Provider, fetched_at, observed_at, lat/lon all populated
- Activity policy sources cited: EPA, WHO, NWS

### 12. Activity-Policy Sources Audited
- **Status: PASS**
- Document: `backend/app/agent/activity_policy.py` docstring
- Sources explicitly cited:
  - EPA AirNow: https://www.airnow.gov/aqi/aqi-basics/
  - WHO: https://www.who.int/publications/i/item/9789240034228
  - NWS Heat Index: https://www.weather.gov/safety/heat
- Importance weights (HIGH=3x, MEDIUM=2x, LOW=1x) are Ambient Guard heuristics

### 13. Live Evidence Sanitized
- **Status: PASS**
- PII removed: location coordinates generalized to 3.13, 101.7
- bee_login removed from response
- Evidence saved to `evidence/milestones/G2/live/`

### 14. Privacy Review Passes
- **Status: PASS**
- No new PII collected in G2
- Environmental data fetched server-side
- User location already handled in G1

### 15. Final Commit Hash Exists
- **Status: PASS**
- Commit: 2197736
- Branch: main
- Merged via PR #22, test fix via PR #24

---

## Summary

G2 Environmental Intelligence & Alternative-Time Reasoning has been successfully implemented, tested, and deployed to production. All 15 certification criteria are met.

### Key Achievements
- 10 activity-specific environmental policies with cited thresholds
- Alternative time window discovery with material improvement policy
- Clear distinction between environmental conditions and personal recommendations
- Complete source attribution and resolution documentation
- No false precision claims for interpolated air quality data

### Files Modified
- `backend/app/agent/activity_policy.py` - Activity-specific environmental policies
- `backend/app/agent/window_selector.py` - Time-window comparison logic
- `backend/app/agent/reasoning.py` - G2 integration
- `backend/app/agent/reasoning_models.py` - New G2 response fields
- `backend/app/environmental/open_meteo.py` - AQI standard attribution
- `docs/ENVIRONMENTAL_DATA_SOURCES.md` - Complete documentation

### Test Coverage
- G2 window selector tests: 20 tests
- G2 activity policy tests: 6 tests
- Total: 67 passed, 1 skipped

---

**Certified by:** Ambient Guard G2 Certification
**Date:** 2026-09-07
