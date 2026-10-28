# Project Moon

Project Moon (登月计划) turns a set of **per-identity Google calendars** into a weekly
record of **cognitive hours** — roughly, how much whole-hour attention each **identity
you're investing in** received — and pairs each week with a short, guided **reflection**
and **coaching**. Each calendar is an identity account, and the report is an honest
mirror of whether your scheduled time funded the person you want to become. The name is
the intent: watch the trajectory of your weeks the way you'd watch a slow approach to a
landing.

This file is the operating guide for **any** agentic coding tool (Claude Code, Codex, or
a plain shell + a human): Moon can be run from this description alone. The deterministic
core is Python scripts and markdown playbooks — there is no dependency on any single tool.

## Three ideas keep it honest

- **Category = an identity account, chosen when you schedule.** Each calendar is one
  identity you're investing in becoming, and putting an event on it is you declaring
  *why* you scheduled the time. The identity is chosen at scheduling time, never inferred
  afterward; titles are free-form notes for *you* and are never parsed. One event lives
  on one calendar, so it funds exactly one identity. This keeps the pipeline
  deterministic — no LLM categorization, same input → same numbers.
- **Cognitive hours, not raw minutes.** Within an identity, overlapping or adjacent
  events merge into a block, and each block is rounded **up** to whole hours, then summed.
  A 25-minute and a 50-minute *builder* block that touch become one 2-hour *builder*
  block. The unit models "this identity had my head for ~N hours," not stopwatch time.
  For the non-identity **Invisible** bucket, calendar time from 12:00 a.m. up to
  7:00 a.m. local is always removed before merge-and-ceil so ordinary sleep does not
  inflate it. The same overnight window is removed from any timed event lasting at least
  24 hours, so a multi-day envelope funds its identity during waking time without
  counting the nights. Outside the Invisible bucket, overnight time is not excluded
  merely because it falls between 12:00 a.m. and 7:00 a.m.: normal timed events shorter
  than 24 hours count in full, so both a 1:00–2:00 a.m. event and a short event that
  crosses midnight still count.
- **The report is a mirror, not a scoreboard.** It shows each identity's share of the
  week as a percentage — every identity in the user's set, even the ones at 0h, so
  neglect stays visible. **The identity set is user-defined in `categories.yaml`; there
  is no fixed list.** Optional non-identity slices help too — the shipped example uses
  **Trash time** (energy-draining time, to *reduce*) and **Invisible (unallocated)**
  (chores / low-return time — fine in small amounts, but don't let it surge). See
  [`Moon/config/categories.md`](Moon/config/categories.md) for the example set, the
  tie-breakers, and how a user makes it their own.

## The weekly flow

The unit of work is one **ISO week** (Monday–Sunday, in your local timezone, e.g.
`2026-W24`). You review the **week that just closed** and plan the **next** one. Each
week moves through five steps:

1. **Ingest** — Read one `.ics` feed per identity (plus any `trash_time` / `invisible`
   calendars) from your private `Astronaut/rocket.md`, expand recurring events, normalize
   every time to your local timezone, and write the week's normalized events to
   `events.json`. Flag any calendar whose Google name no longer matches `categories.yaml`.
2. **Compute** — Merge-and-ceil per category to get cognitive hours; write a
   human-readable `time-report.md` and append a row per category to `trends.csv`.
3. **Signal** — Read the week against the person's own prior weeks and against the
   clock: identity drops and surges versus the trailing median, 0h streaks, Trash
   rises with a time-of-day breakdown, late nights, lost mornings, early long days,
   and what followed what (a 23:00 build → a 07:00–10:00 lost morning). Rules live in
   `config/signals.yaml`; output is `signals.md` + `signals.json`. Facts, no advice.
4. **Reflect** — Run the reflection playbook: first see the exact calculated allocation,
   a factual calendar-title rewind, and the signal flags, then answer the bare questions
   (you review *last week* and plan *this week*), lightly proofread, saved to
   `reflection.md`.
5. **Coach** — Run the coaching playbook as an integrated life and career coach: it
   answers every attention flag with a cause and a decision, grades last week's
   commitments, reads the reflection against `time-report.md` and `events.json`, writes
   grounded advice with checkable commitments to `coaching.md`, and keeps its running
   memory of the person in `Moon/threads.md`.
6. **Trend** — `trends.csv` accumulates across weeks as the long-term signal.

Steps 1–3 are **Engine A** (deterministic Python). Steps 4–5 are **Engine B** (markdown
playbooks). They talk only through the fixed data contracts below.

## Where things live

`Moon/` holds the entire product. See [`Moon/README.md`](Moon/README.md) for the full
directory layout, [`Moon/config/categories.md`](Moon/config/categories.md) for the eight
identities (plus the Trash/Invisible buckets) and how to sort an event, and
[`Moon/config/categories.yaml`](Moon/config/categories.yaml) for the machine-readable
`id → display_name → core_question` (the canonical set the engine reads).

## Data contracts (the interface between the two engines)

These shapes are fixed. A tool reading or writing Moon data should treat them as the
contract; change them deliberately and keep this file and `Moon/README.md` in sync. The
current set is `category_set_version: identity_v1`, a breaking change from the original
activity categories — there is no auto-migration (a clean start).

- `Moon/config/categories.yaml` — the canonical category set: a list of
  `{id, display_name, core_question}` for the user's identities (the example ships eight).
  Committed. The engine reads ids and display names from here; [`categories.md`](Moon/config/categories.md) is
  the human constitution that must stay in sync.
- `Moon/weeks/<ISO-week>/events.json` — array of
  `{uid, category, title, start_local, end_local, duration_min, all_day}`, where
  `category` is the identity **id** the event's feed maps to, or `trash_time` /
  `invisible` for a non-identity calendar. Week is Mon–Sun in local time.
- `Moon/weeks/<ISO-week>/time-report.md` — frontmatter carries
  `category_set_version: identity_v1`; the summary lists **every** identity in the set
  (even at 0h) with `display_name`, cognitive hours, and **share %**, plus **Trash time** and
  **Invisible (unallocated)** slices. Share is each row's percentage of the week's total
  cognitive hours (identities + Trash + Invisible). Invisible segments in the local
  `[00:00, 07:00)` window are excluded from its calculation but remain in `events.json`.
  Timed events lasting at least 24 hours also exclude that window on every covered date;
  their original interval remains in `events.json`, and each still counts as one source
  event. Followed by the event log.
- `Moon/config/signals.yaml` — the signal rules: thresholds (drop/surge ratios, streak
  length, late-night and lost-morning definitions), the focus identities that need deep
  blocks, title markers (🍅, ✖️), and the title lexicons that point a reader at events
  worth reading. Committed; user-editable; defaults are built in.
- `Moon/weeks/<ISO-week>/signals.md` + `signals.json` — Engine A's observations for the
  week: `flags` (`severity` attention/notice, `kind`, `category`, `title`, `evidence`),
  `week_over_week` (hours, previous recorded week, trailing median, 0h streak, blocks,
  longest block), `days` (per local day: first identity event, last event end, identity
  / Trash / Invisible minutes, late night, lost mornings, early long days),
  `sequences`, `trash` breakdown, `markers`, and `carry` (last week's plan, commitments,
  open threads). Never alters events, reports, or trends. Regenerated on every run.
- `Moon/weeks/<ISO-week>/reflection.md` — the saved weekly reflection.
- `Moon/weeks/<ISO-week>/coaching.md` — the saved weekly coaching note. Its
  **Commitments for this week** items carry `calendar:` and `done:` so the next week's
  signals can list them for grading.
- `Moon/threads.md` — the coach's running memory: **Open** (questions, hypotheses,
  watches) and **Closed** threads, one dated bullet each. Gitignored; written only by the
  coaching playbook; its Open bullets are copied into each week's `signals.md`.
