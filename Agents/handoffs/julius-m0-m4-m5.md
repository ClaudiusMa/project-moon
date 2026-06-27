# Handoff - T-1 / T-4 / T-5 (Julius — conventions + Engine B)

Last updated: 2026-06-14 13:30 PT
From: Julius
To: next assigned worker (Augustus for Engine A; whoever runs end-to-end verification)

## Status

- Done:
  - **T-1 / M0 — skeleton & conventions.** Added the *Project Moon — Product
    Operating Layer* section to `AGENTS.md`; created `Moon/README.md` (layout),
    `Moon/config/categories.md` (the 8 fixed categories + one-liners), and the
    repo-root `.gitignore` (`Moon/config/feeds.yaml`, `Moon/weeks/`).
  - **T-4 / M4 — reflection playbook.** `Moon/playbooks/reflection.md`: 6 questions
    asked one at a time, proofread (typos/grammar only), written to
    `Moon/weeks/<ISO-week>/reflection.md`; Q4 auto-drafts from `events.json` titles
    (read-only). Includes degraded mode (no `events.json` → ask Q4 cold; existing
    reflection → confirm before overwrite).
  - **T-5 (Julius portion) — run docs.** Added *Running the weekly flow* and
    *Scheduling (optional, portable)* to `AGENTS.md`: compute (unattended
    `moon-weekly`) + reflect (interactive), plus a portable system-`cron` nudge.
- In progress: none.
- Not started (other owners): Augustus's T-2/T-3 (Engine A) and the `moon-weekly`
  runner script (T-5 Augustus portion).

## Files touched or in scope

- `AGENTS.md` (Project Moon product operating section — Julius scope only)
- `Moon/README.md`
- `Moon/config/categories.md`
- `Moon/playbooks/reflection.md`
- `.gitignore`
- Did **not** touch `Moon/scripts/**` or `Moon/config/feeds.example.yaml` (Augustus).

## Contracts / invariants

- Docs are written against the fixed data contracts in `planning.md` §3a (events.json
  fields, trends.csv columns, week = ISO Mon–Sun local). If Engine A changes a shape,
  update `planning.md` first, then these docs.
- The reflection playbook **reads `events.json` read-only** and must never mutate it.
- Reflection files are dated personal records — don't overwrite without confirmation.
- The 8 category **names** are the cross-cutting key (calendars ↔ feeds.yaml ↔
  reports ↔ trends.csv). Keep them exactly: Learn, Build, Career, Habit, Workout,
  Social, Exploration, Trash.

## Verification

- Ran: `Moon/` structure check; `git check-ignore` confirms `feeds.yaml` + `weeks/`
  are ignored; reflection playbook logic exercised against a **synthetic**
  `events.json` (stdlib only, no installs) — Q4 grouping + dedupe correct, template
  renders, `events.json` read stayed side-effect free. Synthetic week was deleted.
- Not run: end-to-end against a **real** `events.json` from Engine A (doesn't exist
  yet) and the full pipeline run (high-cost, unapproved — `planning.md` §3c).

## Blockers / decisions needed

- None blocking Julius's queue (all three tasks complete).
- Still open for the project: high-cost approval in `planning.md` §3c (`pip install`
  iCal/recurrence/tz libs + first pipeline run over the sample `.ics`).
- `planning.md` is planner-owned — Julius did not edit it. Claudia can mark the
  Julius rows of T-1/T-4/T-5 done.

## Exact next step

- After Augustus produces a real `Moon/weeks/<ISO-week>/events.json`, run the
  reflection playbook against it once to confirm the Q4 auto-draft reads real titles
  correctly and `reflection.md` writes as specified — the one piece verified only
  synthetically so far.
