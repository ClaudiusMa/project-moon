## Product Planning

<!--
## How To Use This File

- Claudia owns this file.
- Keep backlog, active focus, current strategy, worker assignments, and user decisions here.
- Replace placeholders with real project state.
- Do not use this file as a worker journal.
-->

Planner-owned single source of truth for the current iteration.

Last updated: 2026-06-15 11:10 PT
Last updated by: Claudia
User check-in before implementation: yes
High-cost execution approved: yes — Augustus ran the real pipeline over the sample `.ics` (approved in his session)

Status options: `inbox`, `ready`, `next`, `in progress`, `blocked`, `done`, `dropped`.
Type options: `feature`, `bug`, `chore`, `design`, `experiment`.
Priority options: `P0` (must now), `P1` (soon), `P2` (nice), `P3` (maybe).

### 1. Inbox (untriaged)

- None. All current items are triaged into the Backlog.

### 2. Backlog

| ID | Title | Type | Priority | Status | Owner | Notes / Links |
| --- | --- | --- | --- | --- | --- | --- |
| T-1 | M0 — Skeleton & conventions | chore | P0 | done | Julius | `Moon/` layout, product section in `AGENTS.md`, `categories.md`, `.gitignore` for secrets |
| T-2 | M1 — Calendar ingestion | feature | P0 | done | Augustus | per-category `.ics` → recurrence + tz normalize → weekly `events.json`; verified vs real `Building` export |
| T-3 | M2 — Cognitive-hour engine | feature | P0 | done | Augustus | merge-within-category → ceil → `time-report.md` + `trends.csv` |
| T-4 | M4 — Reflection playbook | feature | P1 | done | Julius | 6-question ritual, proofread, write `reflection.md`; auto-draft from titles. Verified synthetically only |
| T-5 | M5 — Weekly glue + nudge | feature | P1 | done | Augustus + Julius | `moon-weekly` runner (Augustus) + run docs / portable cron (Julius) |

### 3. Now (active focus)

- **[x]** Augustus: T-2 → T-3 → T-5 runner — done, verified vs real `Building` export
- **[x]** Julius: T-1 → T-4 → T-5 run docs — done (T-4 verified synthetically)
- **[ ]** Remaining: run the reflection playbook against a real `events.json` once a real week is generated (T-4 cross-check)
- **[ ]** Remaining: Claudia to resolve Augustus's three engine defaults (see 3c)
- **[ ]** Blocker: none

### 3a. Current Iteration Strategy

- Goal: ship Project Moon v1 — weekly cognitive-hour time accounting from per-category calendars plus a guided weekly reflection ritual, runnable by any agentic coding tool.
- Why now:
  - Reason: design is clarified end-to-end and a real `.ics` export is in hand to build and verify against.
  - Reason: removing LLM categorization (category = source calendar) makes Engine A fully deterministic and cheap to ship.
- Context gathered:
  - Fact: category = the calendar an event lives on (one Google calendar per category; confirmed by `X-WR-CALNAME:Building`). Titles are free-form and are NOT used for categorization.
  - Fact: feeds mix UTC (`...Z`) and `TZID=America/Los_Angeles`; recurrence uses `RRULE` + `EXDATE` + `RECURRENCE-ID` overrides, so ingestion needs a recurrence-aware iCal parser.
  - Fact: cognitive hours = per category, merge overlapping/adjacent events into blocks, ceil each block to whole hours, sum. Count everything (no minimum-duration floor). Cross-category overlaps count in both categories for v1.
  - Fact: tool-agnostic — deterministic Python scripts + markdown playbooks anchored on `AGENTS.md`; no Claude-Code-only dependency in the core.
  - Fact: storage is local markdown under `Moon/`, Obsidian-friendly; secret feed URLs are gitignored.
- Architectural decision:
  - Decision: split into Engine A (deterministic scripts) and Engine B (markdown playbooks) with fixed data contracts between them so the two workers can build in parallel.
  - Constraint: no LLM categorization; reproducible numeric output independent of the running tool.
  - Out of scope (v1): Notion, event color, OAuth / Google Cloud project, work calendar, fully unattended reflection.
- Data contracts (fixed interface — both workers code against these):
  - `Moon/weeks/<ISO-week>/events.json`: array of `{uid, category, title, start_local, end_local, duration_min}`. Week = Mon–Sun in local tz.
  - `Moon/weeks/<ISO-week>/time-report.md`: per-category cognitive hours + the event log.
  - `Moon/trends.csv`: long format — `week_iso, category, cognitive_hours, raw_minutes, event_count`.
  - `Moon/config/feeds.yaml` (gitignored; `feeds.example.yaml` committed): map `category -> ics_feed_url` for the 8 categories.
  - Categories (fixed set): Learn, Build, Career, Habit, Workout, Social, Exploration, Trash.
