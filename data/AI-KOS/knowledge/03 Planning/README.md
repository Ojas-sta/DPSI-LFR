# 03 Planning

## Purpose

The Planning folder contains forward-looking documents — roadmaps, sprint plans, estimates, and capacity plans. It is where the team defines what will be done, when, and by whom. Planning documents are living artifacts that evolve as the project progresses.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `QuarterlyPlan.md` | Plan | High-level quarterly objectives and key results |
| `SprintBacklog.md` | Backlog | Items queued for upcoming sprints |
| `EstimationGuide.md` | Guide | How estimates are produced and what units are used |
| `CapacityPlan.md` | Plan | Team availability and velocity tracking |
| `MilestoneTracker.md` | Tracker | Milestone definitions and completion status |
| `RetrospectiveActions.md` | Tracker | Action items from retrospectives |
| `README.md` | Guide | This file |

## Workflow

1. **Quarterly Planning**: At the start of each quarter, update `QuarterlyPlan.md` with OKRs.
2. **Sprint Planning**: Before each sprint, populate `SprintBacklog.md` and create a sprint record in `11 Sprints/`.
3. **Estimation**: Use `EstimationGuide.md` as the reference for sizing work items.
4. **Capacity Tracking**: Update `CapacityPlan.md` at sprint boundaries.
5. **Milestone Review**: Review `MilestoneTracker.md` during sprint reviews.
6. **Retrospectives**: After each sprint, add action items to `RetrospectiveActions.md`.

## Conventions

- Estimates use story points (Fibonacci: 1, 2, 3, 5, 8, 13, 21).
- Dates use ISO 8601 format.
- Sprint records are numbered sequentially: `Sprint-NNN-<Theme>`.
- Milestones use semantic versioning when applicable.
- Planning documents are tagged `<!-- horizon: quarter | sprint | milestone -->`.
- All planning items link to their implementation records (tasks, PRs, sprint records).

## Examples

```markdown
## SprintBacklog.md excerpt

| ID | Item | Points | Sprint | Status |
|----|------|--------|--------|--------|
| SB-012 | Implement auth middleware | 5 | Sprint-002 | ⚪ Not Started |
| SB-013 | Add user profile page | 3 | Sprint-002 | ⚪ Not Started |
```

```markdown
## MilestoneTracker.md excerpt

| Milestone | Target Date | Status | Dependencies |
|-----------|-------------|--------|--------------|
| M1: MVP | 2026-07-15 | 🟡 In Progress | None |
| M2: Beta | 2026-09-01 | ⚪ Not Started | M1 |
```
