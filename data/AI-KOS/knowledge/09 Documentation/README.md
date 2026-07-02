# 09 Documentation

## Purpose

The Documentation folder is the index and management layer for all project documentation — internal and external. It tracks documentation health, identifies gaps, and provides guides for writing and maintaining documentation. This folder ensures documentation is treated as a first-class project artifact.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `DocIndex.md` | Index | Master index of all documentation across the vault |
| `DocStyleGuide.md` | Guide | Standards for writing and formatting documentation |
| `DocMaintenance.md` | Guide | How documentation is reviewed and kept current |
| `ExternalDocs.md` | Reference | Links to external documentation (API docs, wikis) |
| `DocGaps.md` | Tracker | Identified gaps in documentation coverage |
| `README.md` | Guide | This file |

## Workflow

1. **Authoring**: Follow `DocStyleGuide.md` when creating any new documentation.
2. **Indexing**: Add new documents to `DocIndex.md` under the appropriate category.
3. **Review Cycle**: Documentation is reviewed each sprint for accuracy — see `DocMaintenance.md`.
4. **Gap Tracking**: When a documentation gap is identified, add it to `DocGaps.md`.
5. **External Links**: Maintain `ExternalDocs.md` for any referenced external documentation.
6. **Health Check**: During sprint reviews, assess documentation health and prioritize gap-filling.

## Conventions

- All documentation uses Markdown.
- Internal docs link with relative paths; external docs use full URLs.
- Each document has a `Last Reviewed` date at the top.
- Documentation categories: Project, Architecture, Development, Operations, User.
- Use frontmatter `<!-- doc-id: DOC-NNN -->` for tracking.
- Style guide covers: headings, code blocks, tables, links, tone, and structure.

## Examples

```markdown
## DocIndex.md excerpt

| Doc ID | Title | Location | Last Reviewed | Status |
|--------|-------|----------|---------------|--------|
| DOC-001 | Project Goals | 01 Project/ProjectGoals.md | 2026-06-15 | ✅ Current |
| DOC-002 | Tech Stack | 01 Project/TechStack.md | 2026-06-10 | ✅ Current |
| DOC-003 | API Reference | 01 Project/APIReference.md | 2026-05-20 | 🟡 Needs Review |
```

```markdown
## DocStyleGuide.md excerpt

### Heading Levels
- `#` Document title (only one per file)
- `##` Major sections
- `###` Subsections
- `####` Minor sections (avoid going deeper)
```
