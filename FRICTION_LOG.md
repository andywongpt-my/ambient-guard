# Ambient Guard — Developer Experience Friction Log

**Project:** Ambient Guard · Amazon Developer Hackathon 2026

## Policy

This log records **genuine** developer-experience friction encountered while building
Ambient Guard with external tooling — Bee / Bee CLI / Bee MCP, Kiro / Kiro Crew, AWS
tooling, third-party APIs/SDKs, and deployment infrastructure.

Rules for every entry:

- **Genuine only.** Written *only* when a real issue actually occurred during real work.
- **Never fabricated.** Do not invent friction, embellish severity, or file speculative entries.
- **Never manufactured.** Do not intentionally break/misconfigure a tool to generate an entry.
- **Not our bugs.** Ambient Guard's own application defects are **not** external tooling friction.
- **Never rewrite history.** Entries are append-only and immutable; corrections are new notes.

---

## Entry Template

```
timestamp:
tool/API/SDK:
version (if available):
task attempted:
steps taken:
expected result:
actual result:
severity:
evidence:
investigation:
workaround:
outcome:
development impact:
actionable suggestion:
```

---

## Entries

### 2026-09-06 — Bee CLI not installed on any host

```
timestamp: 2026-09-06
tool/API/SDK: Bee CLI
version (if available): unknown / not yet installed
task attempted: validate current Bee integration capabilities for the project
steps taken: checked for the `bee` binary locally on the Windows dev machine and on the remote Fedora deployment server (meow) via `which bee` / `Get-Command bee`
expected result: bee CLI present so we can prove live Bee->app integration
actual result: bee CLI is NOT installed on either the dev machine or the server; a Bee account login (`bee login`) is also required and not yet established
severity: High (Milestone 1, the highest-priority milestone, depends on real Bee data)
evidence: command output: `which bee` returned nothing on both hosts (see evidence/ when captured)
investigation: read the official Bee docs at docs.bee.computer/docs/cli and /docs/mcp — the CLI must be installed and `bee login` run on the host, after which it exposes `bee today`, `bee search`, `bee locations current` and an MCP server (`bee mcp serve`)
workaround: proceed with a mock Bee backend gated behind AMBIENT_GUARD_BEE_MODE=mock for isolated development/testing while the real login is arranged; keep the mock strictly separate from the live demo path
outcome: open — real Bee login still to be established
development impact: blocks completion of Milestone 1 until resolved; does not block M0/M2 scaffolding
actionable suggestion: Bee docs could state hardware/account prerequisites for `bee login` more prominently up front
```

**Resolution note (2026-09-07, append-only):** RESOLVED. Installed `@beeai/cli` v0.7.3 via
`npm install -g @beeai/cli` (the install command is on the docs homepage, not the `/docs/cli`
page, which intermittently failed to load — minor friction). `bee login` completed after
approving the connect link in the Bee app; `bee status` verified as Andy Wong (id 50853).
`bee today` and `bee locations current` return real data. Secondary friction: `bee login`
polls/blocks (~5 min); `--no-wait` only prints the link and does NOT finalize the approved
session — the blocking `bee login` (or re-running it) is what claims the token. Sanitized
evidence: `evidence/M1_bee_login.md`.
