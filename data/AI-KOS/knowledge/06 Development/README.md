# 06 Development

## Purpose

The Development folder contains practical guides, how-tos, and reference material for day-to-day development work. It bridges the gap between project-level documentation and actual coding — covering setup, workflows, common tasks, and troubleshooting tips.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `LocalSetup.md` | Guide | Step-by-step environment setup |
| `GitWorkflow.md` | Guide | Branching, committing, and PR process |
| `CodeReviewChecklist.md` | Checklist | What to look for in code reviews |
| `CommonTasks.md` | How-To | Frequently performed development tasks |
| `DebuggingGuide.md` | Guide | How to debug common issues (see also `07 Debugging/`) |
| `PerformanceProfiling.md` | Guide | How to profile and optimize |
| `DatabaseMigrations.md` | How-To | How to create and run migrations |
| `CI-CD-Pipeline.md` | Guide | How the CI/CD pipeline works |
| `README.md` | Guide | This file |

## Workflow

1. **Onboarding**: New developers follow `LocalSetup.md` and `GitWorkflow.md` to get started.
2. **Daily Reference**: Consult `CommonTasks.md` and `CodeReviewChecklist.md` during development.
3. **Updates**: Development guides are updated when workflows change (new tooling, new process).
4. **Troubleshooting**: When encountering issues, check `DebuggingGuide.md` first, then escalate to `07 Debugging/`.
5. **CI/CD**: Before pushing, review `CI-CD-Pipeline.md` to understand what checks will run.

## Conventions

- Guides use numbered steps for sequential procedures.
- Code blocks include the language tag for syntax highlighting.
- Commands are prefixed with `$` for terminal commands and `>` for REPL.
- Each guide includes a `Prerequisites` section at the top.
- Cross-link to `01 Project/CodingStandards.md` rather than duplicating standards.
- Tag guides with `<!-- level: beginner | intermediate | advanced -->`.

## Examples

```markdown
## LocalSetup.md excerpt

## Prerequisites
- Node.js 22 LTS
- Docker Desktop
- Git

## Steps
1. Clone the repository
   ```bash
   $ git clone https://github.com/org/repo.git
   ```

2. Install dependencies
   ```bash
   $ npm install
   ```
```

```markdown
## GitWorkflow.md excerpt

## Branch Naming
- Feature: `feature/<ticket-id>-<short-description>`
- Bugfix: `fix/<ticket-id>-<short-description>`
- Hotfix: `hotfix/<short-description>`
```
