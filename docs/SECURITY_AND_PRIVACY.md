# Ambient Guard — Security & Privacy

## Privacy principles
Ambient Guard applies **data minimization** to Bee content.

### What Bee data is consumed (G1/G2)
- Structured context needed for the environmental decision: the intent phrase, derived
  activity, planned time, and current/planned location (via `bee locations current`).

### What Bee data is consumed (G3)
- **Personal constraints:** Active todos with timing information (e.g., "Dinner at 7 PM")
- **Personal preferences:** Recent conversation summaries containing preference patterns
- **Data minimization applied:**
  - Only first 3 recent conversations are checked (not full history)
  - Only constraints relevant to timing decisions are extracted
  - Raw text is never persisted (see Privacy-by-Design below)

### What Bee data is consumed (G7)
- **Guard-worthy activities:** Upcoming outdoor activities with specific planned times
- **Activity type, time, location:** Minimum data to monitor environmental conditions
- **Data minimization applied:**
  - Only outdoor activities qualify (jogging, cycling, hiking, etc.)
  - Only future events are monitored
  - Raw Bee source references are hashed, never stored as raw text

### Why it is needed
- Activity + time + location are the minimum inputs to select the right environmental
  observations and produce a relevant recommendation.
- G3: Personal constraints enable feasibility evaluation (e.g., "Cannot jog at 7 PM if you have dinner at 7 PM")
- G7: Proactive monitoring requires persisting minimal state to track decision changes over time

### What is stored (G1-G4)
- **Nothing is persisted for request-only mode.** Verified in the M7 review:
  the backend has no database code for these paths — Bee data (raw or normalized) and 
  assessments are held **in-memory for the single request only** and discarded when the 
  response returns.

### What is stored (G7)
- **Guard Mode requires minimal persistence** for proactive monitoring:
  - Guard: activity type, planned time, location coordinates, lifecycle status
  - Guard Assessment: decision state, environmental summary, reason codes
  - Guard Alert: change type, reason codes, evidence summary
- **Bee source references are HASHED** (SHA-256), never stored as raw text
- **Only normalized data is persisted:**
  - Activity type (e.g., "jogging")
  - Planned time (ISO timestamp)
  - Location coordinates (lat/lon)
  - Decision state enum values
  - Reason code strings

### What is NOT stored
- Raw Bee recordings, full transcripts, unrelated conversations, unrelated personal
  information, full location history, raw todo text, raw conversation content.
- G3: The `raw_text` field in `PersonalConstraint` is **never persisted**
- G7: Raw Bee source text is **hashed before storage**, never persisted as-is

### Retention (G7)
- **Guards expire** after planned time + 2-hour grace period
- **Data retention:** 7 days after guard expiration
- **Automatic cleanup:** Guards and all related data (assessments, alerts) are deleted
  after the retention period
- **Manual deletion:** Users can cancel guards at any time via API

### Why persistence is necessary (G7)
Guard Mode monitors environmental decisions over time and must:
- Track when a guard was created and its baseline assessment
- Compare new assessments against previous ones
- Detect material decision changes (e.g., "conditions worsened")
- Generate alerts only when decisions materially change
- Show decision history for transparency

This requires **minimal state persistence** to function, unlike request-only mode.

## G3: Privacy-by-Design

### Data Minimization Pipeline (G3.10)
```
Raw Bee Context (today_context)
    ↓ [extract only relevant fields]
Active Todos (with timing info)
Recent Conversations (first 3 only)
    ↓ [extract constraints/preferences]
PersonalConstraint (type, time, source_type, source_id)
PersonalPreference (type, value, source_type)
    ↓ [discard raw text]
Output: Only normalized constraint/preference records
```

### What is queried
- `bee today_context`: Active todos and recent conversations
- Only timing-relevant fields are read

### What is transformed
- Todo text → Constraint type + time (e.g., "Dinner at 7 PM" → `FIXED_COMMITMENT` at 19:00)
- Conversation summary → Preference (e.g., "I prefer running after work" → `PREFERRED_ACTIVITY_WINDOW: after work`)

### What is retained
- Constraint type, time, source_type, source_id, confidence level
- Preference type, value, source_type, confidence level
- **NOT retained:** raw todo text, raw conversation content, unrelated Bee data

### What is discarded immediately
- Raw text after constraint extraction
- Todos without timing relevance
- Conversations beyond the first 3
- All Bee context after the request completes

### Retention duration
- Zero persistence. All personal context exists only in-memory during request processing.

### Context Provenance (G3.11)
Every personal constraint carries provenance:
```json
{
  "constraint_type": "fixed_commitment",
  "value": "2026-09-07T19:00:00",
  "source_type": "bee_todo",
  "source_id": "12345",
  "confidence": "high"
}
```

### Context Freshness (G3.12)
Stale context is automatically filtered:
- Todos older than 24 hours → stale, not applied
- Conversations older than 7 days → stale, not applied for preferences
- Daily summaries older than 3 days → stale, not applied

## Security controls
- **No secrets in the repo.** Provider keys and Bee tokens live in env / untracked files;
  `.gitignore` excludes `.env`, credential files, and evidence containing secrets.
- **Bee MCP HTTP transport** (if used) requires a bearer token ≥32 chars and binds to
  `127.0.0.1` only.
- **Log hygiene:** never log secret values or raw personal Bee content; scrub tokens.
- **Evidence redaction:** sanitize logs / API metadata before committing under `evidence/`.
- **Transport:** deployment behind nginx with HTTPS termination on the `meow` server.

## Safety framing
- Ambient Guard is **not** a medical diagnosis system. Recommendations are **informational
  / precautionary** environmental guidance only.
- Absent a physical personal sensor, output uses "estimated environmental exposure" /
  "nearby environmental conditions" — never a claim of measuring the exact air inhaled.
