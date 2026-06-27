#!/usr/bin/env python3
"""Moon Engine A — M1 ingestion.

Read one .ics per category (from feeds.yaml or --ics overrides), expand
recurrence (RRULE / EXDATE / RECURRENCE-ID overrides), normalize every time to
the local timezone, bucket into a Mon–Sun ISO week, and emit
`Moon/weeks/<ISO-week>/events.json` per the data contract:

    [{uid, category, title, start_local, end_local, duration_min}, ...]

Recurrence + tz parsing needs `icalendar` and `recurring-ical-events`
(see requirements.txt). Reading/writing is otherwise side-effect free.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import moon_common as mc


def _require_ical():
    try:
        import icalendar  # noqa: F401
        import recurring_ical_events  # noqa: F401
    except ModuleNotFoundError as e:
        req = Path(__file__).resolve().parent / "requirements.txt"
        raise SystemExit(
            f"Missing dependency: {e.name}. Install Engine A deps with:\n"
            f"    python3 -m pip install -r {req}"
        )


def _load_ics_bytes(src: str) -> bytes:
    src = os.path.expanduser(src)
    if urlparse(src).scheme in ("http", "https"):
        with urlopen(src, timeout=30) as r:   # noqa: S310 - feed URLs are user-supplied
            return r.read()
    return Path(src).read_bytes()


def _to_local(value, tz):
    """Normalize an icalendar DTSTART/DTEND value to (aware datetime, all_day)."""
    if isinstance(value, datetime):
        if value.tzinfo is None:              # floating time -> treat as local wall time
            return value.replace(tzinfo=tz), False
        return value.astimezone(tz), False
    # bare date -> all-day, anchored at local midnight
    return datetime(value.year, value.month, value.day, tzinfo=tz), True


def expand_feed(category, src, week_start, week_end, tz):
    """Expand one feed's recurrence within the week window. Returns
    (events, n_all_day). Events are bucketed by local start time."""
    import icalendar
    import recurring_ical_events

    cal = icalendar.Calendar.from_ical(_load_ics_bytes(src))
    occurrences = recurring_ical_events.of(cal).between(week_start, week_end)

    events, n_all_day = [], 0
    for comp in occurrences:
        if getattr(comp, "name", None) != "VEVENT":
            continue
        dtstart = comp.get("DTSTART")
        if dtstart is None:
            continue
        start_local, all_day = _to_local(dtstart.dt, tz)

        dtend = comp.get("DTEND")
        if dtend is not None:
            end_local, _ = _to_local(dtend.dt, tz)
        elif comp.get("DURATION") is not None:
            end_local = start_local + comp.get("DURATION").dt
        else:
            end_local = start_local
        if end_local < start_local:
            end_local = start_local

        # bucket by start within [week_start, week_end)
        if not (week_start <= start_local < week_end):
            continue
        if all_day:
            n_all_day += 1

        duration_min = int(round((end_local - start_local).total_seconds() / 60))
        events.append({
            "uid": str(comp.get("UID", "")),
            "category": category,
            "title": str(comp.get("SUMMARY", "")).strip(),
            "start_local": start_local.isoformat(timespec="seconds"),
            "end_local": end_local.isoformat(timespec="seconds"),
            "duration_min": duration_min,
        })
    return events, n_all_day


def parse_ics_overrides(items):
    out = {}
    for it in items or []:
        if "=" not in it:
            raise SystemExit(f"--ics expects CATEGORY=PATH, got: {it!r}")
        k, v = it.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def run(week_key=None, feeds_path=None, ics_overrides=None, tz_name=None,
        today=None, verbose=True):
    _require_ical()

    # resolve the week
    if week_key:
        year, week = mc.parse_week_key(week_key)
    else:
        _, year, week = mc.most_recent_completed_week(today or date.today())
    week_key = f"{year}-W{week:02d}"

    # build feed map: config file first, then explicit overrides
    feeds, cfg_tz = {}, None
    feeds_path = Path(feeds_path) if feeds_path else mc.DEFAULT_FEEDS
    if feeds_path.exists():
        cfg = mc.load_feeds(feeds_path)
        cfg_tz = cfg.get("timezone")
        feeds.update(cfg.get("feeds", {}))
    feeds.update(ics_overrides or {})
    if not feeds:
        raise SystemExit(
            "No feeds configured. Provide --feeds <path> or --ics CATEGORY=PATH "
            f"(looked for {feeds_path})."
        )

    # timezone: explicit flag > config file > system local
    tz, tz_label = mc.resolve_tz(tz_name or cfg_tz)
    week_start, week_end = mc.week_bounds(year, week, tz)

    if verbose:
        print(f"Week {week_key}  "
              f"[{week_start.date()} .. {(week_end - timedelta(days=1)).date()}]  tz={tz_label}")

    all_events, unknown, total_all_day = [], [], 0
    for category, src in feeds.items():
        if category not in mc.CATEGORY_SET:
            unknown.append(category)
        evs, n_ad = expand_feed(category, src, week_start, week_end, tz)
        total_all_day += n_ad
        all_events.extend(evs)
        if verbose:
            print(f"  {category:<12} {len(evs):>3} events")

    all_events.sort(key=lambda e: (e["start_local"], e["category"], e["uid"]))

    out_dir = mc.WEEKS_DIR / week_key
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "events.json"
    out_path.write_text(json.dumps(all_events, indent=2, ensure_ascii=False) + "\n")

    if verbose:
        print(f"Wrote {len(all_events)} events -> {out_path}")
        if total_all_day:
            print(f"  note: {total_all_day} all-day event(s) included "
                  f"(duration = full local day span).")
        if unknown:
            print(f"  WARNING: feed categories outside the fixed set: {unknown}")
    return out_path, all_events


def main(argv=None):
    ap = argparse.ArgumentParser(description="Moon M1 ingestion: .ics -> weekly events.json")
    ap.add_argument("--week", help="ISO week key, e.g. 2026-W24 (default: most recent completed week)")
    ap.add_argument("--feeds", help=f"feeds.yaml path (default: {mc.DEFAULT_FEEDS})")
    ap.add_argument("--ics", action="append", metavar="CATEGORY=PATH",
                    help="add/override a feed with a local .ics path or URL (repeatable)")
    ap.add_argument("--timezone", help="IANA tz override (default: config, then system local)")
    args = ap.parse_args(argv)
    run(week_key=args.week, feeds_path=args.feeds,
        ics_overrides=parse_ics_overrides(args.ics), tz_name=args.timezone)


if __name__ == "__main__":
    main()
