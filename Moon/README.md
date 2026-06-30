# Moon

The product layer of Project Moon: weekly **cognitive-hour** accounting from
per-identity calendars, plus a guided weekly **reflection** and **coaching**. For the
product overview and run flow, see the repo-root [`AGENTS.md`](../AGENTS.md) and
[`README.md`](../README.md).

## Directory layout

```text
project-moon/
├── Moon/                       # the product (shareable, committed)
│   ├── README.md               # this file — layout + how the pieces fit
│   ├── config/
│   │   ├── categories.md       # the 8 identity accounts + the Trash / Invisible buckets
│   │   ├── categories.yaml     # the 8 identities as data: id, display_name, core_question (canonical)
│   │   └── feeds.example.md    # committed template for your feed list
│   ├── scripts/                # Engine A — deterministic Python (ingest + cognitive-hour math + test_engine.py)
│   ├── playbooks/
│   │   ├── reflection.md       # Engine B — the weekly reflection ritual
│   │   └── coaching.md         # Engine B — grounded advice after the reflection
│   ├── weeks/                  # runtime output, one dir per ISO week — gitignored
│   │   └── <ISO-week>/         # e.g. 2026-W24/  (Monday–Sunday, local timezone)
│   │       ├── events.json     # normalized events for the week (Engine A)
│   │       ├── time-report.md  # identities + Trash + Invisible: cognitive hours + % + event log
│   │       ├── reflection.md   # the saved weekly reflection (Engine B)
│   │       └── coaching.md     # the saved weekly coaching note (Engine B)
│   └── trends.csv              # longitudinal record (long format) — gitignored (personal aggregates)
└── Astronaut/                  # YOUR private workspace — gitignored, never committed
    └── rocket.md               # your feed list: identity id -> secret iCal URL / local .ics path
```

> The formats of `events.json`, `time-report.md`, and `trends.csv` are owned by Engine A
> (`scripts/`). Your private feed list lives in `Astronaut/rocket.md` (copy it from
> `config/feeds.example.md`); secret URLs never touch the shareable `Moon/` folder.

## The two engines

- **Engine A — `scripts/` (Python, deterministic).** Reads one `.ics` per identity (plus
  any `trash_time` / `invisible` calendars) from `Astronaut/rocket.md`, expands
  recurrence, normalizes timezones, and produces `events.json`, `time-report.md`, and
  `trends.csv`. It also flags when a Google calendar's name no longer matches
  `categories.yaml` (a rename you may want to mirror). No LLM, no tool-specific
  dependency — same calendars always yield the same numbers. `test_engine.py` locks the math.
- **Engine B — `playbooks/` (markdown rituals).** Human-in-the-loop flows an agentic
  tool reads and follows: `reflection.md` (bare weekly questions, answered from memory)
  then `coaching.md` (grounded advice against the actual schedule; learns from your
  feedback over time).

The engines communicate only through the data contracts (next section).

## Data contracts

Fixed shapes shared between the engines. Change them deliberately, keeping the root
[`AGENTS.md`](../AGENTS.md) in sync.

| Path | Shape |
| --- | --- |
| `config/categories.yaml` | the 8 identities as data: `{id, display_name, core_question}` (canonical, committed) |
| `weeks/<ISO-week>/events.json` | array of `{uid, category, title, start_local, end_local, duration_min, all_day}` (`category` = identity `id`, or `trash_time` / `invisible`) |
| `weeks/<ISO-week>/time-report.md` | all 8 identities (incl 0h) + `Trash time` + `Invisible (unallocated)`: cognitive hours + % of week + event log |
| `weeks/<ISO-week>/reflection.md` | the saved weekly reflection |
| `weeks/<ISO-week>/coaching.md` | the saved weekly coaching note |
| `trends.csv` | long format: `week_iso, category_set_version, category_id, cognitive_hours, raw_minutes, event_count` |
| `Astronaut/rocket.md` | your feed list: `- <id>: <secret iCal URL / .ics path>`, plus `- trash_time:` / `- invisible:` lines |

## Conventions

- **Week key:** ISO week, `YYYY-Www` (e.g. `2026-W24`). A week runs Monday–Sunday
  in your local timezone.
- **Cognitive hours:** within an identity, merge overlapping/adjacent events into a
  block, round each block **up** to whole hours, then sum. Everything counts (no
  minimum-duration floor). A cross-identity overlap counts in both identities.
- **Identity source:** an event's identity is the calendar (feed `id`) it lives on,
  chosen when you scheduled it — never its title. One Google calendar per identity.
  See [`config/categories.md`](config/categories.md).

## What is and isn't committed

- **Committed (the product):** this README, `config/categories.md`,
  `config/categories.yaml`, `config/feeds.example.md`, `scripts/` (incl. `test_engine.py`),
  and `playbooks/` (`reflection.md`, `coaching.md`).
- **Gitignored (your private data):** `Astronaut/` (your `rocket.md` + local calendar
  exports), `weeks/` (events, reflections, coaching), and `trends.csv`. See the repo-root
  `.gitignore`.

## Obsidian

The markdown under `weeks/` (reports, reflections, coaching) is written to be
Obsidian-vault friendly — YAML frontmatter and clean headings — so `Moon/` can sit
inside a vault and be browsed week by week.
