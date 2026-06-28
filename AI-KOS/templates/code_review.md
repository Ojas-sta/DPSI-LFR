---
template: code_review
purpose: Record code review with issues, suggestions, and approval
version: 1.0.0
created: 2026-06-29
variables:
  - pr_commit
  - reviewer
  - files
  - issues_found
  - suggestions
  - approval_status
---

# Code Review

## Metadata

| Field      | Value          |
|------------|----------------|
| PR/Commit  | {{pr_commit}}  |
| Reviewer   | {{reviewer}}   |

## Files

{{files}}

## Issues Found

{{issues_found}}

## Suggestions

{{suggestions}}

## Approval Status

{{approval_status}}

## Checklist

- [ ] Code follows style guidelines
- [ ] Tests cover changes
- [ ] Documentation updated
- [ ] No breaking changes introduced
