# Julius Tasks

Planner owns the assignment fields in this file. Julius uses it as the current execution contract.

Keep this file execution-only. Do not copy product rationale, option analysis, or planner strategy here.

<!--
## How To Use This File

- Claudia fills this file when assigning Julius work.
- Keep this file execution-only.
- Put live task scope here instead of relying on role-name assumptions.
-->

## Assigned Queue

- Status: assigned
- Active now: T-1 (M0 — skeleton & conventions)
- Next in sequence: T-4 (M4 — reflection playbook) → T-5 (M5 — run docs)
- Queue order and priority: T-1 (P0) → T-4 (P1) → T-5 (P1)
- Files / write scope: `AGENTS.md` (product operating section), `Moon/README.md`, `Moon/config/categories.md`, `Moon/playbooks/**`, `.gitignore`. Do not edit `Moon/scripts/**` or `Moon/config/feeds.example.yaml` (Augustus's scope).
- Current handoff: [handoffs/julius-m0-m4-m5.md](../handoffs/julius-m0-m4-m5.md)
- Dependencies: read-only consumer of Augustus's data contracts (`events.json`) for the M4 auto-draft; build the reflection ritual itself without waiting on Augustus.
- Verification: low-cost — render the playbook against a sample week's `events.json` and confirm `reflection.md` is written correctly.
- User-approved to execute: no — confirm before any high-cost step (see `planning.md` 3c).
- Report back if blocked by assumption: yes
- Handoff notes: T-1, T-4, and the Julius portion of T-5 are complete and verified (T-4 against a synthetic `events.json` only). See the handoff above. Remaining cross-role step: run the reflection playbook against a real `events.json` once Augustus's Engine A produces one.

## Execution Notes

- Implement in this order:
  1. **M0 conventions** — create the `Moon/` skeleton; add a product operating section to `AGENTS.md` (how any agentic tool runs the weekly flow, tool-agnostic); write `Moon/README.md` (directory layout); write `Moon/config/categories.md` (the 8 categories — Learn, Build, Career, Habit, Workout, Social, Exploration, Trash — each with a one-line description); add `.gitignore` entries for `Moon/config/feeds.yaml` and `Moon/weeks/`.
  2. **M4 reflection playbook** — in `Moon/playbooks/`, a playbook that asks the 6 questions one at a time (Happiness → What's your plan? → How did it go? → What did you do this week? → What might stress you up? → Future-self, would I do differently?), proofreads each answer (fix typos/grammar only, never change meaning), and writes `Moon/weeks/<ISO-week>/reflection.md`. Auto-draft the "What did you do this week?" answer from that week's `events.json` titles (read-only).
  3. **M5 run docs** — document the weekly run in `AGENTS.md`: the interactive session plus an optional portable system-cron nudge (not a Claude-Code-only mechanism).
- Author markdown to be Obsidian-vault friendly (frontmatter, headings); keep the reflection output a clean, proofread record.