- `Moon/trends.csv` — long format, one row per category per week:
  `week_iso, category_set_version, category_id, cognitive_hours, raw_minutes, event_count`.
- `Astronaut/expected-calendars.json` — private expected source counts by category ID,
  including enabled optional calendars. No URLs; changes require deliberate confirmation.
- `Moon/weeks/<ISO-week>/coverage.json` — private evidence of successful retrieval,
  per-source event counts, and fingerprints of the source configuration, category set,
  events and report. Checked before review; does not change events/trends schemas.
- `Astronaut/rocket.md` — your private feed list: bullet lines `- <id>: <secret iCal URL
  or local .ics path>` for the eight identity ids, plus optional `- trash_time: <…>`,
  `- invisible: <…>`, and `- timezone: <IANA>` lines. Lives in the gitignored
  `Astronaut/` workspace; `Moon/config/feeds.example.md` is the committed template.
  (A legacy `Moon/config/feeds.yaml` is still accepted.)

## Operating rules

- **Deterministic core.** No LLM categorization and no tool-specific dependency in
  ingestion or the cognitive-hour math. An event's identity comes from the feed it's on —
  chosen at scheduling time — never from parsing its title, so the same calendars always
  produce the same numbers, whoever runs them.
- **Numbers come only from the engine.** Cognitive hours, percentages, Trash, and
  Invisible are computed by `Moon/scripts/` and locked by `Moon/scripts/test_engine.py`.
  An agent must run the scripts and report their output verbatim — never compute,
  estimate, round, or "correct" the math by hand. The engine also owns the Invisible
  sleep-window and multi-day overnight exclusions; an agent must never add those hours
  back mentally.
- **Flags come only from the signals stage; answers come only from the coach.**
  `signals.py` (locked by `test_signals.py`) decides what changed and what the schedule
  shape was; an agent shows its flags verbatim in the rewind and never invents or drops
  one. The coaching playbook must answer every attention flag with a cause and a
  decision and grade every carried commitment. Title lexicons and markers are pointers
  for a reader; they never assign a category or change a number.
