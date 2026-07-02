---
template: release
purpose: Record a release with changes, breaking changes, and checklist
version: 1.0.0
created: 2026-06-29
variables:
  - version
  - date
  - changes
  - breaking_changes
  - migration_guide
  - checklist
---

# Release: {{version}}

## Metadata

| Field   | Value       |
|---------|-------------|
| Version | {{version}} |
| Date    | {{date}}    |

## Changes

{{changes}}

## Breaking Changes

{{breaking_changes}}

## Migration Guide

{{migration_guide}}

## Checklist

- [ ] {{checklist_item_1}}
- [ ] {{checklist_item_2}}
- [ ] {{checklist_item_3}}
