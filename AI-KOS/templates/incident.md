---
template: incident
purpose: Report an incident with timeline, impact, and resolution
version: 1.0.0
created: 2026-06-29
variables:
  - incident_id
  - date
  - severity
  - summary
  - timeline
  - impact
  - root_cause
  - resolution
  - prevention
---

# Incident: {{incident_id}}

## Metadata

| Field     | Value         |
|-----------|---------------|
| Date      | {{date}}      |
| Severity  | {{severity}}  |

## Summary

{{summary}}

## Timeline

{{timeline}}

## Impact

{{impact}}

## Root Cause

{{root_cause}}

## Resolution

{{resolution}}

## Prevention

- [ ] {{prevention_1}}
- [ ] {{prevention_2}}
- [ ] {{prevention_3}}
