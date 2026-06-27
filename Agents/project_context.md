# Project Context

<!--
## How To Use This File

- Use this file for durable project context only.
- Update it when the product shape, system boundaries, stack, or non-negotiable rules change.
- Do not use this file as a sprint log, task tracker, or session summary.
-->

Shared high-level context for all agents. This file is intentionally architectural and durable. It should not be used as a sprint log, status board, or session history.

## 1. Purpose

- Describe only the durable facts every agent should know before touching the project.
- Give every agent enough shared context to reason about the codebase before reading role docs or task docs.
- Stay high level. Detailed implementation notes, file-by-file guidance, and temporary task context belong elsewhere.

## 2. Maintenance Contract

- Do update this file when the product shape changes, a core subsystem changes, a backend/storage choice changes, or a project-wide rule changes.
- Do not update this file for task progress, bug triage, one-off fixes, completed phases, or temporary work-in-progress notes.
- The agent who changes architecture or introduces a new durable constraint is responsible for updating this file in the same task.
- If a subsystem is in transition, document the boundary or ambiguity at a high level instead of narrating the full history.
- Put task baton-pass notes in [handoffs/](handoffs). Put hard-question learnings in [lessons/](lessons). Put stable cross-task patterns in [patterns.md](patterns.md). Put only high-value cross-task failures in [graveyard.md](graveyard.md).
- If a section does not matter yet, leave it short or blank rather than inventing detail.

## 3. What This Project Is

- Product or system name:
- One-sentence description:
- Primary users, operators, or collaborators:
  - Group:
  - Group:
  - Group:
- Core workflows, surfaces, or jobs every agent should understand:
  - Workflow or surface:
  - Workflow or surface:
  - Workflow or surface:

## 4. Durable Technical Shape

- Platform(s), runtime(s), or environment(s) only if they affect design decisions:
- Major technologies or stack choices only if they are architecturally important:
- Main data, state, or storage owners:
- External systems or dependencies that materially constrain the project:

## 5. Boundaries And Source Of Truth

- Main components, subsystems, or ownership areas:
  - Component:
  - Component:
  - Component:
- Source-of-truth boundaries agents must not violate:
- Coupling, layering, or interface rules agents should preserve:
- Migration, compatibility, or legacy constraints that affect reasoning:
- Environments, secrets, or operational dependencies:

## 6. Core Project Rules

- Rule:
- Rule:
- Rule:
- Read, query, preview, or inspection paths should stay side-effect free when that is a system requirement.
- If degraded or offline operation matters for this project, preserve a usable failure mode when dependencies are unavailable.

## 7. Collaboration Map

- [onboarding.md](onboarding.md) is the mandatory first read for every agent.
- `project_context.md` is shared, high-level context only.
- Role docs (`claudia.md`, `augustus.md`, `julius.md`) define stable collaboration rules. Worker scope is planner-assigned unless your project intentionally adds durable role biases.
- Each chat/session has exactly one active role. Roles do not switch mid-session, and one chat does not run another role live.
- [planning.md](planning.md) is Claudia-owned and is the single iteration source of truth for task allocation, implementation strategy, and worker execution planning.
- Claudia edits planner-owned coordination docs only. Augustus and Julius own implementation code within their assigned write scopes.
- `tasks/` holds current worker assignments for Augustus and Julius.
- `handoffs/` holds current task baton-pass notes for later chats/sessions.
- `lessons/` holds task/problem-specific learnings worth reusing in later chats.
- `Human/` is not part of default agent context.

## 8. Non-Negotiable Rules

- Always read a file before editing it, even mid-session.
- Never merge to `main` unless the user explicitly asks.
- Never push to `origin/main` unless the user explicitly asks.
- Preserve explicit source-of-truth boundaries. Do not create competing state without documenting it here.
- Keep side-effect-free paths side-effect free when the project defines them that way.
- Risky migrations and backfills need explicit approval before live execution.
- High-cost validation should stay opt-in.
- When a rollout changes identity, ownership, permissions, or durable data shape, preserve existing data before polishing workflow details around it.
- Prefer durable constraints over exhaustive description. If a detail will go stale quickly, it probably does not belong here.
- Add project-specific rules below:
  - Rule:
  - Rule:
