# Ambient Guard — Product Feedback

_Maintained throughout the build; finalized at M8. For each major competition technology:
what we used, why, what worked, what was confusing, and whether we'd use it again._

## Bee (CLI + MCP)
- **Used:** `@beeai/cli` 0.7.3 — `bee login`, `bee today`, `bee locations current`, `bee todos`,
  `bee create_todo`; and its MCP server (`bee mcp serve-http`) as the live backend on the server.
- **Why:** the documented integration surface; the CLI doubling as an MCP server let a containerized
  backend consume real Bee data over HTTP.
- **Worked well:** clean JSON output (`--json`); `bee_get_today`/`bee_get_current_location` fast and
  reliable; MCP tool catalog maps closely to CLI commands; auth via stored login (no token juggling
  for stdio/cli).
- **Confusing / friction (see FRICTION_LOG FR-001–007):** install command only on the homepage not
  `/docs/cli`; `bee login` prerequisites (Developer Mode) under-documented; `--no-wait` doesn't
  finalize an approved session; **headless `bee login` has no keyring-free/file token store** (the
  biggest blocker); MCP `serve-http` 403s on non-localhost Host/Origin (breaks container-via-gateway
  without a Host override); `bee_get_today` MCP tool rejects the CLI's `--context` arg; and
  **`bee_search` hangs server-side** (0 bytes, timeout).
- **Reliability:** read tools solid; `bee_search` intermittently unreliable.
- **Would use again:** yes — the personal-context data is genuinely useful; the headless-auth and
  search issues need addressing for server deployments.

## Kiro Crew
- **Used:** agent sessions, parallel sub-agents (`spawn_run`), monitor loops (`monitor_start`) for
  polling Bee sync / DNS / memory, persistent memory + lessons, `learn_add`.
- **Worked well:** the whole product was built and shipped in-session; monitor loops cleanly handled
  "wait for X then verify" (Bee sync, DNS propagation); memory kept multi-session continuity.
- **Confusing:** sub-agents' file-writes (kirocrew-lite) didn't persist in one early batch — had to
  extract content from result files and write locally. SSH-passed commands with nested quotes get
  mangled (use script files). Blocked git ops (push-to-main, reset --hard) are correct but caused a
  cosmetic local-main drift.
- **Would use again:** yes.

## Kiro Specs
- **Used:** `.kiro/specs/ambient-guard/{requirements,design,tasks}.md` drove every milestone M0–M8.
- **Worked well:** requirements→design→tasks kept the build ordered and traceable; the tasks file
  doubled as a live progress ledger.

## Kiro Task Runner
- **Not used.** Development was interactive Crew sessions; noted honestly in the compliance matrix.

## Environmental provider — Open-Meteo
- **Used:** forecast API (temp/humidity/wind/precip/UV/weather) + air-quality API (PM2.5/PM10/O3/NO2/US-AQI).
- **Worked well:** no API key, global coverage, hourly series with clean timestamps, CC BY 4.0.
- **Would use again:** yes — ideal for a no-key demo.

## AWS / deployment tooling
- **Used:** Docker Compose on a Fedora server behind a **Cloudflare Tunnel** (chosen over
  Let's Encrypt/nginx because the server's public IP is residential/CGNAT and Tailscale IPs aren't
  public-routable). `cloudflared` tunnel + auto-CNAME + persistent systemd service.
- **Worked well:** Cloudflare Tunnel gave public HTTPS with zero port-forwarding or certbot;
  auto-CNAME once the zone was authorized.
- **Confusing:** `cloudflared tunnel login` needs a browser callback that can't be held across
  agent turns (run it persistently in the background); had to `--overwrite-dns` a stale record.
- **Would use again:** yes — the right call for a home/CGNAT-hosted demo.
