# Ambient Guard — Product Feedback

_Maintained continuously — not reconstructed at submission time._

For every major competition-related technology, record: what we used, why, onboarding
experience, what worked, what confused, bugs/limitations, workarounds, docs quality,
reliability, performance, would-use-again, suggested improvements.

## Bee (CLI / MCP / API)
- **What we used:** Bee CLI (`cli` backend) + Bee MCP (`bee mcp serve`) — TBD once installed.
- **Why:** Documented integration surface; CLI doubles as MCP server; auth via stored `bee login`.
- **Onboarding:** _pending install + `bee login`._
- **Notes:** docs at docs.bee.computer are clear on commands; hardware/account prereqs for
  `bee login` were not obvious up front (see FRICTION_LOG 2026-09-06).

## Kiro Crew
- **What we used:** agent sessions + sub-agents (`spawn_run`) for parallel doc authoring; specs; memory.
- **Why:** Mini-challenge target (documented Kiro Crew development integration).
- **Notes:** sub-agents (`kirocrew-lite`) authored doc drafts but their file-writes did not persist
  in one batch; parent re-wrote from result payloads. Worth confirming whether lite agents' fs_write
  is a no-op in this environment.

## Kiro Specs
- **What we used:** `.kiro/specs/ambient-guard/{requirements,design,tasks}.md`.

## Environmental providers (Open-Meteo / OpenAQ)
- **What we used:** Open-Meteo (no key) as default. _Pending implementation._

## AWS / deployment tooling
- **What we used:** Docker Compose on the `meow` Fedora server behind nginx. _Pending deploy._