- **Verify complete source coverage before a review.** Run `./Moon/scripts/moon-weekly
  --week <ISO-week>` and then the same command with `--check-coverage` before showing
  the allocation or starting reflection/coaching. Missing sources or failed retrieval
  must stop the review; never interpret them as 0h. Expected source IDs/counts live in
  private `Astronaut/expected-calendars.json`, registered deliberately with
  `moon-weekly --confirm-sources` only after the user confirms the complete calendar
  list, including any Trash/Invisible sources. Never auto-confirm to bypass an error.
  Successful pulls save private `coverage.json`, tied to the events, report, and source
  configuration. Standalone fixture calculations are labelled unverified.
- **Surface calendar changes every pull.** Ingestion compares each Google calendar's own
  name (`X-WR-CALNAME`) to the identity's `display_name`; if they diverge (you renamed a
  calendar), it warns. Mirror an intended rename by editing `display_name` in
  `categories.yaml` — the `id` stays the same, so there's no data migration.
- **Reads stay side-effect free.** Inspecting `events.json`, a report, or `trends.csv`
  must never mutate calendar state or rewrite a finished week.
- **Secrets stay out of git.** The `Astronaut/` workspace (your `rocket.md` + any local
  calendar exports), `Moon/weeks/` (events, reflections, coaching), and `Moon/trends.csv`
  (per-identity weekly aggregates) are gitignored. Never commit them.
- **Don't rewrite a finished week.** Re-running a past week should regenerate the
  computed artifacts, but the reflection and coaching are dated personal records —
  preserve them.

## Running the weekly flow

The flow is meant to run once a week, after a week has closed, in one short sitting.
Compute is unattended; reflection and coaching need a person.

1. **Compute (unattended).** Run the `moon-weekly` runner (Engine A). It chains ingestion
   → cognitive-hour engine → signals for the **most recent completed week**, writes
   `events.json` and `time-report.md` under `Moon/weeks/<ISO-week>/`, appends rows to
   `Moon/trends.csv`, then writes `signals.md` + `signals.json`, prints a one-screen
   summary with the week's flags, and flags any calendar rename. Deterministic — same
   calendars, same numbers, same flags. (`python3 Moon/scripts/signals.py --week
   <ISO-week>` regenerates the signals alone.)
2. **Reflect, then coach (interactive).** Open the reflection playbook
   ([`Moon/playbooks/reflection.md`](Moon/playbooks/reflection.md)): it shows Engine A's
   exact time-by-identity table and a concise factual schedule rewind **before** asking
   the bare questions, then lightly proofreads the answers and writes `reflection.md`.
   The coaching playbook ([`Moon/playbooks/coaching.md`](Moon/playbooks/coaching.md))
   reads it against the actual schedule and writes grounded advice to `coaching.md`.

Any tool that can run a Python script and read a markdown playbook can drive the whole
thing — there's no required assistant.

## Scheduling (optional, portable)

Automation is a **nudge**, not a replacement for the reflection — it needs a person, so
Moon never tries to run it unattended. The portable baseline is system `cron`
(macOS/Linux); richer per-tool schedulers (a Claude Code routine, a Codex equivalent) are
optional adapters on top of the same runner, not a dependency.

```cron
# Project Moon — weekly compute + reflection nudge (Mondays 9:00, local time)
0 9 * * 1  cd /path/to/project-moon && ./Moon/scripts/moon-weekly && \
  echo "Moon: last week is computed — open Moon/playbooks/reflection.md to reflect."
```

Adapt the path and notification to your machine (`osascript -e 'display notification ...'`
on macOS, `notify-send` on Linux, an email, etc.). The cron job only does the unattended
compute; you still reflect and coach interactively. Your feeds live in
`Astronaut/rocket.md` (gitignored), so a scheduled run reads them without anything
sensitive landing in the repo or the crontab.


## Development workflow activation

Use Moon's scripts and playbooks directly for everyday tasks. Load HAI-Harness
only when the user explicitly invokes **Claudia** (case-insensitive) in the current
request. References to the name in quoted material or historical context do not
activate it. Once invoked, follow [the separate HAI instructions](.hai/AGENTS.md).
Do not load `.hai/` or start harness roles, update checks, worktrees, delegation,
or task packets for an ordinary Moon request.

HAI lives entirely in `.hai/`. Run its CLI commands from the product root with
`--target .hai`, including installation, updates, doctor, and worktree commands;
never target the product root for a harness installation or update. Moon's runtime
paths stay rooted in this product workspace.

## Calendar notation context

- 2026-10-27 — ✖️ on a title means **planned but not done**: the block was scheduled
  for that task and the task did not happen (e.g. *"job apps and paper ✖️"*). It is
  the person's own verdict, written after the fact. `signals.md` lists these events;
  the coach reads them as the clearest evidence of plan-versus-reality and asks what
  got in the way, never as a character judgment. The category still comes from the
  calendar the event sits on.
- 2026-10-06 — 🍅 means Pomodoro timer sessions — **focus time**, confirmed again
  2026-10-27. A number alongside it (such as
  `🍅 2`, `🍅 x 2`, or `3 🍅`) records how many sessions ran. The user regards these
  as highly productive focus time and values more sessions. Use this meaning in
  factual rewinds and reflection/coaching context; it does not change category
  assignment or Engine A cognitive-hour calculations. Do not invent a session
  count when none is specified.
