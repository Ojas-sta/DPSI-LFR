# 01 Project

## Purpose

The Project folder holds the canonical project-level documentation — the foundational reference material that defines what the project is, how it works, and what standards it follows. These documents are the first stop for onboarding, alignment, and authoritative project information.

## Contents

| File | Description |
|------|-------------|
| `ProjectGoals.md` | High-level goals, objectives, and success criteria |
| `Roadmap.md` | Timeline, milestones, and phased delivery plan |
| `Architecture.md` | High-level architecture overview (detailed ADRs in `04 Architecture/`) |
| `CodingStandards.md` | Code style, formatting, and linting rules |
| `TechStack.md` | All technologies, frameworks, and tools used |
| `ComponentRegistry.md` | Catalog of all components/modules and their responsibilities |
| `APIReference.md` | API endpoint documentation and contracts |
| `DatabaseSchema.md` | Database tables, relationships, and migrations |
| `DeploymentGuide.md` | How to deploy to each environment |
| `TestingGuide.md` | Testing strategy, frameworks, and coverage targets |
| `PerformanceGoals.md` | Performance budgets, SLOs, and benchmarks |
| `SecurityChecklist.md` | Security requirements and audit checklist |
| `RiskRegister.md` | Identified risks, probabilities, and mitigations |
| `DevelopmentGuide.md` | Developer onboarding and environment setup |
| `FutureIdeas.md` | Backlog of ideas not yet committed to roadmap |
| `LessonsLearned.md` | Post-mortem insights and retrospective notes |
| `Glossary.md` | Domain and project-specific terminology |
| `ReleaseNotes.md` | Changelog of released versions |
| `README.md` | This file |

## Workflow

1. **Onboarding**: New team members and AI agents read `ProjectGoals.md`, `TechStack.md`, and `DevelopmentGuide.md` first.
2. **Reference**: During development, consult `CodingStandards.md`, `APIReference.md`, `DatabaseSchema.md`, and `ComponentRegistry.md`.
3. **Updates**: Project documents are updated whenever a significant change occurs — new dependency, schema migration, API change, or standard update.
4. **Review**: Project documents are reviewed at the start of each sprint for accuracy and relevance.
5. **Authority**: When `shared-context/` and `knowledge/01 Project/` disagree, `shared-context/` is authoritative. File a discrepancy in `07 Debugging/`.

## Conventions

- Each document follows the standard section structure: Purpose, Audience, AI Usage, Human Usage, Templates, Examples.
- Use tables for structured reference data (endpoints, schema columns, components).
- Use code blocks for configuration, commands, and code examples.
- Tag documents with `<!-- status: draft | review | stable | deprecated -->` at the top.
- Link to detailed docs in other folders rather than duplicating content.
- Version-sensitive content includes the version or date it applies to.

## Examples

```markdown
## APIReference.md excerpt

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | /api/v1/users | List all users | Bearer |
| POST | /api/v1/users | Create a user | Bearer |
```

```markdown
## TechStack.md excerpt

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Frontend | React | 19.x | UI framework |
| Backend | Node.js | 22 LTS | Server runtime |
```
