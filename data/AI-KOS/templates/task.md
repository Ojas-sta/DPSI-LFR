---
template: task
purpose: Track a generic task with subtasks, dependencies, and estimate
version: 1.0.0
created: 2026-06-29
variables:
  - task_id
  - title
  - type
  - description
  - subtasks
  - dependencies
  - estimate
  - assignee
  - status
---

# Task: {{title}}

## Metadata

| Field       | Value        |
|-------------|--------------|
| Task ID     | {{task_id}}  |
| Type        | {{type}}     |
| Assignee    | {{assignee}} |
| Status      | {{status}}   |
| Estimate    | {{estimate}} |

## Description

{{description}}

## Subtasks

- [ ] {{subtask_1}}
- [ ] {{subtask_2}}
- [ ] {{subtask_3}}

## Dependencies

{{dependencies}}

## Estimate

{{estimate}}

## Status

{{status}}
