---
file: README.md
purpose: Overview of the shared-context directory — the canonical machine context layer for all AI agents
last_updated: 2026-06-29
updated_by: system
version: 1.0.0
---

## Purpose

This directory is the **single source of truth** for project context. Every AI agent
that operates on this repository MUST read from here before taking any action and MUST
write back here after completing work. Files are compact, structured, and
machine-optimized so agents can parse them in a single pass.

## Update Rules

- **No agent may edit `SharedContext.md` without a recorded decision in `DecisionLog.md`.**
- **`CurrentTask.md` and `ActiveAgents.md` must be updated at the start and end of every session.**
- **`RecentChanges.md` and `TaskHistory.md` are append-only — never delete entries.**
- **All timestamps use ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`).**
- **Locks in `Locks.md` must be claimed before editing any shared file.**
- **When a file is updated, bump its `version` and `last_updated` fields.**
- **Stale data is worse than no data — if you cannot update a file accurately, flag it.**

## Content

### File Inventory

| File | Purpose | Read Frequency |
|------|---------|----------------|
| `SharedContext.md` | THE FIRST FILE every AI reads. Project vision, stack, rules, constraints | Every session start |
| `ProjectState.md` | Machine-readable project status snapshot | Every session start |
| `CurrentTask.md` | The single active task being worked on right now | Every session start |
| `TaskQueue.md` | Prioritized backlog of pending tasks | When picking up new work |
| `TaskHistory.md` | Append-only log of completed tasks | When checking past outcomes |
| `SessionSummary.md` | Summaries of the last 5 sessions | When resuming work |
| `RecentChanges.md` | Append-only changelog of recent file modifications | Before editing shared files |
| `DecisionLog.md` | Important project decisions with rationale | When architectural questions arise |
| `ArchitectureSnapshot.md` | Current architecture summary and component map | When planning changes |
| `CurrentSprint.md` | Active sprint info, tasks, and progress | When checking sprint scope |
| `NextSteps.md` | Ordered list of immediate next actions | When current task completes |
| `KnownIssues.md` | Known bugs, issues, and workarounds | Before starting work |
| `Environment.md` | Dev environment, build/test/deploy commands | When setting up or debugging |
| `ActiveAgents.md` | Currently active AI agents and their tasks | Before claiming locks |
| `Locks.md` | File lock registry to prevent edit conflicts | Before editing any shared file |

### Reading Order for Agents

1. `SharedContext.md` — understand the project
2. `ProjectState.md` — understand where things stand
3. `CurrentTask.md` — understand what is in progress
4. `Locks.md` — check for conflicts before editing
5. `KnownIssues.md` — avoid known pitfalls
6. `RecentChanges.md` — understand recent modifications
7. `SessionSummary.md` — understand recent context
8. Task-specific files as needed (`TaskQueue.md`, `NextSteps.md`, etc.)

### Update Protocol

```
1. READ SharedContext.md → understand project
2. READ ProjectState.md → understand status
3. READ CurrentTask.md → understand active work
4. READ Locks.md → check for file conflicts
5. CLAIM locks for files you will edit
6. REGISTER yourself in ActiveAgents.md
7. DO WORK — edit code and context files
8. UPDATE CurrentTask.md with progress
9. APPEND to RecentChanges.md for each file modified
10. RELEASE locks
11. UPDATE SessionSummary.md and ProjectState.md
12. DEREGISTER from ActiveAgents.md
```

## Example

An agent starting a new session:

```
> READ shared-context/SharedContext.md
> READ shared-context/ProjectState.md
> READ shared-context/CurrentTask.md
> READ shared-context/Locks.md
> No locks on target files → proceed
> REGISTER in ActiveAgents.md
> CLAIM lock on src/api/tasks.ts in Locks.md
> ... perform work ...
> APPEND changes to RecentChanges.md
> RELEASE lock
> UPDATE SessionSummary.md
> DEREGISTER from ActiveAgents.md
```

## AI Instructions

- Always read `SharedContext.md` first — never skip it.
- Never edit a file that another agent has locked without coordinating first.
- Keep entries concise. Use tables over prose. Use status indicators over sentences.
- If you find stale or contradictory information, update it and log the correction in `DecisionLog.md`.
- This directory is the nervous system of the project — treat it with care.
