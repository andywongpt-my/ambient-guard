# Milestone 4 — Reasoning engine + closed vertical slice

Date: 2026-09-07 · POST /api/v1/assess

## Full pipeline
Bee context -> ContextIntent (M3) + location -> environmental observations (M2)
-> ReasoningEngine -> ONE grounded recommendation with evidence.

## Hero recommendation (jogging @ 17:00; AQI 165, UV 8, 33°C)
```
TEXT: Consider rescheduling jogging at 17:00 or moving it indoors: AQI 165 is
      unhealthy — limit sustained outdoor exertion; UV index 8 is very high —
      sun protection strongly advised; Temperature 33°C is hot. If you go, keep
      it short and take precautions.
SUMMARY: Assessed jogging (outdoor=True) at 17:00 against 3 environmental
      reading(s); worst severity: warning. Framed as precautionary
      environmental guidance, not medical advice.
CONFIDENCE: 0.72
EVIDENCE:
  - warning: AQI 165 is unhealthy — limit sustained outdoor exertion
  - warning: UV index 8 is very high — sun protection strongly advised
  - caution: Temperature 33°C is hot
```
Every clause traces to an Observation with source attribution.

## Guardrail (FR-4.2)
- >=1 evidence item is always present. When no threshold trips, the engine cites
  the reassuring readings as info-level evidence ("all clear" is still grounded).
- With zero observations, the engine RAISES (ReasoningError -> HTTP 502) rather than
  inventing advice.

## Tests (mock mode, targeted file)
```
$ pytest -q tests/test_reasoning.py
5 passed
```
Covers: warning tier, all-clear guardrail, no-observation refusal, caution tier,
and the full /api/v1/assess slice (mock Bee + respx-mocked Open-Meteo).

Note: ran targeted test files only due to critically low host memory; full-suite
regression pending memory recovery.
