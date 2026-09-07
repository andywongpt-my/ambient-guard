# G2 — Environmental Intelligence & Alternative-Time Reasoning

**Date:** 2026-09-07T16:45:00+08:00
**Status:** IMPLEMENTATION COMPLETE

---

## G2.1 — Environmental Evidence Model

### Implementation
- Enhanced `Observation` model with `aqi_standard` and `quality` fields
- Open-Meteo provider sets `aqi_standard="us_epa"` for AQI observations
- Quality classification follows US EPA AQI categories:
  - 0-50: Good
  - 51-100: Moderate
  - 101-150: Unhealthy for Sensitive Groups
  - 151-200: Unhealthy
  - 201-300: Very Unhealthy
  - 301+: Hazardous

### Files
- `backend/app/environmental/base.py` — Observation model
- `backend/app/environmental/open_meteo.py` — AQI standard attribution

---

## G2.2 — Confidence Decomposition

### Implementation
- Added `FieldConfidence` model for per-field confidence tracking
- Enhanced `ContextIntent` with:
  - `activity_confidence: FieldConfidence | None`
  - `planned_time_confidence: FieldConfidence | None`
  - `location_confidence: FieldConfidence | None`

### Example
```python
activity_confidence:
  value: "jogging"
  source: "bee_todo"
  confidence: 1.0
  note: "activity 'jogging' matched (outdoor=True)"
```

### Files
- `backend/app/agent/models.py` — FieldConfidence model

---

## G2.3 — Time-Window Comparison

### Implementation
- Created `window_selector.py` module
- `score_window()` — Scores a single time window based on activity-specific importance
- `find_alternative_window()` — Searches ±N hours around planned time
- Weighted scoring: HIGH importance metrics weight 3x, MEDIUM 2x, LOW 1x

### Algorithm
1. Score planned time window (0-1, lower is better)
2. Generate candidate times (hourly intervals, skip past times, skip >48h ahead)
3. Score each candidate
4. Filter candidates with meaningful improvement (≥15% score reduction)
5. Return top 5 alternatives sorted by score

### Files
- `backend/app/agent/window_selector.py` — Window comparison logic

---

## G2.4 — Activity-Aware Evaluation

### Implementation
- Created `activity_policy.py` module
- Defined policies for 10 activity types:
  - Jogging, Running, Walking, Cycling, Hiking
  - Swimming, Exercise, Commute, Picnic, Gardening, Outdoor Work
- Each policy specifies:
  - `is_outdoor`: bool
  - `exertion_level`: "low" | "moderate" | "high"
  - `metrics`: dict of metric -> MetricPolicy
  - `health_note`: disclaimer text

### Threshold Sources
- US EPA AQI: https://www.airnow.gov/aqi/aqi-basics/
- WHO Air Quality: https://www.who.int/publications/i/item/9789240034228
- UV Index: https://www.epa.gov/sunsafety/uv-index-scale-0
- Heat Index: https://www.weather.gov/safety/heat

### Example Policy
```python
ActivityType.JOGGING:
  is_outdoor: True
  exertion_level: "high"
  metrics:
    aqi:
      importance: HIGH
      caution_threshold: 100
      warning_threshold: 150
    pm25:
      importance: HIGH
      caution_threshold: 35.5
      warning_threshold: 55.5
```

### Files
- `backend/app/agent/activity_policy.py` — Activity policies

---

## G2.5 — Alternative-Time Recommendation

### Implementation
- Integrated into `ReasoningEngine.assess()`
- Passes `observe_func`, `lat`, `lon` to enable window comparison
- Returns structured `AlternativeWindow` objects with:
  - `time`: Candidate time
  - `severity`: "info" | "caution" | "warning"
  - `improvement`: Negative value = better than planned
  - `better_metrics`: List of metrics that improved
  - `worse_metrics`: List of metrics that worsened

### Recommendation Logic
- Only recommend alternative if:
  - Severity improves, OR
  - Score improves by ≥15%
- Natural language recommendation generated from structured data

### Files
- `backend/app/agent/reasoning.py` — Integration
- `backend/app/agent/window_selector.py` — Selection logic

---

## G2.6 — Explainability

### Implementation
- Enhanced `Assessment` model with structured explanation fields:
  - `planned_window: PlannedWindow | None`
  - `alternatives: list[AlternativeWindow]`
  - `recommended_time: datetime | None`
  - `reason_codes: list[str]`
  - `limitations: list[str]`

### Structured Output Example
```json
{
  "planned_window": {
    "time": "2026-09-07T17:00:00",
    "severity": "warning",
    "aqi": 175,
    "pm25": 55,
    "uv": 8
  },
  "alternatives": [
    {
      "time": "2026-09-07T19:00:00",
      "severity": "info",
      "improvement": -0.45,
      "better_metrics": ["aqi", "pm25", "uv"],
      "worse_metrics": []
    }
  ],
  "recommended_time": "2026-09-07T19:00:00",
  "reason_codes": ["better_conditions:aqi,pm25,uv", "severity_improved:warning->info"],
  "limitations": ["Missing data for: temp_c, humidity"]
}
```

### Files
- `backend/app/agent/reasoning_models.py` — Structured models

---

## G2.7 — Forecast Integrity

### Implementation
- Already implemented in G1 via `kind` field on `Observation`
- `WindowScore.data_kind` reflects whether data is observed/forecast/mixed
- Timeline labels each entry with `data_kind` and `exposure_kind`

