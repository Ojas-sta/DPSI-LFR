# 02 Context

## Purpose

The Context folder stores background information, domain knowledge, and environmental context that is not project-specific documentation but is essential for understanding the problem space. This includes industry context, competitive analysis, domain primers, and historical background that informs project decisions.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `DomainPrimer.md` | Guide | Introduction to the domain and key concepts |
| `StakeholderMap.md` | Reference | Who the stakeholders are and their interests |
| `CompetitiveAnalysis.md` | Analysis | Overview of competing solutions |
| `HistoricalContext.md` | Narrative | How the project arrived at its current state |
| `Glossary-Extended.md` | Reference | Extended domain glossary (see also `01 Project/Glossary.md`) |
| `ExternalConstraints.md` | Reference | Regulatory, legal, or organizational constraints |
| `README.md` | Guide | This file |

## Workflow

1. **Onboarding**: Read `DomainPrimer.md` and `StakeholderMap.md` before working on project features.
2. **Research**: When investigating new areas, add findings here before promoting them to `05 Research/` or `01 Project/`.
3. **Reference**: Consult `ExternalConstraints.md` when making architecture or feature decisions.
4. **Updates**: Context is relatively stable — update when domain understanding shifts significantly.
5. **Linking**: Link from decisions and planning docs back to context entries that informed them.

## Conventions

- Use narrative prose for domain primers and historical context.
- Use tables for stakeholder maps and competitive analysis.
- Tag each document with `domain: <area>` for searchability.
- Distinguish facts from opinions explicitly (`[Fact]` vs `[Opinion]`).
- Cite sources for external information.
- Keep domain glossary terms synchronized with `01 Project/Glossary.md`.

## Examples

```markdown
## DomainPrimer.md excerpt

The DPSI-LFR project operates in the domain of AI-orchestrated knowledge
management systems. The core challenge is maintaining a coherent, machine-
readable context layer that multiple AI agents can share without drift.
```

```markdown
## StakeholderMap.md excerpt

| Stakeholder | Role | Interest | Influence |
|------------|------|----------|-----------|
| Dev Team | Builders | Technical feasibility | High |
| Product | Owner | Feature delivery | High |
| End Users | Consumers | Usability, reliability | Medium |
```
