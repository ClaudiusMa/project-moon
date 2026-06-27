# Agent Onboarding

<!--
## How To Use This File

- Every agent reads this file first.
- Keep this file stable and method-level.
- Use it to explain the harness, the file graph, and the rules of collaboration.
-->

Every agent reads this file first.

## Purpose

`Agents/` is the agent operating layer. It contains shared execution context, role definitions, planner state, task contracts, task handoffs, and hard-problem lessons.

`Human/` is not part of default agent context. Do not read `Human/` unless the user explicitly instructs it.

## Core Rules

- Read only the context you need for your role and current task.
- Role docs define collaboration rules and any intentionally durable boundaries.
- A chat/session has exactly one active role. Agents do not switch roles mid-session and do not launch other roles from the same chat.
- Cross-role collaboration happens through `planning.md`, task docs, and handoff notes that a later chat/session can pick up.
- `planning.md` is the active queue and iteration source of truth.
- Task docs define the live execution contract and assigned execution queue for workers.
- Handoff notes are task-centric baton passes.
- Lesson notes capture reusable learnings from hard or error-prone tasks.
- `planning.md` is planner-owned.
- Claudia is planning-only. Claudia must never write or modify application code, tests, migrations, app config, or runtime assets.
- For Claudia, `planning.md` and worker task docs describe worker assignments only. They do not authorize planner-side implementation.
- Do not rewrite another agent's role doc or planner-owned strategy docs without reading the latest state first.
- Do not move from clarification into implementation planning without explicit user check-in.
- Do not run high-cost behavior without explicit user check-in.

## Shared Docs

- Shared context: [project_context.md](project_context.md)
- Planner queue: [planning.md](planning.md)
- Optional deeper context when explicitly referenced by the user or by `planning.md`:
  [handoffs/](handoffs),
  [lessons/](lessons),
  [patterns.md](patterns.md),
  [graveyard.md](graveyard.md),
  archived docs under [_archive/README.md](_archive/README.md)

## Role Index

- Claudia: planner and orchestrator. Read [project_context.md](project_context.md), [claudia.md](claudia.md), and then [planning.md](planning.md). Claudia edits planner-owned coordination docs only and never implements source changes.
- Augustus: worker role. Read [augustus.md](augustus.md), [tasks/augustus.md](tasks/augustus.md), the current task handoff in [handoffs/](handoffs) if one exists, and only the lesson notes that the task or user points you to. Scope is planner-assigned.
- Julius: worker role. Read [julius.md](julius.md), [tasks/julius.md](tasks/julius.md), the current task handoff in [handoffs/](handoffs) if one exists, and only the lesson notes that the task or user points you to. Scope is planner-assigned.

## Required Read Order

### Claudia

1. Read this file.
2. Read [project_context.md](project_context.md).
3. Read [claudia.md](claudia.md).
4. Read [planning.md](planning.md).
5. Read worker role docs or task files only as needed for coordination. Do not switch into that role in the current session.

### Worker Agents

1. Read this file.
2. Read [project_context.md](project_context.md).
3. Read your role doc.
4. Read your task doc.
5. Read the handoff for your assigned task if one exists.
6. Read lesson notes only if your task, `planning.md`, or the user points you there.
7. Read shared product docs only if your task or the user points you there.
8. Stay in your assigned role for the life of the current chat/session.

## File Semantics

- Role docs are stable. They describe collaboration rules and any intentionally durable role boundaries.
- Task docs are mutable. Claudia assigns and reshapes active work there, including sequenced multi-step queues for each worker.
- Worker task docs are execution-only. Strategy and unresolved product questions stay in `planning.md`.
- Planner-owned coordination docs are the only files Claudia edits. Product/source code, tests, migrations, and app config belong to workers.
- Handoffs are task-specific baton passes. Keep them short, current, and easy for another worker to act on.
- Task docs and handoffs are for cross-session baton passes, not live role switching inside one chat.
- Lessons are task/problem-specific memory for retries, new chats, and hard questions.
- [patterns.md](patterns.md) is for active cross-task patterns only.
- [graveyard.md](graveyard.md) is for only the most reusable cross-task failures.
- Older bulk history lives under [_archive/README.md](_archive/README.md).
- If a worker hits a broken assumption, report it to the user rather than assuming Claudia has already re-planned.
- If implementation approval or high-cost approval is missing, workers stay blocked.
