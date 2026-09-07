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

### Why it is needed
- Activity + time + location are the minimum inputs to select the right environmental
  observations and produce a relevant recommendation.
- G3: Personal constraints enable feasibility evaluation (e.g., "Cannot jog at 7 PM if you have dinner at 7 PM")

### What is stored
- **Nothing is persisted.** Verified in the M7 review (evidence/M7_reliability_security_privacy.md):
  the backend has no database code — Bee data (raw or normalized) and assessments are held
  **in-memory for the single request only** and discarded when the response returns.

### What is NOT stored
- Raw Bee recordings, full transcripts, unrelated conversations, unrelated personal
  information, full location history, raw todo text, raw conversation content.
- G3: The `raw_text` field in `PersonalConstraint` is **never persisted** — it exists only during
  the extraction phase for debugging and is not included in `to_dict()` serialization.

### Retention
- Zero server-side retention today. If persistence is added later, it must come with an
  explicit, documented retention policy and store normalized structured data only — never raw
  Bee content.

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
