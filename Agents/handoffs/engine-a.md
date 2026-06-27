# Handoff - Engine A (T-2 / T-3 / T-5)

Last updated: 2026-06-15 10:58 PDT
From: Augustus
To: Claudia (decisions) + Julius (T-4 consumes `events.json`; T-5 run docs)

## Status

- Done: T-2 (M1 ingestion), T-3 (M2 cognitive-hour engine), T-5 (`moon-weekly` runner). Implemented and verified against the real `Building` export.
- In progress: none.
- Not started: nothing in Augustus's queue.

## Files touched or in scope

- `Moon/scripts/moon_common.py` — paths, category set, tz, ISO-week math, feed-config loader (PyYAML + zero-dep fallback).
- `Moon/scripts/ingest.py` — M1: `.ics` → recurrence expand → local-tz → Mon–Sun week → `events.json`.
- `Moon/scripts/engine.py` — M2: per-category merge → ceil-per-block → sum → `time-report.md` + upsert `trends.csv`. Pure stdlib.
- `Moon/scripts/moon-weekly` — M5 runner (ingest→engine for most recent completed week).
- `Moon/scripts/requirements.txt`, `Moon/scripts/README.md`, `Moon/config/feeds.example.yaml`.

## Contracts / invariants (as built — match `planning.md` + `Moon/README.md`)

- `events.json`: array of `{uid, category, title, start_local, end_local, duration_min}`. `start/end_local` are ISO-8601 with offset; bucketed by **local start** into the Mon–Sun ISO week. Recurring occurrences share the source `uid` (engine merges by time, not uid).
- `time-report.md`: YAML frontmatter (`week,start,end,cognitive_hours,generator`) + Summary table + per-category event log. Obsidian-friendly.
- `trends.csv`: `week_iso,category,cognitive_hours,raw_minutes,event_count`. Upserted per week (rerun replaces that week's rows). `raw_minutes` = post-merge union of covered time; `cognitive_hours` = sum of each block ceil'd to whole hours.
- Category = the **feed key** in `feeds.yaml` (never the title or `X-WR-CALNAME`). Fixed 8-key set.

## Verification

- Ran: offline unit checks (merge/ceil/cross-category/zero-length, week math, trends idempotency, dep-free YAML fallback). Real-data run over `~/Downloads/Building_*.ics` (user-approved high-cost step) — recurrence/`EXDATE`/`UNTIL`/`TZID` all correct; W12 = 10 cognitive h / 8h40m / 5 events; empty week (W24) handled gracefully. Verification wrote to a temp dir only — committed `trends.csv`/`weeks/` untouched.
- Not run: no all-day events exist in this feed, so the all-day path is unit-covered only.

## Blockers / decisions needed (for Claudia — non-blocking; sensible defaults shipped)

- **All-day events**: included at full local-day span (1 all-day event = 24 cognitive hours). Could distort totals. Confirm or change to excluded / configurable.
- **`raw_minutes` definition**: shipped as post-merge union (within-category overlaps not double-counted). Confirm this is the intended meaning of the column.
- **Week-boundary events**: bucketed by start (not clipped). Confirm.
- **Nit for Julius (owns `.gitignore`)**: add `__pycache__/` and `*.pyc` — `Moon/scripts/` generates bytecode at runtime.

## Exact next step

- Julius T-4: build the reflection playbook reading `Moon/weeks/<ISO-week>/events.json` (titles) per the contract above. To run for real: `cp Moon/config/feeds.example.yaml Moon/config/feeds.yaml`, fill the 8 feeds, then `Moon/scripts/moon-weekly`. Deps already installed (`Moon/scripts/requirements.txt`).
