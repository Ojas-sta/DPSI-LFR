# 05 Research

## Purpose

The Research folder captures investigative work — spikes, proofs of concept, technology evaluations, and exploratory analysis. Research notes are the raw output of learning activities that may or may not lead to project decisions. They preserve the reasoning behind what was explored and what was learned.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `RES-NNN-<Title>.md` | Research Note | Individual research/spike documents |
| `TechEvaluation-<Topic>.md` | Evaluation | Comparative analysis of technologies |
| `POC-<Topic>.md` | POC Report | Proof of concept findings |
| `ResearchIndex.md` | Index | Chronological list of all research notes |
| `README.md` | Guide | This file |

## Workflow

1. **Spike Creation**: When a spike or investigation is needed, create a `RES-NNN-<Title>.md` file.
2. **Research**: Document findings, code snippets, benchmarks, and references as you go.
3. **Conclusion**: Each research note ends with a `Conclusion` section: proceed, abandon, or needs more investigation.
4. **Promotion**: If research leads to a decision, create an ADR in `04 Architecture/` and/or a decision in `08 Decisions/`, linking back to the research note.
5. **Archive**: Completed research that has been acted upon is moved to `15 Archive/` after the decision is implemented.
6. **Indexing**: Update `ResearchIndex.md` with each new research note.

## Conventions

- Research note filenames: `RES-NNN-Short-Title.md` (kebab-case, sequential numbering).
- Each note includes: `Date`, `Researcher`, `Question`, `Methodology`, `Findings`, `Conclusion`.
- Use code blocks for experimental code and benchmarks.
- Tag notes with `<!-- status: active | concluded | archived -->`.
- Include references and links to external resources.
- Distinguish between proven facts and hypotheses explicitly.

## Examples

```markdown
## RES-001 excerpt

## Question
Should we use Redis or PostgreSQL for session storage?

## Methodology
- Benchmark both with 10k concurrent sessions
- Measure read/write latency and memory usage

## Findings
| Metric | Redis | PostgreSQL |
|--------|-------|------------|
| Read latency | 0.3ms | 1.2ms |
| Write latency | 0.4ms | 2.1ms |

## Conclusion
Proceed with Redis for session storage. See ADR-003.
```
