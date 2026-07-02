# 08 Decisions

## Purpose

The Decisions folder records all significant project decisions — technical, product, and process. Decision records (DECs) complement ADRs (which focus specifically on architecture) by covering the broader landscape of choices that shape the project. Together, ADRs and DECs form the complete decision log.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `DEC-NNN-<Title>.md` | Decision | Individual decision records |
| `DecisionLog.md` | Log | Chronological summary table of all decisions |
| `README.md` | Guide | This file |

## Workflow

1. **Decision Needed**: When a non-trivial decision is made, create a `DEC-NNN-<Title>.md`.
2. **Proposal**: Draft the decision with context, options considered, and recommendation.
3. **Review**: Circulate the decision to stakeholders for input.
4. **Resolution**: Update status to `Accepted`, `Rejected`, or `Superseded`.
5. **Logging**: Add the decision to `DecisionLog.md`.
6. **Linking**: Link to related ADRs in `04 Architecture/`, research in `05 Research/`, and context in `02 Context/`.
7. **Supersession**: When a decision is reversed, update its status to `Superseded by DEC-NNN` — never delete it.

## Conventions

- Decision filenames: `DEC-NNN-Short-Title.md` (kebab-case, sequential).
- Each decision includes: `Date`, `Deciders`, `Status`, `Context`, `Options Considered`, `Decision`, `Rationale`, `Consequences`.
- Decision numbers are never reused.
- Status values: `Proposed`, `Accepted`, `Rejected`, `Superseded`, `Deprecated`.
- Use the `DEC-` prefix for general decisions and `ADR-` prefix for architecture decisions (stored in `04 Architecture/`).
- Decisions are immutable once `Accepted` — changes require a new decision that supersedes the old one.

## Examples

```markdown
## DEC-001 excerpt

## Status
Accepted

## Date
2026-06-01

## Context
We need to choose a frontend framework for the new dashboard.

## Options Considered
1. React — Mature ecosystem, large community
2. Vue — Simpler learning curve, good performance
3. Svelte — Minimal runtime, compiler-based

## Decision
Choose React for its ecosystem maturity and team familiarity.

## Rationale
Team has 3+ years of React experience. Ecosystem provides ready-made
solutions for routing, state management, and testing.
```
