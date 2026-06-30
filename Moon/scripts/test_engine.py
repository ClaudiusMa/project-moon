#!/usr/bin/env python3
"""Moon Engine A — calculation guardrail.

Locks the cognitive-hour math and feed parsing so a future edit can't silently
change the numbers. Pure stdlib — run it directly, no pytest needed:

    python3 Moon/scripts/test_engine.py

Exits non-zero if any check fails. This is the guardrail: the numbers come from
this deterministic code, never from an agent's mental arithmetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine
import moon_common as mc

CHECKS = []


def check(name, got, want):
    CHECKS.append((name, got, want, got == want))


def ev(s, e, all_day=False):
    return {"start_local": s, "end_local": e, "all_day": all_day}


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

# --- report ----------------------------------------------------------------
print()
for name, got, want, ok in CHECKS:
    print(("PASS" if ok else "FAIL"), f"{name} => {got!r} (want {want!r})")
failed = [c for c in CHECKS if not c[3]]
print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} passed" + ("" if failed else "  ✓"))
sys.exit(1 if failed else 0)
