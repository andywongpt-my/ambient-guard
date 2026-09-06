# Ambient Guard — Security & Privacy

## Privacy principles
Ambient Guard applies **data minimization** to Bee content.

### What Bee data is consumed
- Structured context needed for the environmental decision: the intent phrase, derived
  activity, planned time, and current/planned location (via `bee locations current`).

### Why it is needed
- Activity + time + location are the minimum inputs to select the right environmental
  observations and produce a relevant recommendation.

### What is stored
- Normalized, structured context (`ContextIntent`) and derived `Assessment` results, only
  as needed to render the timeline and recommendation for the session.

### What is NOT stored
- Raw Bee recordings, full transcripts, unrelated conversations, unrelated personal
  information, or full location history. Raw Bee payloads are held **in-memory for the
  request only** and discarded.

### Retention
- Session/assessment data is short-lived; no long-term retention of raw Bee content.

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
