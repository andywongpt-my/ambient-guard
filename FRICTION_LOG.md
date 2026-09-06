# Ambient Guard — Developer Friction Log

This document records genuine developer-experience friction encountered while building **Ambient Guard — A Personal Environmental Agent powered by Bee**.

The purpose of this log is to provide useful, reproducible feedback about the tools, APIs, SDKs, documentation, and development workflows used during the project.

Entries are written when issues occur. We do not fabricate errors, manufacture problems, or exaggerate friction. Entries are append-only; history is never rewritten.

---

# Scope

Relevant friction may include genuine issues encountered with: Amazon Bee, Bee CLI, Bee MCP, Bee Agent Skills, Kiro, Kiro Crew, AWS development tooling, environmental APIs, MCP integrations, deployment tooling, authentication / developer onboarding, and SDKs/APIs used directly by Ambient Guard.

Normal bugs caused by Ambient Guard's own application code should generally NOT be included unless an external tool or unclear developer experience materially contributed to the issue.

---

# Severity Scale

- **S1 — Minor**: small inconvenience; development continues without meaningful interruption (unclear wording, minor doc gap, unnecessary manual step).
- **S2 — Moderate**: requires investigation or an unclear/undocumented workaround (unexpected config behavior, missing setup guidance, tool state not refreshing, confusing API response).
- **S3 — Major**: blocks an important development task until a workaround is found (integration cannot proceed, auth repeatedly fails, required MCP tool cannot be discovered, SDK differs significantly from docs).
- **S4 — Critical**: prevents a required competition integration or makes the intended workflow unusable (live Bee data unreachable via the documented path; required tooling consistently fails without a viable workaround).

---

# Entry Template

## FR-XXX — Short descriptive title

**Date / Time**: YYYY-MM-DD HH:MM MYT
**Tool / API / SDK**: Product · Version · Environment

### Task attempted
### Why this mattered
### Steps taken
### Expected result
### Actual result
### Severity
### Evidence
### Investigation
### Root cause
### Workaround
### Outcome  (Resolved | Partially resolved | Unresolved | Deferred)
### Development impact
### Actionable suggestion

---

# Genuine Friction Entries

## FR-001 — Bee CLI not installed on any host; login prerequisites not obvious

**Date / Time**: 2026-09-06 ~23:40 → 2026-09-07 02:03 MYT
**Tool / API / SDK**: Bee CLI (`@beeai/cli`) · v0.7.3 · Windows dev machine + Fedora 43 server (`meow`)

### Task attempted
Validate current Bee integration capability and establish a live Bee → Ambient Guard data path (Milestone 1).

### Why this mattered
The primary competition track requires REAL Bee data consumed at runtime; a README-only integration does not count. M1 gates all downstream work.

### Steps taken
1. Checked for the `bee` binary on the dev machine and on `meow` (`which bee` / `Get-Command bee`).
2. Read the Bee docs (docs.bee.computer/docs, /docs/cli, /docs/mcp).
3. Installed the CLI with `npm install -g @beeai/cli`.
4. Ran `bee login` and approved the connect link in the Bee app (Developer Mode).
5. Verified with `bee status`, `bee today`, `bee locations current`.

### Expected result
A `bee` CLI present, so live Bee → app integration could be proven.

### Actual result
`bee` was not installed on either host, and a Bee account login was also required and not yet established. The install command (`npm install -g @beeai/cli`) is on the docs homepage; the dedicated `/docs/cli` page intermittently failed to load (see FR-002). Developer Mode (tap app version 5× in Settings) is a prerequisite for `bee login`.

### Severity
**S3 — Major.** The highest-priority milestone could not proceed until the CLI was installed and a login established; scaffolding (M0) was unaffected.

### Evidence
- `which bee` returned nothing on both hosts.
- `bee status` after login: `Verified as Andy Wong (id 50853)` (token redacted).
- Sanitized: `evidence/M1_bee_login.md`, `evidence/M1_bee_ingress.md`.

### Investigation
Confirmed via docs that the CLI must be installed and `bee login` run on the host; auth is stored per-host. Verified live data retrieval afterward.

### Root cause
Expected onboarding gap — the tooling was simply not yet installed and the account not yet linked. Hardware/account prerequisites for `bee login` are not surfaced prominently up front.

### Workaround
During setup, developed against a mock Bee backend gated behind `AMBIENT_GUARD_BEE_MODE=mock`, kept strictly separate from the live demo path.

### Outcome
**Resolved.** CLI installed, `bee login` verified, and real data reaches the app via `GET /api/v1/bee/context` (`AMBIENT_GUARD_BEE_MODE=cli`).

### Development impact
Briefly blocked M1; did not delay M0/M2 scaffolding. Resolved same session.

### Actionable suggestion
On the CLI's getting-started page (not only the homepage), state the prerequisites for `bee login` up front and in order: (1) latest Bee app installed and signed in, (2) Developer Mode enabled by tapping the app version five times, (3) approve the connect link. This removes a guess about why `bee login` cannot complete.