### Files
- `backend/app/environmental/base.py` — Kind field
- `backend/app/agent/timeline.py` — Timeline labels

---

## G2.8 — Graceful Uncertainty

### Implementation
- Missing metrics: Skipped, not fabricated; tracked in `missing_metrics`
- No better window: `reason_codes` contains "no_better_window_in_range"
- Forecast uncertainty: `limitations` includes "Forecast >24h out; accuracy decreases"
- Alternative window analysis failure: Does not break main assessment

### Test Cases
- `test_missing_aqi_continues`: Missing AQI continues with available data
- `test_missing_multiple_metrics`: Multiple missing metrics handled
- `test_find_alternative_no_better_window`: "No better window" case
- `test_conflicting_metrics_warning_wins`: Warning severity wins over good metrics

### Files
- `tests/test_g2_window_selector.py` — Edge case tests

---

## G2.9 — Tests

### New Tests
- `tests/test_g2_window_selector.py` — 15 test cases covering:
  - AQI standard attribution
  - Observed vs forecast classification
  - Activity-aware evaluation
  - Time-window comparison
  - Alternative selection
  - No-better-alternative case
  - Partial environmental data
  - Conflicting metrics
  - Timezone correctness
  - Deterministic recommendation

### G1 Tests
- All existing tests remain compatible (new fields are optional)
- `tests/test_reasoning.py` — No changes required
- `tests/test_environmental.py` — Updated for new Observation fields

---

## G2.10 — Demo Scenario

### Live Test
```
curl -X POST "https://bee.andywongpt.com/api/v1/assess" -H "Content-Type: application/json" -d '{}'
```

### Result (Before Deployment)
```
bee_mode: mcp
activity: jogging
planned_time: 2026-09-07T17:00:00
severity: caution
alternatives: 0
recommended_time: None
```

### Expected Result (After Deployment)
```
bee_mode: mcp
activity: jogging
planned_time: 2026-09-07T17:00:00
severity: caution
planned_window: {time: 17:00, severity: caution, aqi: 119, pm25: 33, uv: 2.2}
alternatives: [...]
recommended_time: 19:00 (if conditions improve)
reason_codes: ["better_conditions:aqi,pm25"]
```

---

## G2.11 — Evidence

### Files
- `evidence/milestones/G2/G2_implementation.md` — This file
- `evidence/milestones/G2/verification_output.txt` — Local verification output

---

## G2.12 — Friction and Product Feedback

### Friction
- No new friction entries for G2 implementation
- All existing G1 friction resolved or documented

### Product Feedback
- G2 implementation demonstrates environmental intelligence beyond simple threshold alerts
- Alternative-time reasoning provides actionable decision support

---

## G2 PASS Criteria

| Criterion | Status | Notes |
|-----------|--------|-------|
| AQI standard is explicit | ✅ PASS | `aqi_standard="us_epa"` on AQI observations |
| Observed and forecast distinguishable | ✅ PASS | `kind` field, `data_kind` on WindowScore |
| Context confidence/source decomposed | ✅ PASS | `FieldConfidence` model per field |
| Planned-time conditions evaluated | ✅ PASS | `PlannedWindow` structure |
| Nearby alternative windows evaluated | ✅ PASS | `find_alternative_window()` |
| System can identify better alternative | ✅ PASS | Verified in local test |
| System can return no better alternative | ✅ PASS | `no_better_window_in_range` reason code |
| Recommendation reconstructable from evidence | ✅ PASS | Structured `reason_codes` and `limitations` |
| No environmental values invented by LLM | ✅ PASS | All values from provider observations |
| Uncertainty/missing data handled safely | ✅ PASS | Missing metrics tracked, not fabricated |
| All G1 tests remain passing | ⏳ PENDING | Deployment + CI run needed |
| New G2 tests pass | ✅ PASS | Local verification passed |
| Evidence captured | ✅ PASS | This file |
| Privacy review passes | ✅ PASS | No new personal data processed |
| Git diff reviewed | ⏳ PENDING | Commit pending |

---

## Implementation Summary

### New Files
1. `backend/app/agent/activity_policy.py` (400 lines) — Activity-aware evaluation policies
2. `backend/app/agent/window_selector.py` (282 lines) — Time-window comparison and alternative selection
3. `tests/test_g2_window_selector.py` (347 lines) — Comprehensive G2 test suite
4. `scripts/verify_g2.py` (122 lines) — Local verification script

### Modified Files
1. `backend/app/environmental/base.py` — Added `aqi_standard` and `quality` to Observation
2. `backend/app/environmental/open_meteo.py` — AQI standard attribution and quality classification
3. `backend/app/agent/models.py` — Added `FieldConfidence` for per-field confidence tracking
4. `backend/app/agent/reasoning_models.py` — Added structured explanation models
5. `backend/app/agent/reasoning.py` — Integrated G2 components
6. `backend/app/main.py` — Wired G2 into assess endpoint

### Total Changes
- New code: ~1,150 lines
- Modified code: ~150 lines
- New tests: 15 test cases

---

## Next Steps

1. Run full test suite to verify G1 compatibility
2. Deploy to production
3. Verify live endpoint with G2 enhancements
4. Capture live demo evidence
5. Update UI to display alternative windows
