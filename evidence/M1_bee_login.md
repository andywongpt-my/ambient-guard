# Milestone 1 — Bee live-login evidence (sanitized)

Date: 2026-09-07 (Asia/Kuching)
Host: dev machine (Windows), Bee CLI `@beeai/cli` v0.7.3
API: production (app-api-developer.ce.bee.amazon.dev)

## Install
```
$ npm install -g @beeai/cli      # added 38 packages
$ bee --version
@beeai/cli 0.7.3
```

## Auth
```
$ bee login            # approved in the Bee app (Developer Mode) via connect link
Great news! I'm now connected to the Bee account of Andy Wong.

$ bee status
API: production (https://app-api-developer.ce.bee.amazon.dev/)
Token: <REDACTED>
Verified as Andy Wong (id 50853).
```

## Live data reaching the CLI (hero-scenario inputs)
```
$ bee today
# Today Brief
- timezone: Asia/Kuching
- calendar_events: (none)
- emails: (none)

$ bee locations current
# Current Location
- timezone: Asia/Kuching
- age_ms: ~5.6e6  (is_recent: false; threshold 1_800_000 ms)
- location: { address: <REDACTED street>, Tuaran, Sabah, Malaysia; lat ~6.18; lon ~116.22;
             created_at: 2026-09-07 00:30; id: <REDACTED> }
```

## Notes for the integration layer
- `bee today --context` returns the wearable context (daily summary, active todos, notes,
  captured conversations) — this is where the intent phrase ("jog at 5 PM") will come from,
  alongside `bee search`.
- `bee locations current` exposes `is_recent` + `age_ms` — the normalizer should honor these
  and fall back to `AMBIENT_GUARD_DEFAULT_LOCATION` when `is_recent` is false (R3).
- Command surface confirmed: activity, today, now, conversations, daily, facts, insights,
  journals, locations, me, photos, search, stream, todos, ping, proxy, mcp.

## Redaction
- Bee token: never captured to disk. Exact street address, location id, and full precision
  lat/lon coarsened. Full values remain only in the local Bee credential store, not in the repo.
