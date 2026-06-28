---
template: bug
purpose: Report a bug with reproduction steps, environment, and impact
version: 1.0.0
created: 2026-06-29
variables:
  - bug_id
  - title
  - severity
  - description
  - steps_to_reproduce
  - expected_behavior
  - actual_behavior
  - environment
  - workaround
  - status
---

# Bug: {{title}}

## Metadata

| Field     | Value       |
|-----------|-------------|
| Bug ID    | {{bug_id}}  |
| Severity  | {{severity}}|
| Status    | {{status}}  |

## Description

{{description}}

## Steps to Reproduce

1. {{step_1}}
2. {{step_2}}
3. {{step_3}}

## Expected Behavior

{{expected_behavior}}

## Actual Behavior

{{actual_behavior}}

## Environment

{{environment}}

## Workaround

{{workaround}}

## Status

{{status}}
