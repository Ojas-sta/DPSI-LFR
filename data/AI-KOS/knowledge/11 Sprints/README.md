# 11 Sprints

## Purpose

The Sprints folder records the complete history of each sprint — scope, goals, completed work, carry-over, metrics, and retrospectives. Sprint records are the authoritative log of what was planned, what was delivered, and what was learned.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `Sprint-NNN-<Theme>.md` | Sprint Record | Complete record of a single sprint |
| `SprintIndex.md` | Index | Chronological list of all sprints with summary metrics |
| `VelocityHistory.md` | Tracker | Velocity trend across sprints |
| `README.md` | Guide | This file |

## Workflow

1. **Sprint Planning**: At sprint start, create `Sprint-NNN-<Theme>.md` with goals, scope, and capacity.
2. **During Sprint**: Update the sprint record with progress, blockers, and scope changes.
3. **Sprint Review**: At sprint end, record completed/deferred items and demo outcomes.
4. **Retrospective**: Add retrospective notes (what went well, what didn't, action items).
5. **Metrics**: Record velocity, completion rate, and other metrics.
6. **Indexing**: Update `SprintIndex.md` and `VelocityHistory.md`.

## Conventions

- Sprint filenames: `Sprint-NNN-Short-Theme.md` (kebab-case, sequential).
- Each sprint record includes: `Sprint #`, `Theme`, `Dates`, `Goals`, `Scope`, `Capacity`, `Completed`, `Deferred`, `Metrics`, `Retrospective`.
- Sprints are typically 2 weeks; adjust the `Dates` field accordingly.
- Velocity is measured in story points completed.
- Sprint numbers are never reused.
- Link to meeting notes in `10 Meetings/` for planning and retrospective sessions.

## Examples

```markdown
## Sprint-001 excerpt

## Theme
Foundation

## Dates
Start: 2026-06-01 | End: 2026-06-14

## Goals
- Set up project infrastructure
- Implement core data models
- Establish CI/CD pipeline

## Metrics
| Metric | Value |
|--------|-------|
| Planned | 34 points |
| Completed | 28 points |
| Completion Rate | 82% |
| Velocity | 28 |
```

```markdown
## VelocityHistory excerpt

| Sprint | Planned | Completed | Velocity |
|--------|---------|-----------|----------|
| Sprint-001 | 34 | 28 | 28 |
| Sprint-002 | 30 | 30 | 30 |
| Sprint-003 | 32 | 26 | 26 |
```
