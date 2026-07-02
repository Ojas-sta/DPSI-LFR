# 07 Debugging

## Purpose

The Debugging folder holds debugging guides, incident reports, post-mortems, and known-issue trackers. It is the operational counterpart to `06 Development/` — used when things go wrong and we need to understand why, fix it, and prevent recurrence.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `ISS-NNN-<Title>.md` | Issue | Known issue reports with reproduction and resolution |
| `INC-NNN-<Title>.md` | Incident | Incident reports for production issues |
| `PMT-NNN-<Title>.md` | Post-Mortem | Post-mortem analysis of incidents |
| `DebugPlaybook.md` | Guide | Systematic debugging methodology |
| `Runbook.md` | Runbook | Operational runbook for common incidents |
| `KnownIssues.md` | Tracker | Summary table of all open known issues |
| `README.md` | Guide | This file |

## Workflow

1. **Issue Discovery**: When a bug is found, create an `ISS-NNN-<Title>.md` with reproduction steps.
2. **Investigation**: Use `DebugPlaybook.md` methodology to investigate systematically.
3. **Incident Response**: For production issues, create an `INC-NNN-<Title>.md` and follow `Runbook.md`.
4. **Post-Mortem**: After resolution, create a `PMT-NNN-<Title>.md` covering timeline, root cause, and action items.
5. **Tracking**: Update `KnownIssues.md` with the current status of all issues.
6. **Resolution**: When fixed, update the issue file with the resolution and link to the PR.
7. **Archive**: Resolved issues are moved to `15 Archive/` after one sprint cycle.

## Conventions

- Issue filenames: `ISS-NNN-Short-Title.md` (kebab-case, sequential).
- Incident filenames: `INC-NNN-Short-Title.md`.
- Post-mortem filenames: `PMT-NNN-Short-Title.md`.
- Each issue includes: `Date`, `Severity`, `Status`, `Reproduction`, `Root Cause`, `Resolution`.
- Use severity levels: `P0 Critical`, `P1 High`, `P2 Medium`, `P3 Low`.
- Status values: `Open`, `Investigating`, `Fix in Progress`, `Resolved`, `Won't Fix`.
- Post-mortems follow the blameless format — focus on systems, not individuals.

## Examples

```markdown
## ISS-001 excerpt

## Severity
P1 High

## Status
Fix in Progress

## Reproduction
1. Start the server with `npm start`
2. Send 1000 concurrent requests to `/api/v1/users`
3. Observe memory usage climbing without release

## Root Cause
Connection pool not releasing connections on error paths.
```

```markdown
## PMT-001 excerpt

## Timeline
| Time | Event |
|------|-------|
| 14:03 | Alert: 500 errors spiking |
| 14:05 | On-call paged |
| 14:10 | Identified database connection exhaustion |
| 14:25 | Rolled back to previous deployment |
| 14:30 | Service recovered |
```
