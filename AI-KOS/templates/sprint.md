---
template: sprint
purpose: Record sprint goals, tasks, capacity, and retrospective
version: 1.0.0
created: 2026-06-29
variables:
  - sprint_number
  - start_date
  - end_date
  - goal
  - tasks
  - capacity
  - burndown
  - retrospective
---

# Sprint {{sprint_number}}

## Metadata

| Field       | Value          |
|-------------|----------------|
| Start Date  | {{start_date}} |
| End Date    | {{end_date}}   |
| Capacity    | {{capacity}}   |

## Goal

{{goal}}

## Tasks

- [ ] {{task_1}}
- [ ] {{task_2}}
- [ ] {{task_3}}

## Capacity

{{capacity}}

## Burndown

{{burndown}}

## Retrospective

{{retrospective}}
