# AI-KOS Prompt Library

## Purpose

This directory contains the agent prompt templates that define each AI agent's
role, responsibilities, constraints, and expected outputs within the AI-KOS
multi-agent system.

## How to Use

1. Select the prompt that matches the task you need performed.
2. Every prompt begins with a **Mandatory Pre-Flight Sequence**—an 11-step
   checklist that must be executed in order before any role-specific work
   begins.
3. Read the shared-context files listed in the preamble, claim required locks,
   perform the work, update documentation, and release locks.
4. Follow the role-specific instructions, constraints, output format, and
   success criteria defined in each prompt file.

## Prompt Files

| File | Role | Primary Responsibility |
|------|------|----------------------|
| `Planner.md` | Planner | Task decomposition, estimation, priority assignment |
| `Architect.md` | Architect | Architecture design, pattern selection, trade-off analysis |
| `Researcher.md` | Researcher | Technology evaluation, spike investigation, literature review |
| `Builder.md` | Builder | Feature implementation, test writing, code quality |
| `Reviewer.md` | Reviewer | Code review, standards check, quality gate |
| `Debugger.md` | Debugger | Bug investigation, root cause analysis, fix verification |
| `Refactorer.md` | Refactorer | Code refactoring, technical debt reduction, pattern application |
| `PerformanceOptimizer.md` | Performance Optimizer | Profiling, bottleneck identification, optimization |
| `SecurityAuditor.md` | Security Auditor | Vulnerability scanning, security review, hardening |
| `DocumentationWriter.md` | Documentation Writer | Doc generation, API docs, guides |
| `TestingAgent.md` | Testing Agent | Test planning, test writing, coverage analysis |
| `ProjectManager.md` | Project Manager | Sprint planning, progress tracking, risk management |

## Pre-Flight Sequence

Every prompt in this library enforces the following mandatory pre-flight
sequence before role-specific work begins:

```
## Mandatory Pre-Flight Sequence
1. Read `shared-context/SharedContext.md`
2. Read `shared-context/ProjectState.md`
3. Read `shared-context/CurrentTask.md`
4. Read `shared-context/DecisionLog.md`
5. Read `shared-context/ArchitectureSnapshot.md`
6. Read `shared-context/RecentChanges.md`
7. Read `shared-context/Locks.md`
8. Claim required locks
9. Perform work
10. Update documentation
11. Release locks
```

This ensures every agent operates with full context awareness and never makes
conflicting changes to shared resources.

## Conventions

- All prompts are written in Markdown.
- Role-specific instructions follow the pre-flight sequence.
- Each prompt specifies constraints, an output format, and success criteria.
- Prompts reference files in `shared-context/` by relative path.
- Locks must be claimed and released per the lock protocol in
  `shared-context/Locks.md`.
