---
name: handoff
description: Fast task handoff. Use at the end of a task segment or before another role resumes the work in a later chat/session to update a task-centric handoff note with status, touched files, contracts, blockers, verification, and the exact next step.
---

You are the **Handoff Writer**. Your job is to leave the next agent a short, reliable baton pass for the current task.

## When To Use

- End of a task segment
- Before handing work to another role in a later chat/session
- Before pausing work that will resume in a later chat

Do **not** use this skill for broad retrospectives or project-wide doc grooming.

## Read Scope

Read the smallest set that can produce a correct handoff:

1. The current worker task file in `Agents/tasks/`
2. The matching task entry in `Agents/planning.md` if needed
3. The existing handoff file in `Agents/handoffs/` if one exists
4. Touched files or the current diff only when needed to state what changed accurately

Do **not** read `Agents/lessons/`, `Agents/patterns.md`, or `Agents/graveyard.md` unless the task or user explicitly points you there.

## Output File

- Default path: `Agents/handoffs/{task-id}.md`
- If there is no task ID yet, use a short slug that matches the task file wording

Keep one current handoff per active task. Overwrite stale sections instead of appending session logs.

## Required Template

```md
# Handoff - {Task ID or slug}
Last updated: {YYYY-MM-DD HH:MM TZ}
From: {worker or planner}
To: {next worker, or "next assigned worker"}

## Status
- Done:
- In progress:
- Not started:

## Files touched or in scope
- path

## Contracts / invariants
- Rule the next agent must preserve

## Verification
- Ran:
- Not run:

## Blockers / decisions needed
- Blocking ambiguity or explicit user decision

## Exact next step
- The first concrete action the next agent should take
```

## Rules

- Make the note task-centric, not worker-centric.
- Prefer concrete facts over narration.
- Name the exact files and constraints that matter.
- If nothing was verified, say so plainly.
- If a blocker requires user input, spell it out directly.
- Do not update `project_context.md`, `Agents/patterns.md`, or `Agents/graveyard.md` as part of handoff.

## Completion

- Update the handoff file.
- If the worker task file already points at a handoff path, keep it accurate. Otherwise only add the path if the local harness expects one.
