# 14 Assets

## Purpose

The Assets folder stores all binary and media files referenced by the knowledge vault — diagrams, screenshots, images, PDFs, and other attachments. Centralizing assets prevents broken links and makes it easy to find and update visual content.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `diagrams/` | Folder | Architecture, data flow, and sequence diagrams |
| `screenshots/` | Folder | UI screenshots and visual references |
| `logos/` | Folder | Project and partner logos |
| `documents/` | Folder | PDFs, slides, and other binary documents |
| `icons/` | Folder | Custom icons used in documentation |
| `AssetIndex.md` | Index | Catalog of all assets with descriptions and usage |
| `README.md` | Guide | This file |

## Workflow

1. **Adding Assets**: Place new assets in the appropriate subfolder, then register in `AssetIndex.md`.
2. **Naming**: Use descriptive, kebab-case filenames: `system-architecture-v2.png`.
3. **Referencing**: Link to assets using relative paths from the referencing document.
4. **Versioning**: When updating an asset, either replace in-place (minor) or create a new versioned file (major).
5. **Cleanup**: Periodically review `AssetIndex.md` for orphaned assets (referenced by no document).
6. **Optimization**: Images should be optimized for web (compressed, reasonable dimensions).

## Conventions

- Supported formats: `.png` for diagrams/screenshots, `.svg` for scalable graphics, `.pdf` for documents.
- Filenames: kebab-case, descriptive, versioned when needed: `data-flow-v2.png`.
- Maximum image size: 2MB (use compression for larger files).
- Diagrams should also have a Mermaid or text version when possible.
- Each asset in `AssetIndex.md` includes: filename, description, dimensions, and which documents reference it.
- Do not commit large binary files (>5MB) — use external storage and link instead.

## Examples

```markdown
## AssetIndex.md excerpt

| Asset | Type | Description | Referenced By |
|-------|------|-------------|---------------|
| diagrams/system-architecture-v2.png | Diagram | System architecture diagram | 04 Architecture/SystemDiagram.md |
| screenshots/login-page.png | Screenshot | Login page UI | 06 Development/CommonTasks.md |
```

```markdown
## Referencing an asset from a document

![System Architecture](../14%20Assets/diagrams/system-architecture-v2.png)
```
