---
template: meeting
purpose: Capture meeting notes with agenda, discussion, and action items
version: 1.0.0
created: 2026-06-29
variables:
  - date
  - attendees
  - agenda
  - discussion
  - decisions
  - action_items
---

# Meeting Notes

## Metadata

| Field     | Value       |
|-----------|-------------|
| Date      | {{date}}    |
| Attendees | {{attendees}}|

## Agenda

{{agenda}}

## Discussion

{{discussion}}

## Decisions

{{decisions}}

## Action Items

- [ ] {{action_item_1}}
- [ ] {{action_item_2}}
- [ ] {{action_item_3}}
