# AGENTS

This project uses [HAI-Harness](https://github.com/ClaudiusMa/HAI-Harness), a repo-as-truth collaboration layer for humans and AI agents.

## Where to look

- `Agents/` — the agent operating layer. Shared execution context, role definitions, planner state, task contracts, handoffs, and lessons. **This is your scope.**
- `Human/` — the human workspace (product thinking, decisions, open questions). **Do not read `Human/` unless the user explicitly instructs it.**

## Start here

Before doing anything else, read [`Agents/onboarding.md`](Agents/onboarding.md). It defines:

- the file graph and what each file means,
- the active role you are in (Claudia, Augustus, or Julius) and its required read order,
- the rules of collaboration that you must follow for the rest of the session.

If the user has not told you which role you are in, ask before proceeding.

## Operating rules (summary)

- The repo is the only source of truth. Do not act on chat history or assumed memory.
- One role per chat session. No role switching mid-session.
- Cross-role collaboration happens through `Agents/planning.md`, task docs, and handoff notes — never through chat history.
- Do not move from clarification into implementation planning without an explicit user check-in.
- Do not run high-cost behavior without an explicit user check-in.

The full rules live in [`Agents/onboarding.md`](Agents/onboarding.md). Read it now.

---

# Project Moon — Product Operating Layer

> The sections above govern **how agents collaborate** (the HAI-Harness). This
> section governs **what the product does and how its weekly flow runs**. It is
> intentionally tool-agnostic: any agentic coding tool (Claude Code, Codex, or a
> plain shell + a human) should be able to run Moon from this description alone.
> The deterministic core is Python scripts and markdown playbooks — there is no
> dependency on any single tool.

## What Moon is

Project Moon turns a set of **per-category Google calendars** into a weekly record
of **cognitive hours** — roughly, how much whole-hour attention each part of your
life received — and pairs each week with a short, guided **reflection**. The name
is the intent: watch the trajectory of your weeks the way you'd watch a slow
approach to a landing.

Two ideas keep it honest:

- **Category = the calendar an event lives on.** You keep one Google calendar per
  category and put each event on the right one. Titles are free-form notes for
  *you*; they are never parsed to guess a category. This makes the whole pipeline
  deterministic — no LLM categorization, same input → same numbers.
- **Cognitive hours, not raw minutes.** Within a category, overlapping or adjacent
  events merge into a block, and each block is rounded **up** to whole hours, then
  summed. A 25-minute and a 50-minute Build block that touch become one 2-hour
  Build block. The unit models "this category had my head for ~N hours," not
  stopwatch time.

## The weekly flow

The unit of work is one **ISO week** (Monday–Sunday, in your local timezone, e.g.
`2026-W24`). Each week moves through four steps:

1. **Ingest** — Read one `.ics` feed per category (URLs come from your private
   `Moon/config/feeds.yaml`), expand recurring events, normalize every time to your
   local timezone, and write the week's normalized events to `events.json`.
2. **Compute** — Merge-and-ceil per category to get cognitive hours; write a
   human-readable `time-report.md` and append a row per category to `trends.csv`.
3. **Reflect** — Run the reflection playbook: six questions, asked one at a time,
   lightly proofread, saved to `reflection.md`. The "what did you do this week?"
   answer is auto-drafted from the week's event titles so you start from a recap,
   not a blank page.
4. **Trend** — `trends.csv` accumulates across weeks as the long-term signal.

Steps 1–2 are **Engine A** (deterministic Python, owned by Augustus). Step 3 is
**Engine B** (markdown playbooks, owned by Julius). They talk only through the
fixed data contracts below, so neither needs to know how the other is implemented.

## Where things live

`Moon/` holds the entire product. See [`Moon/README.md`](Moon/README.md) for the
full directory layout and [`Moon/config/categories.md`](Moon/config/categories.md)
for the eight fixed categories.

## Data contracts (the interface between the two engines)

These shapes are fixed. A tool reading or writing Moon data should treat them as
the contract; change them only by updating `Agents/planning.md` first.

- `Moon/weeks/<ISO-week>/events.json` — array of
  `{uid, category, title, start_local, end_local, duration_min}`. Week is Mon–Sun
  in local time.
- `Moon/weeks/<ISO-week>/time-report.md` — per-category cognitive hours plus the
  event log for that week.
- `Moon/weeks/<ISO-week>/reflection.md` — the saved weekly reflection.
- `Moon/trends.csv` — long format, one row per category per week:
  `week_iso, category, cognitive_hours, raw_minutes, event_count`.
- `Moon/config/feeds.yaml` — `category -> ics_feed_url` for the eight categories.
  **Secret and gitignored.** `feeds.example.yaml` is the committed template.

## Operating rules

- **Deterministic core.** No LLM categorization and no tool-specific dependency in
  ingestion or the cognitive-hour math. The same calendars must always produce the
  same numbers, whoever runs them.
- **Reads stay side-effect free.** Inspecting `events.json`, a report, or
  `trends.csv` must never mutate calendar state or rewrite a finished week.
- **Secrets stay out of git.** `feeds.yaml` (real feed URLs) and `Moon/weeks/`
  (your event data and personal reflections) are gitignored. Never commit them.
- **Don't rewrite a finished week.** Re-running a past week should regenerate the
  computed artifacts, but the reflection is a dated personal record — preserve it.

## Running the weekly flow

The flow is meant to run once a week, after a week has closed, in one short
sitting. There are two parts and only the second needs a human:

1. **Compute (unattended).** Run the `moon-weekly` runner (Engine A). It chains
   ingestion → cognitive-hour engine for the **most recent completed week**, writes
   `events.json` and `time-report.md` under `Moon/weeks/<ISO-week>/`, appends rows
   to `Moon/trends.csv`, and prints a one-screen summary. It's deterministic and
   needs no input — same calendars, same numbers. (The runner's exact path and
   flags are defined by the script in `Moon/scripts/`; this section describes the
   contract, not the CLI surface.)
2. **Reflect (interactive).** Open the reflection playbook
   ([`Moon/playbooks/reflection.md`](Moon/playbooks/reflection.md)) and run it with
   an agentic tool, or by hand. It asks six questions one at a time, auto-drafts the
   "what did you do this week?" answer from the week's `events.json`, lightly
   proofreads, and writes `Moon/weeks/<ISO-week>/reflection.md`. This step is
   human-in-the-loop by design.

A normal session is: run `moon-weekly`, glance at the summary and `time-report.md`,
then do the reflection. Any tool that can run a Python script and read a markdown
playbook can drive the whole thing — there's no required assistant.

## Scheduling (optional, portable)

Automation is a **nudge**, not a replacement for the reflection — the reflection
needs a person, so v1 never tries to run it unattended. The portable baseline is
system `cron` (macOS/Linux), which any environment has; richer per-tool schedulers
(a Claude Code routine, a Codex equivalent) are optional adapters layered on top of
the same runner, not a dependency.

A weekly nudge runs the deterministic compute and reminds you to reflect. For
example, every Monday at 9am, run the compute step and notify yourself that the
week is ready to reflect on:

```cron
# Project Moon — weekly compute + reflection nudge (Mondays 9:00, local time)
0 9 * * 1  cd /path/to/project-moon && ./Moon/scripts/moon-weekly && \
  echo "Moon: last week is computed — open Moon/playbooks/reflection.md to reflect."
```

Adapt the path and the notification to your machine (`osascript -e 'display
notification ...'` on macOS, `notify-send` on Linux, an email, etc.). The cron job
only does the unattended compute; you still run the reflection interactively when
you sit down. Keep secrets in `Moon/config/feeds.yaml` (gitignored) so a scheduled
run reads them without anything sensitive landing in the repo or the crontab.
