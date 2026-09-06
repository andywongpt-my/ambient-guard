# Ambient Guard — Architecture

> Personal Environmental Agent — Amazon Developer Hackathon 2026

## 1. System Overview

Ambient Guard is a personal environmental agent that turns your stated intentions
into proactive, evidence-backed environmental guidance. It ingests personal
context from a Bee wearable (paired with an Apple Watch) — conversations, todos,
locations, and daily summaries — and normalizes that raw signal into a structured
`ContextIntent` (what you plan to do, when, and where). In parallel, an
Environmental Layer pulls live weather, UV, and air-quality observations from
free public providers (Open-Meteo, OpenAQ). A Reasoning Engine fuses the personal
intent with the environmental picture, applies deterministic threshold rules, and
layers LLM synthesis on top — guarded so that no recommendation ships without at
least one concrete evidence item. The result is a human-readable recommendation
plus a timeline, served by a FastAPI backend and rendered in a single-screen
Next.js demo UI. The hero flow: you say "I plan to jog at 5 PM," and Ambient Guard
tells you whether that's a good idea — and why.

## 2. Architecture Diagram

```
 PERSONAL CONTEXT PATH
 ┌──────────────────────┐
 │  Apple Watch + Bee   │  (wearable capture: audio, activity, location)
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐   bee login / today / search /
 │     Bee CLI / MCP    │   locations current / conversations / todos
 │  (cli | mcp serve)   │   bee mcp serve  |  serve-http :8790
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Bee Integration Layer│   backend = cli | mcp | mock
 │ (AMBIENT_GUARD_BEE_  │   (selected via env var)
 │        MODE)         │
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Context Normalization│   → ContextIntent
 │        Layer         │     {activity, planned_time, location,
 └──────────┬───────────┘      intent_text, source_ref, confidence}
            │
            ▼
     ┌─────────────┐
     │ ContextIntent│──────────────┐
     └─────────────┘               │
                                   │
 ENVIRONMENTAL PATH                │
 ┌───────────────────────────────┐│
 │ Environmental Providers        ││
 │ • Open-Meteo weather + UV      ││
 │   (no API key)                 ││
 │ • Open-Meteo air-quality /     ││
 │   OpenAQ (PM2.5/PM10/AQI/      ││
 │   O3/NO2)                      ││
 │ • optional pollen              ││
 └──────────────┬────────────────┘│
                │                  │
                ▼                  │
 ┌───────────────────────────────┐│
 │ Environmental Layer            ││
 │ (normalized observations)      ││
 └──────────────┬────────────────┘│
                │                  │
                └────────┬─────────┘
                         │  (both feed the engine)
                         ▼
             ┌───────────────────────┐
             │    Reasoning Engine    │  threshold rules + LLM
             │  (guardrail: ≥1        │  synthesis
             │   evidence item)       │
             └───────────┬───────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │ Recommendation +       │
             │      Timeline          │
             └───────────┬───────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │   FastAPI Backend      │  /health
             │                        │  /api/v1/assess
             │                        │  /api/v1/timeline
             └───────────┬───────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │   React / Next.js UI   │  single demo screen
             └───────────────────────┘
```

## 3. Components

### 3.1 Bee Integration Layer

Sole boundary between Ambient Guard and the Bee wearable's data. It exposes one
internal interface and swaps its concrete backend based on `AMBIENT_GUARD_BEE_MODE`:

- **`cli`** — shells out to the Bee CLI. Documented surface only: `bee login`,
  `bee today`, `bee search`, `bee locations current`, `bee conversations`, `bee todos`.
- **`mcp`** — connects to Bee as an MCP server, over stdio (`bee mcp serve`) or HTTP
  (`bee mcp serve-http --token <≥32chars> --port 8790`, bound to `127.0.0.1`).
- **`mock`** — canned fixtures for local development, tests, and offline demos.

