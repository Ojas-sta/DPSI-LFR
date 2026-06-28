---
template: decision
purpose: Record a decision with context, options, and rationale
version: 1.0.0
created: 2026-06-29
variables:
  - decision_id
  - title
  - context
  - options_considered
  - decision
  - rationale
  - impact
  - status
---

# Decision: {{title}}

## Metadata

| Field       | Value           |
|-------------|-----------------|
| Decision ID | {{decision_id}} |
| Status      | {{status}}      |

## Context

{{context}}

## Options Considered

{{options_considered}}

## Decision

{{decision}}

## Rationale

{{rationale}}

## Impact

{{impact}}

## Status

{{status}}
