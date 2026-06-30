# Engine A — scripts

Deterministic Python: calendars in, cognitive-hour numbers out. Same calendars
always yield the same numbers, with no LLM and no tool-specific dependency. For
the product overview and where this sits, see [`../README.md`](../README.md).

## Files

| File | Role |
| --- | --- |
| `ingest.py` | **M1** — read one `.ics` per category, expand recurrence, normalize to local tz, bucket into a Mon–Sun ISO week → `weeks/<ISO-week>/events.json`. |
| `engine.py` | **M2** — merge per-identity, round each block up to whole hours, sum → `weeks/<ISO-week>/time-report.md` (display names + % of week) + upsert `trends.csv`. Pure stdlib. |
| `moon-weekly` | **M5** — run ingest → engine for the most recent completed week, print a summary, point to the reflection + coaching playbooks. |
| `test_engine.py` | Guardrail — locks the cognitive-hour math and feed parsing (`python3 test_engine.py`). |
| `moon_common.py` | Shared paths, the identity set loader (`../config/categories.yaml`), the all-day policy, tz, ISO-week math, feed-config loading. |
| `requirements.txt` | Ingestion deps (`icalendar`, `recurring-ical-events`, `PyYAML`). |

## Setup

```sh
python3 -m pip install -r requirements.txt   # needed for ingestion only
mkdir -p ../../Astronaut && cp ../config/feeds.example.md ../../Astronaut/rocket.md   # then fill in your feeds
```

Your feed list (`Astronaut/rocket.md`) and `weeks/` are gitignored. The M2 engine needs no dependencies,
so it runs on a hand-written `events.json` even without the install above.

## Usage

```sh
# Most recent completed week, using Astronaut/rocket.md:
./moon-weekly

# A specific week:
./moon-weekly --week 2026-W24

# One calendar from a local file, no config needed (handy for a first run):
# (the key is an identity id from categories.yaml)
./moon-weekly --ics builder=~/Downloads/cal.ics --timezone America/Los_Angeles

# Run the stages individually:
python3 ingest.py --week 2026-W24
python3 engine.py --week 2026-W24
```

Week keys are ISO `YYYY-Www` (Monday–Sunday, local tz). Without `--week`, the
"most recent completed week" is the last full Mon–Sun that has already ended.

## Conventions worth knowing

- **Category = the feed key**, never the event title or the calendar's internal
  name. Keys are **identity ids** and must match an `id` in
  [`../config/categories.yaml`](../config/categories.yaml); reports render the
  `display_name`. See [`../config/categories.md`](../config/categories.md) for what
  each identity means.
- **Cognitive hours** round each merged block up independently and count
  cross-category overlaps in both identities, so the **Total can exceed
  wall-clock time** — that is intended.
- **All-day events** are recorded in `events.json` (with `all_day: true`) but, by
  default, **excluded from cognitive hours** so a single all-day event can't swamp a
  week. Flip `ALL_DAY_POLICY` in `moon_common.py` to `"include"` to count them at
  their full local-day span instead.
- **`trends.csv`** is long format, version-stamped, and upserted per week
  (re-running a week replaces its rows rather than appending duplicates). Columns:
  `week_iso, category_set_version, category_id, cognitive_hours, raw_minutes,
  event_count`.
- `raw_minutes` in `trends.csv` is the post-merge union of covered time;
  `cognitive_hours` is the rounded-up sum. Both reflect only counted events
  (all-day events excluded under the default policy).
