# Engine A — scripts

Deterministic Python: calendars in, cognitive-hour numbers out. Same calendars
always yield the same numbers, with no LLM and no tool-specific dependency. For
the product overview and where this sits, see [`../README.md`](../README.md).

## Files

| File | Role |
| --- | --- |
| `ingest.py` | **M1** — read one `.ics` per category, expand recurrence, normalize to local tz, bucket into a Mon–Sun ISO week → `weeks/<ISO-week>/events.json`. |
| `engine.py` | **M2** — merge per-category, round each block up to whole hours, sum → `weeks/<ISO-week>/time-report.md` + append `trends.csv`. Pure stdlib. |
| `moon-weekly` | **M5** — run ingest → engine for the most recent completed week, print a summary, point to the reflection playbook. |
| `moon_common.py` | Shared paths, category set, tz, ISO-week math, feed-config loading. |
| `requirements.txt` | Ingestion deps (`icalendar`, `recurring-ical-events`, `PyYAML`). |

## Setup

```sh
python3 -m pip install -r requirements.txt   # needed for ingestion only
cp ../config/feeds.example.yaml ../config/feeds.yaml   # then fill in your feeds
```

`feeds.yaml` and `weeks/` are gitignored. The M2 engine needs no dependencies,
so it runs on a hand-written `events.json` even without the install above.

## Usage

```sh
# Most recent completed week, using config/feeds.yaml:
./moon-weekly

# A specific week:
./moon-weekly --week 2026-W24

# One calendar from a local file, no config needed (handy for a first run):
./moon-weekly --ics Build=~/Downloads/cal.ics --timezone America/Los_Angeles

# Run the stages individually:
python3 ingest.py --week 2026-W24
python3 engine.py --week 2026-W24
```

Week keys are ISO `YYYY-Www` (Monday–Sunday, local tz). Without `--week`, the
"most recent completed week" is the last full Mon–Sun that has already ended.

## Conventions worth knowing

- **Category = the feed key**, never the event title or the calendar's internal
  name. Keys must match the 8 fixed categories in
  [`../config/categories.md`](../config/categories.md).
- **Cognitive hours** round each merged block up independently and count
  cross-category overlaps in both categories, so the **Total can exceed
  wall-clock time** — that is intended.
- **All-day events** are included, with a duration equal to their full local-day
  span (a 1-day all-day event = 24h → 24 cognitive hours). Flagged at ingest.
- **`trends.csv`** is upserted per week: re-running a week replaces its rows
  rather than appending duplicates.
- `raw_minutes` in `trends.csv` is the post-merge union of covered time;
  `cognitive_hours` is the rounded-up sum.
