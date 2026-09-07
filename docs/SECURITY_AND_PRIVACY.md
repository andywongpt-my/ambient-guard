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
- **Nothing is persisted.** Verified in the M7 review (evidence/M7_reliability_security_privacy.md):
  the backend has no database code — Bee data (raw or normalized) and assessments are held
  **in-memory for the single request only** and discarded when the response returns. A Postgres
  service exists in compose for future use but is currently unused by the app.

### What is NOT stored
- Raw Bee recordings, full transcripts, unrelated conversations, unrelated personal
  information, full location history — and, currently, not even the normalized `ContextIntent`
  or `Assessment` (no persistence layer is wired).

### Retention
- Zero server-side retention today. If persistence is added later, it must come with an
  explicit, documented retention policy and store normalized structured data only — never raw
  Bee content.

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
