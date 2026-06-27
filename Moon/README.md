# Moon

The product layer of Project Moon: weekly **cognitive-hour** accounting from
per-category calendars, plus a guided weekly **reflection**. For the product
overview and the run flow, see the *Project Moon — Product Operating Layer*
section in the repo-root [`AGENTS.md`](../AGENTS.md).

## Directory layout

```text
Moon/
├── README.md                 # this file — layout + how the pieces fit
├── config/
│   ├── categories.md         # the 8 fixed categories + one-line descriptions
│   ├── feeds.example.yaml    # committed template: category -> ics_feed_url
│   └── feeds.yaml            # YOUR real secret feed URLs — gitignored, never committed
├── scripts/                  # Engine A — deterministic Python (ingestion + cognitive-hour math)
├── playbooks/
│   └── reflection.md         # Engine B — the 6-question weekly reflection playbook
├── weeks/                    # runtime output, one dir per ISO week — gitignored
│   └── <ISO-week>/           # e.g. 2026-W24/  (Monday–Sunday, local timezone)
│       ├── events.json       # normalized events for the week (Engine A)
│       ├── time-report.md    # per-category cognitive hours + event log (Engine A)
│       └── reflection.md     # the saved weekly reflection (Engine B)
└── trends.csv                # committed longitudinal record (long format)
```

> `scripts/`, `feeds.example.yaml`, and the formats of `events.json`,
> `time-report.md`, and `trends.csv` are built and owned by Engine A. This README
> documents the intended layout; those files appear as that engine is implemented.

## The two engines

- **Engine A — `scripts/` (Python, deterministic).** Reads one `.ics` per category
  from `config/feeds.yaml`, expands recurrence, normalizes timezones, and produces
  `events.json`, `time-report.md`, and `trends.csv`. No LLM, no tool-specific
  dependency — same calendars always yield the same numbers.
- **Engine B — `playbooks/` (markdown rituals).** Human-in-the-loop flows an
  agentic tool reads and follows. The first is `reflection.md`: six questions asked
  one at a time, lightly proofread, saved to the week's `reflection.md`.

The engines communicate only through the data contracts (next section), so they
can be built and run independently.

## Data contracts

Fixed shapes shared between the engines. Change them only by updating
`../Agents/planning.md` first.

| Path | Shape |
| --- | --- |
| `weeks/<ISO-week>/events.json` | array of `{uid, category, title, start_local, end_local, duration_min}` |
| `weeks/<ISO-week>/time-report.md` | per-category cognitive hours + event log |
| `weeks/<ISO-week>/reflection.md` | the saved weekly reflection |
| `trends.csv` | long format: `week_iso, category, cognitive_hours, raw_minutes, event_count` |
| `config/feeds.yaml` | map `category -> ics_feed_url` for the 8 categories |

## Conventions

- **Week key:** ISO week, `YYYY-Www` (e.g. `2026-W24`). A week runs Monday–Sunday
  in your local timezone.
- **Cognitive hours:** within a category, merge overlapping/adjacent events into a
  block, round each block **up** to whole hours, then sum. Everything counts (no
  minimum-duration floor). A cross-category overlap counts in both categories.
- **Category source:** an event's category is the calendar it lives on — never its
  title. One Google calendar per category. See
  [`config/categories.md`](config/categories.md).

## What is and isn't committed

- **Committed:** this README, `config/categories.md`, `config/feeds.example.yaml`,
  `scripts/`, `playbooks/`, and `trends.csv` (the longitudinal record).
- **Gitignored:** `config/feeds.yaml` (secret feed URLs) and `weeks/` (your event
  data and personal reflections). See the repo-root `.gitignore`.

## Obsidian

The markdown under `weeks/` (reports and reflections) is written to be
Obsidian-vault friendly — YAML frontmatter and clean headings — so `Moon/` can sit
inside a vault and be browsed week by week.
