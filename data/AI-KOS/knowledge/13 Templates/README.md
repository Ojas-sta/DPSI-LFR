# 13 Templates

## Purpose

The Templates folder provides standardized templates for every type of document created in the knowledge vault. Using templates ensures consistency, completeness, and discoverability across the vault. Every new document should start from a template.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `TPL-ADR.md` | Template | Architecture Decision Record template |
| `TPL-Decision.md` | Template | General decision record template |
| `TPL-Sprint.md` | Template | Sprint record template |
| `TPL-Issue.md` | Template | Known issue / bug report template |
| `TPL-Incident.md` | Template | Incident report template |
| `TPL-PostMortem.md` | Template | Post-mortem template |
| `TPL-Research.md` | Template | Research note / spike template |
| `TPL-Meeting.md` | Template | Meeting notes template |
| `TPL-Prompt.md` | Template | AI prompt template |
| `TPL-ProjectDoc.md` | Template | Project document template (for `01 Project/`) |
| `TPL-FolderReadme.md` | Template | Folder README template |
| `TemplateIndex.md` | Index | List of all templates with descriptions |
| `README.md` | Guide | This file |

## Workflow

1. **New Document**: When creating any new document, check `TemplateIndex.md` for a matching template.
2. **Copy Template**: Copy the template content into the new file location.
3. **Fill In**: Replace placeholder content (marked with `[brackets]`) with actual content.
4. **Remove Placeholders**: Delete any template sections that don't apply.
5. **Review**: Ensure all required sections are filled in before saving.
6. **Template Updates**: When document conventions change, update templates first, then existing documents.

## Conventions

- Template filenames: `TPL-<Type>.md`.
- Placeholders use `[bracketed descriptions]` syntax.
- Required sections are marked with `(required)` — optional sections with `(optional)`.
- Templates include a comment at the top: `<!-- template: TPL-<Type>.md -->`.
- Templates are versioned — note the version in `TemplateIndex.md`.
- Never edit a template after documents have been created from it without bumping the version.

## Examples

```markdown
## TPL-Sprint.md excerpt

# Sprint-[NNN]: [Theme]

## Dates
Start: [YYYY-MM-DD] | End: [YYYY-MM-DD]

## Goals
- [Goal 1]
- [Goal 2]

## Scope
| ID | Item | Points | Assignee | Status |
|----|------|--------|----------|--------|
| [ID] | [Description] | [Points] | [Person] | [Status] |

## Metrics
| Metric | Value |
|--------|-------|
| Planned | [Points] |
| Completed | [Points] |
```
