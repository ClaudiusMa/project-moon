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
3. **Reflect** — Run the reflection playbook: bare questions answered from memory (you
   review *last week* and plan *next week*), lightly proofread, saved to `reflection.md`.
4. **Coach** — Run the coaching playbook: it reads the reflection against the week's
   `time-report.md` and `events.json` and writes grounded advice to `coaching.md`.
5. **Trend** — `trends.csv` accumulates across weeks as the long-term signal.

Steps 1–2 are **Engine A** (deterministic Python). Steps 3–4 are **Engine B** (markdown
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
  cognitive hours (identities + Trash + Invisible). Followed by the event log.
- `Moon/weeks/<ISO-week>/reflection.md` — the saved weekly reflection.
- `Moon/weeks/<ISO-week>/coaching.md` — the saved weekly coaching note.
- `Moon/trends.csv` — long format, one row per category per week:
  `week_iso, category_set_version, category_id, cognitive_hours, raw_minutes, event_count`.
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
  estimate, round, or "correct" the math by hand.
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
   → cognitive-hour engine for the **most recent completed week**, writes `events.json`
   and `time-report.md` under `Moon/weeks/<ISO-week>/`, appends rows to `Moon/trends.csv`,
   prints a one-screen summary, and flags any calendar rename. Deterministic — same
   calendars, same numbers.
2. **Reflect, then coach (interactive).** Open the reflection playbook
   ([`Moon/playbooks/reflection.md`](Moon/playbooks/reflection.md)): bare questions
   answered from memory, lightly proofread, written to `reflection.md`. Then the coaching
   playbook ([`Moon/playbooks/coaching.md`](Moon/playbooks/coaching.md)) reads it against
   the actual schedule and writes grounded advice to `coaching.md`.

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
