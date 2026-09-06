# Milestone 3 — Context normalization (sanitized)

Date: 2026-09-07 · GET /api/v1/context · AMBIENT_GUARD_BEE_MODE=cli (live)

## Behavior on LIVE Bee data (redacted)
```json
{
  "activity": null,
  "planned_time": null,
  "location": "<REDACTED addr>, Tuaran",
  "latitude": 6.18, "longitude": 116.22,
  "location_is_recent": true,
  "intent_text": "Andy tests if the device recognizes his voice.",
  "source_ref": { "provider": "bee", "ref_id": "<REDACTED>",
                  "observed_at": "2026-09-07T02:07:47", "location": "<REDACTED addr>, Tuaran" },
  "confidence": 0.5,
  "notes": [
    "intent text from Bee ref <REDACTED>",
    "activity not determined",
    "planned_time not determined",
    "location from Bee (recent)"
  ]
}
```
**Key point:** the user's real Bee feed has no jog/time phrase, so `activity` and
`planned_time` are honestly `null` — the layer does NOT invent them (FR-2.3). The `notes`
array traces exactly how each field was derived. Location came from a fresh Bee GPS fix.

## Hero scenario (mock fixture with a real 'jog at 5 PM' utterance)
Extracts: activity=jogging, planned_time=17:00, location from Bee, confidence >= 0.9,
source_ref.ref_id = search hit id.

## Tests (mock mode, CI-safe)
```
$ AMBIENT_GUARD_BEE_MODE=mock pytest -q
23 passed, 1 skipped
```
Covers activity match, 12h/24h/relative time (+ tomorrow rollover), location
recent/stale/fallback (R3), the no-inference case, and the endpoint.
