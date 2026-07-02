# 15 Archive

## Purpose

The Archive folder holds completed, superseded, and no-longer-active documents that are retained for historical reference. Archiving keeps active folders clean while preserving the full history of decisions, research, issues, and sprints. Archived documents are immutable — they are not edited after archiving.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `sprints/` | Folder | Completed sprint records |
| `issues/` | Folder | Resolved issues and incidents |
| `research/` | Folder | Concluded research that informed decisions |
| `decisions/` | Folder | Superseded decisions |
| `meetings/` | Folder | Meeting notes older than 6 months |
| `documents/` | Folder | Deprecated or replaced project documents |
| `ArchiveIndex.md` | Index | Catalog of all archived items with archive date |
| `README.md` | Guide | This file |

## Workflow

1. **Archiving**: When an item is completed or superseded, move it from its active folder to the appropriate `15 Archive/` subfolder.
2. **Indexing**: Add the item to `ArchiveIndex.md` with the original location, archive date, and reason.
3. **Linking**: Update any links in active documents to point to the new archived location.
4. **Immutability**: Archived documents are never edited. If information needs updating, create a new document in the active section.
5. **Retention**: Archived items are retained indefinitely unless they contain sensitive data.
6. **Review**: Periodically review the archive for items that can be safely deleted (after regulatory retention periods).

## Conventions

- Preserve the original filename when archiving.
- Add an `Archived` section at the top of each archived document:
  ```
  > **Archived**: Originally at `01 Project/OldDoc.md`. Archived on 2026-06-20. Reason: Superseded by ProjectGoals.md.
  ```
- Use subfolders that mirror the active folder structure: `sprints/`, `issues/`, `research/`, etc.
- `ArchiveIndex.md` includes: filename, original location, archive date, reason, and link to superseding document if any.
- Archived ADRs and decisions retain their numbers — the originals in `04 Architecture/` and `08 Decisions/` are updated with `Superseded` status and a link to the archive.

## Examples

```markdown
## ArchiveIndex.md excerpt

| File | Original Location | Archived On | Reason | Superseded By |
|------|-------------------|-------------|--------|---------------|
| Sprint-001-Foundation.md | 11 Sprints/ | 2026-06-15 | Sprint completed | — |
| ISS-003-Memory-Leak.md | 07 Debugging/ | 2026-06-20 | Resolved in v1.2.0 | — |
| DEC-002-Use-Vue.md | 08 Decisions/ | 2026-06-10 | Superseded | DEC-005-Use-React |
```
