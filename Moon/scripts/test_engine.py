#!/usr/bin/env python3
"""Moon Engine A — calculation guardrail.

Locks the cognitive-hour math and feed parsing so a future edit can't silently
change the numbers. Pure stdlib — run it directly, no pytest needed:

    python3 Moon/scripts/test_engine.py

Exits non-zero if any check fails. This is the guardrail: the numbers come from
this deterministic code, never from an agent's mental arithmetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine
import moon_common as mc

CHECKS = []


def check(name, got, want):
    CHECKS.append((name, got, want, got == want))


def ev(s, e, all_day=False):
    return {"start_local": s, "end_local": e, "all_day": all_day}


def full_ev(uid, category, title, s, e, duration_min):
    return {
        "uid": uid,
        "category": category,
        "title": title,
        "start_local": s,
        "end_local": e,
        "duration_min": duration_min,
        "all_day": False,
    }


def ch(events):
    return engine.compute_category(events)[0]


def rm(events):
    return engine.compute_category(events)[1]


# --- cognitive-hour math ----------------------------------------------------
check("45m -> 1h", ch([ev("2026-06-22T09:00:00", "2026-06-22T09:45:00")]), 1)
check("60m -> 1h", ch([ev("2026-06-22T09:00:00", "2026-06-22T10:00:00")]), 1)
check("61m -> 2h (ceil)", ch([ev("2026-06-22T09:00:00", "2026-06-22T10:01:00")]), 2)
check("5m -> 1h (no floor)", ch([ev("2026-06-22T09:00:00", "2026-06-22T09:05:00")]), 1)
check("overlap merges -> 2h",
      ch([ev("2026-06-22T09:00:00", "2026-06-22T10:00:00"),
          ev("2026-06-22T09:30:00", "2026-06-22T10:30:00")]), 2)
check("adjacent touch merges -> 2h",
      ch([ev("2026-06-22T09:00:00", "2026-06-22T10:00:00"),
          ev("2026-06-22T10:00:00", "2026-06-22T11:00:00")]), 2)
check("two 15m with a gap -> 2h (each ceils)",
      ch([ev("2026-06-22T09:00:00", "2026-06-22T09:15:00"),
          ev("2026-06-22T10:00:00", "2026-06-22T10:15:00")]), 2)
check("cross-midnight 22:00-00:30 -> 3h",
      ch([ev("2026-06-22T22:00:00", "2026-06-23T00:30:00")]), 3)
check("raw_minutes = post-merge union (90)",
      rm([ev("2026-06-22T09:00:00", "2026-06-22T10:00:00"),
          ev("2026-06-22T09:30:00", "2026-06-22T10:30:00")]), 90)

# --- all-day policy ---------------------------------------------------------
_evset = [ev("2026-06-22T09:00:00", "2026-06-22T10:00:00"),
          ev("2026-06-26T00:00:00", "2026-06-27T00:00:00", all_day=True)]
check(f"all-day excluded (policy={mc.ALL_DAY_POLICY})", len(engine._counted(_evset)), 1)

# --- Invisible sleep-window policy -----------------------------------------
_night = [ev("2026-06-22T01:00:00", "2026-06-22T06:00:00")]
_segments, _source_count, _all_day, _removed, _multi_day_removed = \
    engine._prepare_category_events(_night, mc.INVISIBLE_ID)
check("Invisible 01:00-06:00 excluded", len(_segments), 0)
check("Invisible fully excluded source event count", _source_count, 0)
check("Invisible fully excluded minutes", _removed, 300)

_cross_7 = [ev("2026-06-22T06:00:00", "2026-06-22T08:00:00")]
_segments, _source_count, _all_day, _removed, _multi_day_removed = \
    engine._prepare_category_events(_cross_7, mc.INVISIBLE_ID)
check("Invisible 06:00-08:00 keeps one segment", len(_segments), 1)
check("Invisible 06:00-08:00 starts counting at 07:00",
      _segments[0]["start_local"], "2026-06-22T07:00:00")
check("Invisible 06:00-08:00 removes 60m", _removed, 60)
check("Invisible 06:00-08:00 computes 1h", ch(_segments), 1)

_cross_midnight = [ev("2026-06-22T23:00:00", "2026-06-23T08:00:00")]
_segments, _source_count, _all_day, _removed, _multi_day_removed = \
    engine._prepare_category_events(_cross_midnight, mc.INVISIBLE_ID)
check("Invisible 23:00-08:00 splits around sleep", len(_segments), 2)
check("Invisible split does not inflate event count", _source_count, 1)
check("Invisible 23:00-08:00 removes 7h", _removed, 420)
check("Invisible 23:00-08:00 keeps 2 raw hours", rm(_segments), 120)
check("Invisible 23:00-08:00 computes 2h", ch(_segments), 2)

_overlapping_sleep = [
    ev("2026-06-22T01:00:00", "2026-06-22T04:00:00"),
    ev("2026-06-22T02:00:00", "2026-06-22T05:00:00"),
]
_segments, _source_count, _all_day, _removed, _multi_day_removed = \
    engine._prepare_category_events(_overlapping_sleep, mc.INVISIBLE_ID)
check("overlapping Invisible sleep exclusion uses union minutes", _removed, 240)

_identity_segments, _source_count, _all_day, _removed, _multi_day_removed = \
    engine._prepare_category_events(_night, "builder")
check("identity time inside 00:00-07:00 still counts", ch(_identity_segments), 5)
check("identity sleep-window minutes not removed", _removed, 0)

_one_am_identity_event = [
    ev("2026-06-22T01:00:00", "2026-06-22T02:00:00")
]
_segments, _source_count, _all_day, _removed, _multi_day_removed = \
    engine._prepare_category_events(_one_am_identity_event, "builder")
check("short identity event at 01:00-02:00 counts in full", ch(_segments), 1)
check("short identity event at 01:00-02:00 removes no time", _multi_day_removed, 0)

# --- Multi-day timed-event overnight policy --------------------------------
_stella = [
    ev("2026-07-24T18:00:00-07:00", "2026-07-26T15:45:00-07:00")
]
_segments, _source_count, _all_day, _invisible_removed, _multi_day_removed = \
    engine._prepare_category_events(_stella, "loyal_friend")
check("multi-day event splits into waking-day segments", len(_segments), 3)
check("multi-day split does not inflate event count", _source_count, 1)
check("multi-day event removes two seven-hour nights", _multi_day_removed, 840)
check("multi-day event keeps 31h45m raw time", rm(_segments), 1905)
check("multi-day event computes 32 cognitive hours", ch(_segments), 32)

_short_overnight = [
    ev("2026-07-24T20:00:00-07:00", "2026-07-25T04:00:00-07:00")
]
_segments, _source_count, _all_day, _invisible_removed, _multi_day_removed = \
    engine._prepare_category_events(_short_overnight, "loyal_friend")
check("short overnight event remains one segment", len(_segments), 1)
check("short overnight event keeps full duration", rm(_segments), 480)
check("short overnight event removes no time", _multi_day_removed, 0)

_exact_day = [
    ev("2026-07-24T18:00:00-07:00", "2026-07-25T18:00:00-07:00")
]
_segments, _source_count, _all_day, _invisible_removed, _multi_day_removed = \
    engine._prepare_category_events(_exact_day, "loyal_friend")
check("24h timed envelope activates multi-day rule", _multi_day_removed, 420)
check("24h timed envelope keeps 17h", rm(_segments), 1020)

# --- feed markdown parsing --------------------------------------------------
_md = """# feeds
- timezone: America/Los_Angeles
- builder: https://calendar.google.com/calendar/ical/abc/private-xyz/basic.ics
- grateful_son: <paste secret iCal URL>
- invisible: /tmp/primary.ics
- invisible: /tmp/trash.ics
prose line, ignored
"""
_cfg = mc._parse_feeds_md(_md)
check("feeds.md timezone", _cfg["timezone"], "America/Los_Angeles")
check("feeds.md keeps filled identity", _cfg["feeds"].get("builder", "").endswith("basic.ics"), True)
check("feeds.md skips placeholder", "grateful_son" in _cfg["feeds"], False)
check("feeds.md collects multiple invisible", len(_cfg["invisible"]), 2)
check("feeds.md URL keeps scheme", _cfg["feeds"]["builder"].startswith("https://"), True)

# --- isolated engine integration (writes only to a temporary directory) ----
with tempfile.TemporaryDirectory(prefix="moon-engine-test-") as _tmp:
    _tmp_path = Path(_tmp)
    _old_weeks_dir, _old_trends_csv = mc.WEEKS_DIR, mc.TRENDS_CSV
    try:
        mc.WEEKS_DIR = _tmp_path / "weeks"
        mc.TRENDS_CSV = _tmp_path / "trends.csv"
        _week_dir = mc.WEEKS_DIR / "2026-W26"
        _week_dir.mkdir(parents=True)
        _source_events = [
            full_ev("night", mc.INVISIBLE_ID, "sleep", "2026-06-22T01:00:00",
                    "2026-06-22T06:00:00", 300),
            full_ev("cross", mc.INVISIBLE_ID, "early task", "2026-06-22T06:00:00",
                    "2026-06-22T08:00:00", 120),
            full_ev("builder", "builder", "night build", "2026-06-22T01:00:00",
                    "2026-06-22T02:00:00", 60),
        ]
        _source_json = json.dumps(_source_events, indent=2)
        _events_path = _week_dir / "events.json"
        _events_path.write_text(_source_json)
        _report_path, _rows = engine.run(week_key="2026-W26", verbose=False)
        _invisible_row = next(r for r in _rows if r[0] == mc.INVISIBLE_ID)
        _trash_row = next(r for r in _rows if r[0] == mc.TRASH_ID)
        _report = _report_path.read_text()
        check("engine Invisible row applies sleep window", _invisible_row, (mc.INVISIBLE_ID, 1, 60, 1))
        check("engine always emits zero Trash row", _trash_row, (mc.TRASH_ID, 0, 0, 0))
        check("engine report names sleep-window rule", "12:00 a.m.–7:00 a.m." in _report, True)
        check("engine leaves source events.json untouched", _events_path.read_text() == _source_json, True)
        check("engine writes identity + both diagnostic trend rows",
              len(mc.TRENDS_CSV.read_text().splitlines()), len(mc.get_categories().ids) + 3)
    finally:
        mc.WEEKS_DIR, mc.TRENDS_CSV = _old_weeks_dir, _old_trends_csv

# --- report ----------------------------------------------------------------
print()
for name, got, want, ok in CHECKS:
    print(("PASS" if ok else "FAIL"), f"{name} => {got!r} (want {want!r})")
failed = [c for c in CHECKS if not c[3]]
print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} passed" + ("" if failed else "  ✓"))
sys.exit(1 if failed else 0)