---

## FR-002 — `bee login --no-wait` prints the link but does not finalize the approved session

**Date / Time**: 2026-09-07 02:03 MYT
**Tool / API / SDK**: Bee CLI (`@beeai/cli`) · v0.7.3 · Windows dev machine

### Task attempted
Complete `bee login` non-interactively by surfacing the auth link to the device owner, then confirming the session once approved.

### Why this mattered
An agent-driven setup should not block a shell for ~5 minutes; `--no-wait` looked like the right non-blocking path to print the link and finish later.

### Steps taken
1. `bee login --no-wait` → printed the connect link and exited.
2. Approved the connection in the Bee app.
3. Re-ran `bee login --no-wait` and `bee status` to confirm.

### Expected result
After approval, a subsequent `--no-wait` invocation (or `bee status`) would recognize the approval and finalize the session.

### Actual result
The second `--no-wait` re-printed the still-pending link and `bee status` stayed `Not logged in`. Only the blocking `bee login` (which polls after approval) actually claimed the token and completed the session.

### Severity
**S2 — Moderate.** An undocumented behavioral nuance; a clear workaround existed once identified.

### Evidence
`bee status` remained `Not logged in` after two `--no-wait` runs; the blocking `bee login` then reported `Great news! I'm now connected to the Bee account of Andy Wong.`

### Investigation
Compared `--no-wait` vs blocking `bee login` behavior and `bee login --help` (which lists `--no-wait`, `--qr`, `--token`, `--token-stdin`, `--proxy`).

### Root cause
`Root cause not conclusively identified` from the outside, but observationally `--no-wait` starts/prints the request without a token-claim/poll step, so it does not finalize an already-approved session on a later invocation.

### Workaround
Run the blocking `bee login` (bounded by a timeout) after the owner approves; it polls and claims the token. `bee status` then confirms.

### Outcome
**Resolved.** Login completed via the blocking path.

### Actionable suggestion
Document (in `bee login --help` and the CLI docs) that `--no-wait` only initiates the request and prints the link; to finalize an approved session, run `bee login` (blocking) or have `--no-wait` re-check and claim an already-approved request on a subsequent call. Even a one-line note ("`--no-wait` does not poll; re-run `bee login` to finish") would remove the ambiguity.

---

## FR-003 — docs.bee.computer/docs/cli intermittently failed to load

**Date / Time**: 2026-09-07 02:00 MYT
**Tool / API / SDK**: Bee documentation site (docs.bee.computer) · web

### Task attempted
Read the Bee CLI reference page for the exact install command and login flags.

### Why this mattered
Needed the authoritative install command and `login` options to script the integration correctly.

### Steps taken
1. Fetched `https://docs.bee.computer/docs/cli` (failed repeatedly).
2. Fetched `https://docs.bee.computer/` (succeeded — carried the `npm install -g @beeai/cli` command).
3. Fetched `https://docs.bee.computer/docs/mcp` (succeeded — full CLI/MCP tool catalog).

### Expected result
The `/docs/cli` page loads reliably like the other doc pages.

### Actual result
`/docs/cli` returned a transport error on multiple attempts within a short window while sibling pages loaded fine.

### Severity
**S1 — Minor.** The needed information was available on adjacent pages; no real delay.

### Evidence
Repeated `error sending request for url (https://docs.bee.computer/docs/cli)` while `/` and `/docs/mcp` returned full content.

### Root cause
`Root cause not conclusively identified` (likely a transient CDN/edge hiccup for that path).

### Workaround
Used the homepage (install command) and `/docs/mcp` (command catalog) instead.

### Outcome
**Resolved** (transient).

### Actionable suggestion
None material — if the `/docs/cli` path shows recurring edge errors, verify its cache/routing configuration matches the sibling doc pages.

---

# Submission Review Checklist

Before submitting this friction log:

- [ ] Remove all fake/example entries
- [x] Confirm every event genuinely happened
- [x] Remove credentials and secrets
- [x] Remove unnecessary personal Bee data
- [x] Ensure each issue includes expected vs actual behavior
- [x] Ensure severity is justified
- [x] Include workaround where one exists
- [x] Include an actionable recommendation
- [x] Ensure evidence references are valid
- [x] Ensure wording is factual rather than emotional
- [x] Ensure unresolved issues are clearly marked unresolved

---

# Summary

_Completed near submission._

## Tools covered
- Bee: CLI v0.7.3 (install, login, today/locations/search); docs site
- Kiro Crew: —
- AWS tooling: —
- Environmental APIs: —
- Deployment: —
- Other: —

## Total genuine friction events
- S1: 1
- S2: 1
- S3: 1
- S4: 0

## Most important developer-experience improvement
Surface `bee login` prerequisites (app installed + Developer Mode + approve link) prominently on the CLI getting-started page, and clarify that `--no-wait` does not finalize an approved session (FR-001, FR-002).

## Most valuable tool experience
To be completed from actual development experience near submission.
