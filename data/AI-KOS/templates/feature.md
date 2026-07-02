---
template: feature
purpose: Document a feature request with user story, acceptance criteria, and tasks
version: 1.0.0
created: 2026-06-29
variables:
  - feature_id
  - title
  - description
  - user_story
  - acceptance_criteria
  - tasks
  - dependencies
  - estimate
  - status
---

# Feature: {{title}}

## Metadata

| Field       | Value          |
|-------------|----------------|
| Feature ID  | {{feature_id}} |
| Status      | {{status}}     |
| Estimate    | {{estimate}}   |

## Description

{{description}}

## User Story

{{user_story}}

## Acceptance Criteria

- [ ] {{acceptance_criteria_1}}
- [ ] {{acceptance_criteria_2}}
- [ ] {{acceptance_criteria_3}}

## Tasks

- [ ] {{task_1}}
- [ ] {{task_2}}
- [ ] {{task_3}}

## Dependencies

{{dependencies}}

## Estimate

{{estimate}}

## Status

{{status}}
