# Engine A — scripts

Deterministic Python: calendars in, cognitive-hour numbers out. Same calendars
always yield the same numbers, with no LLM and no tool-specific dependency. For
the product overview and where this sits, see [`../README.md`](../README.md).

## Files

| File | Role |
| --- | --- |
| `ingest.py` | **M1** — read one `.ics` per category, expand recurrence, normalize to local tz, bucket into a Mon–Sun ISO week → `weeks/<ISO-week>/events.json`. |
| `engine.py` | **M2** — merge per-identity, round each block up to whole hours, sum → `weeks/<ISO-week>/time-report.md` (display names + % of week) + upsert `trends.csv`. Pure stdlib. |
| `signals.py` | **M3** — read the week against prior weeks and the clock → `weeks/<ISO-week>/signals.md` + `signals.json`: identity drops/surges vs the trailing median, 0h streaks, Trash rises by time of day, late nights, lost mornings, early long days, cross-day sequences, deep blocks, 🍅/✖️ markers, title-lexicon pointers, and last week's plan + commitments to grade. Rules in `../config/signals.yaml`. Pure stdlib. |
| `review_guard.py` | **M4** — for a week that already has a `reflection.md`: freeze its computed files in `weeks/<ISO-week>/reviewed/` before the first re-pull, then write `repull-diff.md` and warn when a later pull differs. Pure stdlib. |
| `moon-weekly` | **M5** — run review guard → ingest → engine → signals for the most recent completed week, print a summary with the flags (and a re-pull warning if a reviewed week changed), point to the reflection + coaching playbooks. |
| `test_engine.py` | Guardrail — locks the cognitive-hour math and feed parsing (`python3 test_engine.py`). |
| `test_signals.py` | Guardrail — locks the signal rules (`python3 test_signals.py`). |
| `test_review_guard.py` | Guardrail — locks the snapshot/diff behaviour (`python3 test_review_guard.py`). |
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
python3 signals.py --week 2026-W24     # needs events.json; uses trends.csv for history
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
- **Invisible sleep-window time** from 12:00 a.m. up to 7:00 a.m. local is excluded
  before Invisible's merge-and-ceil calculation, and the original Invisible events
  remain in `events.json`. Cross-boundary events are clipped (for example, 6:00–8:00
  a.m. contributes 7:00–8:00 a.m.).
- **Multi-day timed-event nights** are also excluded: when a timed event lasts at least
  24 hours, its local 12:00 a.m.–7:00 a.m. windows are removed before merge-and-ceil.
  The original event remains unchanged in `events.json` and counts once; only its
  calculation segments are split. Short events that cross midnight count in full.
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
- **Signals compare against recorded weeks only.** The baseline is the last
  `baseline_weeks` rows in `trends.csv` before the target week; gaps are named, never
  interpolated. Shape flags (late nights, lost mornings) are *attention* only when the
  count is both above the threshold and above the person's own median over prior weeks
  whose `events.json` is still on disk. A "lost morning" is a Trash/Invisible block of
  90m+ starting 06:00–10:00; a "late night" is any event ending at/after 23:00; an
  "early long day" is an event starting at/before 07:00 lasting 5h+. Lexicon hits point
  at titles; they never categorize.
- **Baselines are only as comparable as the sources.** When a Trash or Invisible
  calendar is added, removed, or redefined, the medians straddle that change for
  `baseline_weeks` weeks. Nothing detects this; note it in `threads.md` as a watch.
- **Carried commitments** come from the previous week's newest coaching file
  (`coaching.md` or `coaching-revised*.md`, by frontmatter `date:`). Open threads are
  copied from `threads.md` as it is *now*, so re-running an old week's signals shows
  current threads, not the threads of that time.
