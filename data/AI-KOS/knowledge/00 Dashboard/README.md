# 00 Dashboard

## Purpose

The Dashboard is the primary landing hub for the entire knowledge vault. It provides an at-a-glance view of project health, current sprint progress, active tasks, recent changes, known issues, and key decisions. This folder exists so that any human or AI agent entering the vault can orient themselves immediately without hunting through subfolders.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `Dashboard.md` | Dashboard | The full project dashboard with status tables, metrics, and links |
| `README.md` | Guide | This file — explains dashboard structure and conventions |

## Workflow

1. **Entry Point**: All vault navigation starts here. The `Dashboard.md` file is the single source of truth for "what is happening right now."
2. **Update Cadence**: The dashboard is updated at least once per sprint and ideally after every significant change (merge, deployment, incident, decision).
3. **Agent Responsibility**: AI agents should read `Dashboard.md` at the start of every session to understand current context before taking action.
4. **Human Responsibility**: Humans update the dashboard after sprint planning, retrospectives, and major milestones.
5. **Cross-Linking**: Every section in the dashboard links to detailed records in their respective folders (e.g., sprint details link to `11 Sprints/`, decisions link to `08 Decisions/`).

## Conventions

- Use status indicators: `✅ Done`, `🟡 In Progress`, `🔴 Blocked`, `⚪ Not Started`
- Use priority indicators: `P0 Critical`, `P1 High`, `P2 Medium`, `P3 Low`
- Dates use ISO 8601 format: `YYYY-MM-DD`
- All links are relative to the vault root
- Tables are used for structured data; bullet lists for narrative content
- The dashboard must never contain detailed content — only summaries and links

## Examples

```markdown
## Current Sprint

| Field | Value |
|-------|-------|
| Sprint | Sprint-001-Foundation |
| Status | 🟡 In Progress |
| Start | 2026-06-01 |
| End | 2026-06-14 |
```

```markdown
## Known Issues

| ID | Issue | Severity | Status | Link |
|----|-------|----------|--------|------|
| ISS-003 | Memory leak in worker pool | P1 High | 🔴 Blocked | [07 Debugging/ISS-003](../07%20Debugging/ISS-003.md) |
```
