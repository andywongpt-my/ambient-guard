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

## FR-004 — `bee login` cannot persist credentials on a headless server (no keyring/D-Bus, no file fallback)

**Date / Time**: 2026-09-07 04:00–04:12 MYT
**Tool / API / SDK**: Bee CLI (`@beeai/cli`) · v0.7.3 · Fedora 43 server (`meow`), headless SSH session

### Task attempted
Authenticate `bee` on the deployment server so the containerized backend can consume live
Bee data via `bee mcp serve-http` (making https://bee.andywongpt.com show real Bee context).

### Why this mattered
The public demo runs on the server, not the dev machine. For the server to serve REAL Bee
data (the primary-track requirement), the server's `bee` must be logged in.

### Steps taken
1. Installed `@beeai/cli` 0.7.3 on the server.
2. Ran `bee login` over SSH → `The name is not activatable (code: 2)`; fell through to help.
3. Installed `dbus-daemon` + `gnome-keyring` (sudo).
4. Ran `bee login` wrapped in `dbus-run-session` + `gnome-keyring-daemon --unlock`.
5. Started `bee mcp serve-http --port 8790 --token <32+>` and called `bee_get_current_location`.

### Expected result
`bee login` stores credentials (as it does on a desktop), and `bee status` / the MCP server
report the account as logged in.

### Actual result
- Bare `bee login`: `The name is not activatable` (no session D-Bus / Secret Service).
- With `dbus-run-session` + keyring: keyring tried to raise a **GUI unlock prompt**
  (`gcr-prompter: cannot open display`) and reported `.../collection/login … does not exist`.
- Even after a browser authorization, a new shell and the MCP server both report
  `Not logged in`. `bee` writes **no config/token file** (`~/.config/bee*`, `~/.bee*` absent) —
  it relies solely on the OS keyring, so with no working keyring the login never persists.
- `bee mcp serve-http` runs and authenticates the bearer token, but every tool call returns
  `Not logged in. Run "bee login" first.`

### Severity
**S3 — Major.** Blocks live Bee on the server via the documented `login` flow; a workaround
(token-based login, or running the live component on a desktop host) exists.

### Evidence
`~/bee_login.log` on the server: `The name is not activatable (code: 2)`, `gcr-prompter …
cannot open display`, `org.gnome.keyring.SystemPrompter exited with status 1`,
`/org/freedesktop/secrets/collection/login … does not exist (code: 19)`. MCP tool response:
`{"result":{"content":[{"type":"text","text":"Not logged in. Run \"bee login\" first."}],"isError":true}}`.

### Investigation
Confirmed the server SSH session has no `XDG_RUNTIME_DIR` and no session bus; `dbus-launch`
was absent until installed. Verified `bee` stores no plaintext token file, so keyring is the
only credential store. `bee login --token` / `--token-stdin` exist and bypass the interactive
keyring OAuth, but require a Bee **account** access token (distinct from the MCP bearer token).

### Root cause
`bee login` depends on an OS Secret Service (keyring over D-Bus) with no file-based fallback.
On a headless server that backend isn't running, and `gnome-keyring` still attempts a GUI
unlock prompt, so credentials are never stored — every subsequent process sees "Not logged in".

### Workaround
Use `bee login --token-stdin` with a Bee account token (no keyring), OR run the live-Bee
backend on a desktop host where `bee login` already works and point the public tunnel there.
Server otherwise runs `AMBIENT_GUARD_BEE_MODE=mock` (live Open-Meteo, mock Bee context).

### Outcome
**Unresolved (pending decision).** Live server Bee is blocked until a token is supplied or
the tunnel is repointed at a logged-in host.

### Development impact
Blocks live Bee on the public site; does not affect the deployed stack, the tunnel, or live
environmental data, all of which work. Cost a focused debugging session.

### Actionable suggestion
Support a headless, keyring-free credential store for `bee login` — e.g. persist the token to
a permission-restricted file under `$XDG_CONFIG_HOME/bee/` when no Secret Service is available
(with a clear warning), and skip the GUI `gcr-prompter` in non-interactive sessions. Document
`--token-stdin` prominently as the headless/server path, and clarify where to obtain a Bee
**account** token (vs. the MCP HTTP bearer token, which is unrelated).

---

## FR-005 — `bee mcp serve-http` 403s on non-localhost Host/Origin, blocking container access

**Date / Time**: 2026-09-07 04:18 MYT
**Tool / API / SDK**: Bee CLI MCP HTTP transport (`bee mcp serve-http`) · v0.7.3 · Fedora 43 (`meow`)

### Task attempted
Let the Dockerized Ambient Guard backend consume the host's `bee mcp serve-http` (bound to
127.0.0.1:8790) via the Docker host gateway.

