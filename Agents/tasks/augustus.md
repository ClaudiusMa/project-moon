# Augustus Tasks

Planner owns the assignment fields in this file. Augustus uses it as the current execution contract.

Keep this file execution-only. Do not copy product rationale, option analysis, or planner strategy here.

<!--
## How To Use This File

- Claudia fills this file when assigning Augustus work.
- Keep this file execution-only.
- Put live task scope here instead of relying on role-name assumptions.
-->

## Assigned Queue

- Status: assigned
- Active now: T-2 (M1 — calendar ingestion)
- Next in sequence: T-3 (M2 — cognitive-hour engine) → T-5 (M5 — `moon-weekly` runner)
- Queue order and priority: T-2 (P0) → T-3 (P0) → T-5 (P1)
- Files / write scope: `Moon/scripts/**`, `Moon/config/feeds.example.yaml`. Do not edit `AGENTS.md`, `Moon/README.md`, `Moon/config/categories.md`, or `Moon/playbooks/**` (Julius's scope).
- Current handoff: none (first assignment)
- Dependencies: `feeds.yaml` schema is yours to define; category list and `Moon/` layout come from Julius's T-1, but you may proceed against the data contracts in `planning.md` without waiting.
- Verification: run over the sample `.ics` (user's `Building` export) and inspect `events.json` / `time-report.md`. Low-cost only by default.
- User-approved to execute: no — installing Python deps and running the full pipeline is high-cost and needs explicit user approval first (see `planning.md` 3c).
- Report back if blocked by assumption: yes
- Handoff notes: -

## Execution Notes

- Implement in this order:
  1. **M1 ingestion** — read one `.ics` per category from paths in `feeds.yaml`; expand recurrence with a recurrence-aware iCal library (handle `RRULE`, `EXDATE`, `RECURRENCE-ID` overrides); normalize all times to local tz; bucket into a Mon–Sun week; emit `Moon/weeks/<ISO-week>/events.json` as `{uid, category, title, start_local, end_local, duration_min}`, tagging category from the feed map.
  2. **M2 engine** — per category, merge overlapping/adjacent events into blocks, ceil each block to whole hours, sum; count everything (no minimum-duration floor); cross-category overlaps count in both. Render `Moon/weeks/<ISO-week>/time-report.md` and append long-format rows to `Moon/trends.csv` (`week_iso, category, cognitive_hours, raw_minutes, event_count`).
  3. **M5 runner** — `moon-weekly` script chaining ingestion → engine for the most recent completed week, printing a summary, then pointing to the reflection playbook.
- Verify recurrence/tz correctness against the sample `.ics` before trusting totals; report any contract mismatch rather than silently changing the schema.
