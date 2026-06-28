---
template: agent_handoff
purpose: Transfer context between agents with state, files, and locks
version: 1.0.0
created: 2026-06-29
variables:
  - from_agent
  - to_agent
  - context_summary
  - current_state
  - files_modified
  - next_steps
  - locks_held
---

# Agent Handoff

## Metadata

| Field       | Value           |
|-------------|-----------------|
| From Agent  | {{from_agent}}  |
| To Agent    | {{to_agent}}    |

## Context Summary

{{context_summary}}

## Current State

{{current_state}}

## Files Modified

{{files_modified}}

## Next Steps

- [ ] {{next_step_1}}
- [ ] {{next_step_2}}
- [ ] {{next_step_3}}

## Locks Held

{{locks_held}}
