---
file: SharedContext.md
purpose: THE FIRST FILE every AI reads — project vision, stack, rules, and constraints
last_updated: 2026-06-29
updated_by: system
version: 1.0.0
---

## Purpose

This file is the entry point for all AI agents. It contains the essential project
context needed to understand what we are building, how we build it, and what rules
govern the process. Read this completely before taking any action.

## Update Rules

- Only update this file when project-level facts change (stack, vision, rules, constraints).
- Any change to this file requires a corresponding entry in `DecisionLog.md`.
- Bump `version` on every edit. Use semantic versioning.
- Keep under 300 lines. Move detail to specialized files if needed.

## Content

### Project

| Field | Value |
|-------|-------|
| Name | ProjectNova |
| Type | Web Application (SaaS) |
| Description | Task management SaaS with real-time collaboration, AI-assisted task breakdown, and cross-team dependency tracking |
| Repository | github.com/roopalisingh/DPSI-LFR |
| License | Proprietary |
| Stage | MVP — pre-launch |

### Vision

Empower teams to ship faster by turning ambiguous goals into actionable, tracked,
and dependency-aware tasks — with AI assistance that reduces planning overhead by 80%.

### Goals

1. Ship a functional MVP with core task CRUD, boards, and real-time sync by Q3 2026.
2. Integrate AI-assisted task breakdown and prioritization by Q4 2026.
3. Achieve sub-200ms API response time at p99 for all core endpoints.
4. Support 10,000 concurrent users on a single production cluster.
5. Maintain 90%+ test coverage on all critical paths.

### Current Milestone

**Milestone 3: Real-Time Collaboration Layer** — WebSocket-based live updates for
boards, task assignments, and presence indicators. Target completion: 2026-07-15.

### Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | React + TypeScript | 18.3 / 5.4 |
| Backend | Node.js + Fastify | 20 LTS / 4.28 |
| Database | PostgreSQL | 16 |
| Cache | Redis | 7.2 |
| Real-time | WebSocket (ws) | 8.18 |
| ORM | Prisma | 5.18 |
| Queue | BullMQ | 5.1 |
| Auth | JWT + refresh tokens | — |
| Testing | Vitest + Playwright | 1.6 / 1.45 |
| CI/CD | GitHub Actions | — |
| Hosting | AWS (ECS Fargate + RDS) | — |
| Monitoring | Datadog + Sentry | — |

### Architecture Summary

```
Client (React SPA)
  ↕ HTTPS / WebSocket
API Gateway (Fastify)
  ├── Auth Service (JWT)
  ├── Task Service (CRUD + boards)
  ├── Collaboration Service (WebSocket hub)
  ├── Notification Service (BullMQ workers)
  └── AI Service (task breakdown, prioritization)
  ↕
PostgreSQL (primary store) + Redis (cache + pub/sub + queues)
```

### Coding Standards

- **Language**: TypeScript strict mode on all layers. No `any` without a comment.
- **Style**: ESLint + Prettier. Run `npm run lint` before every commit.
- **Naming**: `camelCase` for variables/functions, `PascalCase` for types/components, `SCREAMING_SNAKE` for constants.
- **File structure**: Feature-based folders (`src/features/tasks/`, `src/features/boards/`).
- **Error handling**: All async functions use Result types or try/catch with typed errors.
- **API design**: RESTful with versioned routes (`/api/v1/`). WebSocket events use `resource:action` format.
- **Database**: All migrations are reversible. Never use raw SQL without review.
- **Testing**: Unit tests colocated with source. E2E tests in `tests/e2e/`.

### Constraints

- No PII in logs. All PII fields encrypted at rest using AES-256.
- API rate limit: 100 requests/minute per user, 1000/minute per org.
- WebSocket connections max 5 per user session.
- No external API calls in request handlers — use the queue.
- Bundle size must stay under 250KB gzipped for the initial load.

### Repository Rules

- `main` branch is always deployable. Never commit directly to `main`.
- All changes via pull request. Minimum 1 approval required.
- Squash merges only. Commit messages follow Conventional Commits.
- No secrets in code. Use `.env.local` (gitignored) and AWS Secrets Manager in prod.
- Run `npm run lint && npm run typecheck && npm test` before requesting review.

### Communication Rules

- All agent actions logged in `RecentChanges.md` and `SessionSummary.md`.
- Disagreements between agents resolved by logging to `DecisionLog.md` with rationale.
- Never edit a file locked by another agent — request handoff in `ActiveAgents.md`.
- Use `CurrentTask.md` notes section for async communication about the active task.

### Branch Strategy

| Branch Pattern | Purpose |
|---------------|---------|
| `main` | Production-ready code |
| `develop` | Integration branch for the next release |
| `feature/<task-id>-<slug>` | Feature development |
| `fix/<task-id>-<slug>` | Bug fixes |
| `hotfix/<slug>` | Production hotfixes |

### Definition of Done

A task is complete when ALL of the following are true:
1. Code written, linted, and type-checked with zero errors.
2. Unit tests written and passing (90%+ coverage on changed lines).
3. E2E tests written for user-facing changes.
4. Documentation updated (API docs, component docs as needed).
5. `CurrentTask.md` marked complete, `TaskHistory.md` appended.
6. PR merged to `develop` (or `main` for hotfixes).
7. `RecentChanges.md` updated with all modified files.

### Important Decisions

See `DecisionLog.md` for the full history. Key decisions:
- **D001**: Fastify over Express for performance and schema validation.
- **D002**: Prisma over raw SQL for type safety and migration tooling.
- **D003**: WebSocket over SSE for bidirectional real-time needs.
- **D004**: Feature-based folder structure over layer-based.

### Current Priorities

1. Complete the real-time collaboration WebSocket layer (Milestone 3).
2. Fix Known Issue KI-003 (WebSocket reconnection race condition).
3. Set up production staging environment on AWS.
4. Write E2E tests for the task board drag-and-drop flow.

## Example

An agent reading this file should conclude:
- This is a TypeScript SaaS using React + Fastify + PostgreSQL + Redis.
- We are in MVP stage, building real-time collaboration.
- I must use feature-based folders, strict TypeScript, and conventional commits.
- I need to check `CurrentTask.md` to see what is actively being worked on.
- I need to check `Locks.md` before editing any shared files.

## AI Instructions

- Read this file completely at the start of every session.
- Do not begin work until you understand the tech stack, constraints, and rules.
- If any information here contradicts what you see in the codebase, trust the codebase and update this file.
- Keep this file under 300 lines — move detail to specialized files.
- Never edit this file without logging a decision in `DecisionLog.md`.