Selecting the backend by env var keeps the demo reproducible (`mock`) while allowing
a live device path (`cli` / `mcp`) with no code changes. Raw Bee payloads are never
persisted (see privacy).

### 3.2 Context Normalization Layer

Consumes raw Bee output and distills a single structured `ContextIntent`:

| Field          | Description                                                     |
|----------------|-----------------------------------------------------------------|
| `activity`     | Inferred activity (`jogging`, `commute`, `outdoor_lunch`, …)    |
| `planned_time` | When it's planned (absolute or resolved from relative phrasing) |
| `location`     | Where it happens (from `bee locations current` or intent text)  |
| `intent_text`  | The original phrase that produced this intent                   |
| `source_ref`   | Reference back to the originating Bee record (traceability)     |
| `confidence`   | Normalization confidence (0.0–1.0)                              |

`source_ref` and `confidence` make every downstream recommendation auditable.

### 3.3 Environmental Layer

Each source implements a common `Provider` protocol; the layer wraps every call with
timeout, retry-with-backoff, response validation, unit normalization, source
attribution, and a short-lived cache. Providers:

- **Open-Meteo (weather + UV)** — temperature, wind, precipitation, UV index. No key.
- **Open-Meteo air-quality / OpenAQ** — PM2.5, PM10, AQI, O₃, NO₂.
- **Pollen (optional)** — pollen indices when available.

### 3.4 Reasoning Engine

Two stages: (1) **threshold rules** encode domain limits (AQI > 150 unhealthy for
exertion; UV ≥ 8 sun protection; PM2.5 above threshold discourages sustained cardio)
producing structured evidence items; (2) **LLM synthesis** composes evidence +
`ContextIntent` into a natural-language recommendation and timeline. **Guardrail:**
no recommendation is emitted without ≥1 evidence item — every claim ties back to a
normalized observation and its source.

### 3.5 FastAPI Backend

- **`GET /health`** — liveness/readiness probe.
- **`POST /api/v1/assess`** — core endpoint; resolves a `ContextIntent`, invokes the
  Environmental Layer + Reasoning Engine, returns recommendation + evidence.
- **`GET /api/v1/timeline`** — environmental timeline over the relevant window.

### 3.6 Next.js UI

A single-screen React / Next.js demo showing intent, evidence-backed recommendation,
and timeline. Deliberately minimal to keep the hackathon demo focused.

## 4. Tech Stack

| Layer     | Choice                                              |
|-----------|-----------------------------------------------------|
| Backend   | Python + FastAPI                                    |
| Frontend  | React / Next.js                                     |
| Database  | PostgreSQL                                          |
| Packaging | Docker Compose                                      |
| Ingress   | nginx reverse proxy (front of backend + UI)         |
| Host      | Dedicated Fedora server (`meow`)                    |

## 5. Hero Scenario Walkthrough — "I plan to jog at 5 PM"

1. **Capture.** Bee records the utterance "I plan to jog at 5 PM."
2. **Retrieve.** Bee Integration Layer pulls records via `bee conversations`/`bee today`
   and location via `bee locations current`.
3. **Normalize.** → `ContextIntent{activity=jogging, planned_time=17:00, location=…,
   intent_text="I plan to jog at 5 PM", source_ref=…, confidence=0.9}`.
4. **Fetch environment.** `POST /api/v1/assess` queries Open-Meteo (weather+UV) and
   air-quality (PM2.5/PM10/AQI/O₃/NO₂) for that location + ~17:00 window.
5. **Reason.** Threshold rules fire (e.g. AQI 165 > exertion limit; UV 7 high) → evidence
   items; guardrail satisfied; LLM synthesis runs.
6. **Recommend.** One grounded recommendation ("Air quality at 5 PM is unhealthy (AQI 165)
   — consider a post-sunset jog…"), each statement linked to evidence + source.
7. **Timeline.** `GET /api/v1/timeline` shows surrounding hours (AQI improving toward 7 PM).
8. **Present.** Next.js UI renders intent, evidence-backed recommendation, and timeline.