- Worker split:
  - Augustus: Engine A. Write scope `Moon/scripts/**`, `Moon/config/feeds.example.yaml`. Owns `events.json`, `time-report.md`, `trends.csv` formats.
  - Julius: conventions + Engine B. Write scope `AGENTS.md` (product section), `Moon/README.md`, `Moon/config/categories.md`, `Moon/playbooks/**`, `.gitignore`. Consumes Augustus's data contracts read-only.
- Risks / ambiguity:
  - Risk: recurrence edge cases (overrides, cancellations, DST boundary) — verify against the sample `.ics` before trusting totals.
  - Risk: cross-category overlap rule and the no-floor rule may distort totals; both flagged revisitable after week 1.

### 3b. Implementation Steps

Assigned queue for Augustus:

1. T-2 / M1 — Ingestion. Build `Moon/scripts/` to read one `.ics` per category (paths from `feeds.yaml`), expand recurrence with a recurrence-aware library, normalize all times to local tz, bucket into a Mon–Sun week, and emit `events.json` per the contract. Tag each event with its category from the feed map.
2. T-3 / M2 — Cognitive-hour engine. Consume `events.json`; per category merge overlapping/adjacent events into blocks, ceil each block to whole hours, sum; render `time-report.md` and append `trends.csv` rows.
3. T-5 / M5 — `moon-weekly` runner script that chains ingestion → engine for the most recent completed week and prints a summary; hand off to the reflection playbook.

Assigned queue for Julius:

1. T-1 / M0 — Create the `Moon/` skeleton and conventions: a product operating section in `AGENTS.md` (how any tool runs the weekly flow), `Moon/README.md` (layout), `Moon/config/categories.md` (the 8 categories + one-line descriptions), and `.gitignore` entries for `Moon/config/feeds.yaml` and `Moon/weeks/`.
2. T-4 / M4 — Reflection playbook in `Moon/playbooks/`: ask the 6 questions one at a time, proofread each answer (fix typos/grammar only, never change meaning), and write `Moon/weeks/<ISO-week>/reflection.md`. Auto-draft the "What did you do this week?" answer from that week's `events.json` titles (read-only).
3. T-5 / M5 — Document the weekly run (session + optional system-cron nudge) in `AGENTS.md`; describe the portable scheduling adapter, not a Claude-Code-only one.

Advancement rule:

- Continue directly to the next queued task after the current one is done.
- Pause only for a blocking user decision, an overlapping write-scope conflict, or unapproved high-cost behavior.

Verification rule:

- Low-cost by default: run scripts over the sample `.ics` (the user's `Building` export) and inspect output.
- High-cost (needs explicit approval before running): installing Python dependencies and executing the full pipeline.

### 3c. Decision needed from user

- Engine default (Augustus flagged): all-day events count at full local-day span, so 1 all-day event = 24 cognitive hours. Confirm, exclude, or make configurable.
- Engine default (Augustus flagged): `raw_minutes` in `trends.csv` = post-merge union (within-category overlaps not double-counted). Confirm this is the intended meaning.
- Engine default (Augustus flagged): events crossing a week boundary are bucketed by start time, not clipped. Confirm.
- Cleanup (Julius scope, `.gitignore`): add `__pycache__/` and `*.pyc` — `Moon/scripts/` generates bytecode at runtime.
- Scope nudge: OK for Claudia to populate the currently-blank `Agents/project_context.md` (and the human-owned `Human/brief.md`) so worker sessions inherit shared context? These are outside Claudia's default write scope, so confirming first.

### 4. Bugs list (optional detail)

| Bug ID | Title | Severity | Status | Repro steps | Notes |
| --- | --- | --- | --- | --- | --- |
| - | None yet | - | - | - | - |

### 5. Feature ideas / roadmap (optional detail)

- **Idea**: Keep event color via a Google Apps Script export — **Why**: richer signal without OAuth — **Rough scope**: M — **Notes**: deferred from v1.
- **Idea**: Include the work calendar — **Why**: fuller week picture — **Rough scope**: S.
- **Idea**: Longitudinal charts from `trends.csv` — **Why**: see the "moon landing" trajectory — **Rough scope**: M.
- **Idea**: Per-tool scheduling adapters (Claude routine, Codex equivalent) — **Why**: nicer automation per tool — **Rough scope**: S–M.
- **Idea**: Obsidian-native niceties (wikilinks/dataview) over the markdown output — **Why**: better in-vault browsing — **Rough scope**: S.
