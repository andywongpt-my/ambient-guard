# Ambient Guard — AWS Builder / Kiro Crew Evidence

## Overview

Ambient Guard was developed using **Kiro Crew** — an agent orchestration platform built on AWS infrastructure.

This document details the Kiro Crew integration for the **AWS Builder Mini Challenge**.

---

## What is Kiro Crew?

Kiro Crew is an autonomous agent management layer that adds:
- **Persistent memory** across sessions
- **Scheduled jobs** (cron-like)
- **Background subagents** for parallel work
- **Self-learning** (corrections and preferences)
- **Multi-session orchestration**
- **Task Runner** for spec-driven autonomous implementation

It runs on AWS infrastructure and orchestrates LLM agents for complex development workflows.

---

## Kiro Crew Usage in Ambient Guard

### Project Setup

Ambient Guard was created as a Kiro Crew project from day one.

**Workspace:** `~/.kiro/crew/workspace/ambient-guard`

**Project configuration:** `.kiro/` directory containing:
- Specs
- Session history
- Workspace configuration
- Memory and lessons

---

### Specs (Spec-Driven Development)

Kiro Crew uses three core specs that define the entire project:

| Spec | Purpose | Location |
|------|---------|----------|
| `requirements.md` | Requirements + acceptance criteria | `.kiro/specs/ambient-guard/requirements.md` |
| `design.md` | Architecture + data models + API | `.kiro/specs/ambient-guard/design.md` |
| `tasks.md` | Ordered implementation tasks | `.kiro/specs/ambient-guard/tasks.md` |

**Workflow:**
1. Specs written upfront (M0)
2. Task Runner executes tasks sequentially
3. Agent implements against specs
4. Specs updated as design evolves

**Evidence:**
- `.kiro/specs/ambient-guard/` directory in repository
- Commit history shows spec-driven commits

---

### Task Runner

Kiro Crew's **Task Runner** autonomously implements features by:
1. Reading the task spec
2. Planning the implementation
3. Executing code changes
4. Running tests
5. Reporting completion

**Usage in Ambient Guard:**
- Milestones M0-M8 executed via Task Runner
- Each milestone had clear acceptance criteria
- Agent worked autonomously until blocked or complete

**Example tasks:**
- "Implement context normalization from Bee data"
- "Build Open-Meteo environmental layer"
- "Create decision-first UI"

---

### Subagents (Parallel Work)

Kiro Crew spawns **subagents** for parallel tasks.

**Usage patterns:**
- Research tasks (read multiple docs in parallel)
- Investigation tasks (explore codebase)
- Testing tasks (run different test suites)

**Evidence:**
- Session history shows subagent spawns
- Memory context references subagent results

**Limitation:** For Ambient Guard, most work was sequential (milestone dependencies), so subagent usage was limited to research/investigation rather than parallel implementation.

---

### Memory & Learning

Kiro Crew provides **persistent memory** across sessions.

**Types:**
- **Semantic memory:** Key-value pairs (project configuration, known facts)
- **Episodic memory:** Conversation fragments
- **History:** Recent activity log

**Usage in Ambient Guard:**
- Project state persisted across sessions
- Lessons learned saved (e.g., git push policy)
- Context compaction handled automatically

**Evidence:**
- `memory/` directory in workspace
- Session history in `[SESSION CONTEXT]` blocks

---

### Friction Log

Kiro Crew encourages logging **genuine platform friction**.

**Ambient Guard friction log:** [`FRICTION_LOG.md`](FRICTION_LOG.md)

Key entries related to Kiro Crew:
- FR-008: Bee MCP lacks programmatic todo creation
- Various session management notes

---

## AWS Infrastructure

Kiro Crew runs on AWS:

- **Agent orchestration:** AWS Lambda / Fargate (managed by Kiro Crew)
- **Memory storage:** DynamoDB / S3 (managed by Kiro Crew)
- **Session management:** AWS-backed state
- **Subagent execution:** AWS compute

**Note:** Ambient Guard itself uses Kiro Crew for development, but does not deploy to AWS runtime. The production deployment is on a dedicated Fedora server via Docker Compose + Cloudflare Tunnel.

---

## Development Velocity Impact

### What Worked Well

1. **Spec-driven development:** Clear specs upfront meant less backtracking
2. **Persistent memory:** Context survived session boundaries
3. **Task Runner:** Autonomous execution of well-defined tasks
4. **Friction log:** Systematic capture of platform issues

### Challenges

1. **Learning curve:** Initial setup required understanding Kiro Crew concepts
2. **Context limits:** Large sessions required manual summarization
3. **Subagent coordination:** Limited use due to sequential milestone dependencies

### Overall Assessment

Kiro Crew provided:
- **Structure:** Specs + tasks + milestones
- **Continuity:** Memory across sessions
- **Automation:** Task Runner for routine implementation

For a spec-driven hackathon project, the structure was valuable.

---

## Evidence Summary

| Item | Location | Description |
|------|----------|-------------|
| Specs | `.kiro/specs/ambient-guard/` | Requirements, design, tasks |
| Workspace | `.kiro/` directory | Project configuration |
| Memory | Session context | Persistent across sessions |
| Friction log | `FRICTION_LOG.md` | Platform issues encountered |
| Session history | `[SESSION CONTEXT]` blocks | Development timeline |

---

## Conclusion

Ambient Guard demonstrates **Kiro Crew** as the development orchestration layer for a hackathon project:

- **Spec-driven:** Requirements → Design → Tasks → Implementation
- **Autonomous:** Task Runner executes tasks
- **Persistent:** Memory survives sessions
- **Structured:** Milestones with clear acceptance criteria

This qualifies for the **AWS Builder Mini Challenge** as a real-world application of an AWS-backed agent orchestration platform.

---

## References

- Kiro Crew docs: `~/.kiro/crew/docs/` (local installation)
- Ambient Guard specs: `.kiro/specs/ambient-guard/`
- Session memory: `[SESSION CONTEXT]` in chat history