### Why this mattered
The backend runs in a container; the Bee MCP server runs on the host loopback. The container
must reach it to serve live Bee data.

### Steps taken
1. Added a host TCP forwarder `0.0.0.0:8791 → 127.0.0.1:8790` (the server is loopback-only).
2. Pointed the container at `http://host.docker.internal:8791/mcp` with the bearer token.
3. Called a tool from the container.

### Expected result
With a valid bearer token, the authenticated JSON-RPC call succeeds.

### Actual result
`403 Forbidden`. The server rejects requests whose `Host`/`Origin` header is not localhost —
independent of the (valid) bearer token. The container's request carried
`Host: host.docker.internal:8791`.

### Severity
**S2 — Moderate.** Documented security behavior, but it silently blocks a legitimate
same-host-via-gateway path; a header override is a clean workaround.

### Evidence
`{"detail":"Bee MCP request failed: Client error '403 Forbidden' for url 'http://host.docker.internal:8791/mcp'"}`.

### Root cause
The HTTP transport enforces a localhost-only `Host`/`Origin` guard (defense against DNS
rebinding). A container reaching the server through the host gateway presents a non-loopback
Host, so the guard rejects it even though the traffic never leaves the host.

### Workaround
Send `Host: 127.0.0.1` + `Origin: http://127.0.0.1` on the client request (implemented as
`AMBIENT_GUARD_BEE_MCP_HOST`, default `127.0.0.1`). The forwarder is a raw TCP pipe, so the
overridden Host reaches the server unchanged and the guard passes.

### Outcome
**Resolved.**

### Actionable suggestion
Allow an explicit allow-list of accepted Host/Origin values (e.g. `--allow-host`) or a flag to
bind a non-loopback interface for trusted same-host container setups, so operators don't have
to spoof the Host header to use the documented HTTP transport from a container.

---

## FR-006 — MCP `bee_get_today` rejects the `context` argument that the CLI `--context` flag implies

**Date / Time**: 2026-09-07 04:22 MYT
**Tool / API / SDK**: Bee CLI MCP tools (`bee_get_today`) · v0.7.3 · Fedora 43 (`meow`)

### Task attempted
Fetch the Bee wearable *context* (conversations/todos/notes) over MCP, mirroring the CLI's
`bee today --context`.

### Why this mattered
The context normalization layer sources the intent phrase from today-context; the MCP path
must return the same data the CLI `--context` flag returns.

### Steps taken
Called `tools/call` for `bee_get_today` with `{"context": true}` (mapping the CLI `--context`).

### Expected result
The tool returns the wearable context, as `bee today --context` does on the CLI.

### Actual result
`Invalid arguments for bee_get_today: 'context' is not a recognized property.` The MCP tool's
input schema has **no properties** — it takes no arguments — yet the CLI exposes `--context`.
`tools/list` confirmed `bee_get_today -> []`. Calling it with `{}` returns the today object
(including the context fields) correctly.

### Severity
**S1 — Minor.** Quickly diagnosed via `tools/list`; the fix is to pass no arguments.

### Evidence
`tools/list`: `bee_get_today -> []`. Error envelope:
`{"result":{"content":[{"type":"text","text":"Invalid arguments for bee_get_today: 'context' is not a recognized property."}],"isError":true}}`.

### Root cause
CLI/MCP surface mismatch: the CLI `today` command has a `--context` flag, but the MCP
`bee_get_today` tool takes no arguments and returns the full object unconditionally.

### Workaround
Call `bee_get_today` with `{}`; the returned object already contains the context fields.

### Outcome
**Resolved.**

### Actionable suggestion
Align the MCP tool schemas with the CLI flags (accept an optional `context` arg on
`bee_get_today`, or document the difference in the MCP tool catalog), so a developer mapping
CLI commands to MCP tools doesn't hit a rejected-argument error.

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
- S1: 2
- S2: 2
- S3: 2
- S4: 0

## Most important developer-experience improvement
Bee CLI on headless servers is the recurring theme: (1) `bee login` has no keyring-free/file
credential store (FR-004); (2) `bee mcp serve-http` 403s on non-localhost Host/Origin, so a
container reaching it via the host gateway must spoof the Host header (FR-005); (3) MCP tool
schemas diverge from CLI flags, e.g. `bee_get_today` rejects the CLI's `--context` (FR-006).
Highest-value fixes: a file-based token store for headless login, and an explicit
Host/Origin allow-list (or trusted-interface bind) for the MCP HTTP transport.

## Most valuable tool experience
To be completed from actual development experience near submission.
