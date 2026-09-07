# Ambient Guard — Demo Plan (Under 3 Minutes)

**Project:** Ambient Guard — Personal Environmental Agent powered by Bee
**Event:** Amazon Developer Hackathon 2026 · **Total runtime:** ≤ 3:00

## Demo Objective

Prove, live and in one continuous flow, that Ambient Guard turns **real Bee-derived
personal context** into **one grounded environmental recommendation** backed by evidence
and a timeline. Every claim on screen must trace to a source.

## Mandatory On-Screen Sequence (in order)

1. **Bee-derived personal context** — the real captured phrase and its source.
2. **Current / forecast environmental conditions** — PM2.5, UV, temperature, humidity, weather.
3. **The Ambient Guard recommendation** — a single, clear call to action.
4. **Evidence** — the observations and thresholds that justify the recommendation.
5. **Environmental timeline** — observed vs forecast, labeled with timestamps.

## Hero Scenario

> Real Bee context: **"I plan to jog at 5 PM"**

```
Bee context "I plan to jog at 5 PM"
  → extract: activity=jogging, planned_time=17:00, location=<user location>
  → retrieve: PM2.5 / UV / temperature / humidity / weather (current + 17:00 forecast)
  → reason: combine context + observations + time + location
  → ONE grounded recommendation + supporting evidence + confidence
```

## Second-by-Second Script (0:00–3:00)

| Time | On screen | Narration |
|------|-----------|-----------|
| 0:00–0:15 | Title card "Ambient Guard — powered by Bee" → app home. | "Ambient Guard is a personal environmental agent. It listens to your real day through Bee and tells you when the world around you is safe for what you're about to do." |
| 0:15–0:35 | **Bee context panel** highlights real captured line "I plan to jog at 5 PM" + Bee source badge + timestamp. | "This isn't a form I filled in. Bee captured this from my actual day: I plan to jog at 5 PM." |
| 0:35–0:55 | **Context extraction** animates: activity=jogging, planned_time=17:00, location resolved, each with a from-Bee/derived tag. | "Ambient Guard extracts structured context — activity, time, location — and only what the data supports. No guessing." |
| 0:55–1:30 | **Conditions panel** populates: PM2.5, UV, temperature, humidity, weather — each with source + timestamp; current AND 17:00 forecast. | "It pulls the environment for that time and place — air quality, UV, temperature, humidity, weather — each tagged with its source and when it was measured." |
| 1:30–2:00 | **Recommendation card**: ONE headline recommendation + confidence badge. | "Here's the payoff: one clear recommendation for my 5 PM jog — grounded in the data, with a confidence level." |
| 2:00–2:35 | **Evidence drawer** expands: the observations + thresholds behind the call, each source-linked. | "And it shows its work — the exact readings and thresholds. Nothing is asserted without evidence." |
| 2:35–2:55 | **Timeline** scrolls hourly from now through evening; observed/forecast/estimate labels; 17:00 marked. | "The timeline puts it in context — what's observed, what's forecast, and where my 5 PM sits." |
| 2:55–3:00 | Return to recommendation card + tagline. | "Real context in. One grounded answer out. That's Ambient Guard." |

## Shot List

1. **S1** Title card (0:00). 2. **S2** Bee context panel (0:15). 3. **S3** Extraction overlay (0:35).
4. **S4** Conditions panel (0:55). 5. **S5** Recommendation card (1:30). 6. **S6** Evidence drawer (2:00).
7. **S7** Timeline (2:35). 8. **S8** Closing card (2:55).

## Pre-Demo Checklist (run ≤15 min before recording)

**Bee**
- [ ] Bee account logged in; session valid (not expired).
- [ ] Hero line "I plan to jog at 5 PM" present in the live Bee feed (or freshly re-captured).
- [ ] Bee CLI/MCP reachable from the demo machine.
- [ ] Capture timestamp displays correctly.

**Environmental providers**
- [ ] Air-quality (PM2.5), UV, and weather providers each return fresh data within timeout.
- [ ] Fallback path NOT triggered for the hero location.
- [ ] Source attribution + timestamps render on each metric.

**Application**
- [ ] Server up; `/health` green; frontend loads with no console errors.
- [ ] Full hero pipeline dry-run produces the expected single recommendation.
- [ ] Evidence drawer + timeline populate with real data, not placeholders.

**Recording**
- [ ] Screen recorder + audio checked; zoom set so all five panels are legible.
- [ ] Machine clock consistent with the scenario; one clean take under 3:00.

## Fallback if live data fails during recording

- Keep a **captured-real-data snapshot** of the hero pipeline (recorded earlier same day) as backup, labeled real-but-cached — **never fabricate readings**.
- If one provider is down, show the fallback/attribution behavior honestly as a reliability feature.


---

## Live reconciliation (M8 — matches the shipped product)

The plan above still holds; notes for demoing the LIVE site [bee.andywongpt.com](https://bee.andywongpt.com):

- **Intent source:** the live hero intent comes from a real Bee **todo** ("Go jogging at 5 PM",
  id 28703772) via `activeTodos`, since spoken-conversation capture has sync lag and `bee_search`
  is currently unreliable server-side (FR-007). The recommendation, environment, and location are
  all live/real. A spoken-conversation capture can be shown as an even-more-authentic variant if it
  has synced.
- **Timeline panel** now shows two label columns — **Data** (observed/forecast) and **Exposure**
  (estimate — location/API-based, never a personal measurement), and highlights the planned hour
  when it falls in the window. For the demo, request a window that includes the planned time.
- **Latency:** live assess is slower than local (~few s) due to the Cloudflare Tunnel + MCP
  round-trip to real Bee — narrate over it or pre-warm with one call before recording.
- **Evidence to show:** `evidence/screenshots/M6_demo_flow_live.gif` is the recorded live flow;
  `evidence/INDEX.md` maps all evidence.
- **Pre-demo:** confirm `curl -s -XPOST https://bee.andywongpt.com/api/v1/assess -d '{}'` returns
  `bee_mode=mcp` + `activity=jogging`; if the server Bee token expired, re-run the keyring-unlock
  login (see `docs/DEPLOYMENT.md`).
