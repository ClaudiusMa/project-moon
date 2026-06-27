#!/usr/bin/env python3
"""Moon Engine A — M2 cognitive-hour engine.

Consume `Moon/weeks/<ISO-week>/events.json`. Per category: merge
overlapping/adjacent events into blocks, round each block UP to whole hours,
then sum. Everything counts (no minimum-duration floor); cross-category
overlaps count in both categories because merging is per-category.

Writes `time-report.md` (Obsidian-friendly) and upserts the week's rows into
`Moon/trends.csv` (long format). Pure stdlib — no external dependencies.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import moon_common as mc

TRENDS_HEADER = ["week_iso", "category", "cognitive_hours", "raw_minutes", "event_count"]


def compute_category(events):
    """For one category's events, merge into blocks and accumulate hours.

    Returns (cognitive_hours, raw_minutes). `raw_minutes` is the union of time
    covered (post-merge, so within-category overlap is not double counted);
    `cognitive_hours` is the sum of each block rounded up to whole hours."""
    intervals = sorted(
        (datetime.fromisoformat(e["start_local"]), datetime.fromisoformat(e["end_local"]))
        for e in events
    )
    blocks = []
    for s, e in intervals:
        if blocks and s <= blocks[-1][1]:            # overlapping or touching
            if e > blocks[-1][1]:
                blocks[-1] = (blocks[-1][0], e)
        else:
            blocks.append((s, e))

    cognitive_hours, raw_minutes = 0, 0.0
    for s, e in blocks:
        minutes = (e - s).total_seconds() / 60.0
        raw_minutes += minutes
        if minutes > 0:
            cognitive_hours += math.ceil(minutes / 60.0)
    return cognitive_hours, int(round(raw_minutes))


def _ordered_categories(by_cat):
    """Fixed set first (stable order), then any unexpected categories present."""
    out = [c for c in mc.CATEGORIES if c in by_cat]
    out += sorted(c for c in by_cat if c not in mc.CATEGORY_SET)
    return out


def render_report(week_key, year, week, rows, by_cat) -> str:
    monday = date.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)
    total_ch = sum(r[1] for r in rows)
    total_rm = sum(r[2] for r in rows)
    total_ev = sum(r[3] for r in rows)

    L = [
        "---",
        f"week: {week_key}",
        f"start: {monday.isoformat()}",
        f"end: {sunday.isoformat()}",
        f"cognitive_hours: {total_ch}",
        "generator: moon engine-a",
        "---",
        "",
        f"# Time Report — {week_key}",
        "",
        f"_{monday.strftime('%a %b %d')} – {sunday.strftime('%a %b %d, %Y')} · local timezone_",
        "",
        ("Cognitive hours: within each category, overlapping/adjacent events are merged "
         "into blocks, each block is rounded **up** to whole hours, then summed. Everything "
         "counts (no minimum-duration floor); a cross-category overlap counts in both."),
        "",
        "## Summary",
        "",
        "| Category | Cognitive hours | Raw time | Events |",
        "| --- | ---: | ---: | ---: |",
    ]
    for cat, ch, rm, n in rows:
        L.append(f"| {cat} | {ch} | {mc.fmt_hm(rm)} | {n} |")
    L.append(f"| **Total** | **{total_ch}** | **{mc.fmt_hm(total_rm)}** | **{total_ev}** |")
    L += [
        "",
        ("> Total cognitive hours can exceed wall-clock time: cross-category overlaps are "
         "counted in every category they touch, and each block rounds up independently."),
        "",
        "## Event log",
    ]
    if not rows:
        L += ["", "_No events this week._", ""]
        return "\n".join(L)

    for cat, ch, _rm, _n in rows:
        L += ["", f"### {cat} — {ch} h", ""]
        for e in sorted(by_cat[cat], key=lambda x: x["start_local"]):
            s = datetime.fromisoformat(e["start_local"])
            en = datetime.fromisoformat(e["end_local"])
            title = e["title"] or "(untitled)"
            L.append(f"- {s.strftime('%a %m/%d %H:%M')}–{en.strftime('%H:%M')}  "
                     f"{title}  ({e['duration_min']}m)")
    L.append("")
    return "\n".join(L)


def update_trends(week_key, rows):
    """Upsert this week's rows: drop any existing rows for the week, add the new
    ones, and rewrite in a deterministic order (idempotent across reruns)."""
    path = mc.TRENDS_CSV
    kept = []
    if path.exists():
        with path.open(newline="") as f:
            reader = csv.reader(f)
            next(reader, None)  # header
            kept = [r for r in reader if r and r[0] != week_key]
    for cat, ch, rm, n in rows:
        kept.append([week_key, cat, str(ch), str(rm), str(n)])
    kept.sort(key=lambda r: (
        r[0],
        mc.CATEGORIES.index(r[1]) if r[1] in mc.CATEGORY_SET else len(mc.CATEGORIES),
        r[1],
    ))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(TRENDS_HEADER)
        w.writerows(kept)


def run(week_key=None, today=None, verbose=True):
    if week_key:
        year, week = mc.parse_week_key(week_key)
    else:
        _, year, week = mc.most_recent_completed_week(today or date.today())
    week_key = f"{year}-W{week:02d}"

    week_dir = mc.WEEKS_DIR / week_key
    events_path = week_dir / "events.json"
    if not events_path.exists():
        raise SystemExit(f"No events.json for {week_key} at {events_path}. Run ingest first.")
    events = json.loads(events_path.read_text())

    by_cat = {}
    for e in events:
        by_cat.setdefault(e["category"], []).append(e)

    rows = []  # (category, cognitive_hours, raw_minutes, event_count)
    for cat in _ordered_categories(by_cat):
        ch, rm = compute_category(by_cat[cat])
        rows.append((cat, ch, rm, len(by_cat[cat])))

    report_path = week_dir / "time-report.md"
    report_path.write_text(render_report(week_key, year, week, rows, by_cat))
    update_trends(week_key, rows)

    if verbose:
        total_ch = sum(r[1] for r in rows)
        print(f"Week {week_key}: {total_ch} cognitive hours across {len(rows)} categories")
        for cat, ch, rm, n in rows:
            print(f"  {cat:<12} {ch:>3} h   (raw {mc.fmt_hm(rm)}, {n} events)")
        print(f"Wrote {report_path}")
        print(f"Updated {mc.TRENDS_CSV}")
    return report_path, rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Moon M2 engine: events.json -> time-report.md + trends.csv")
    ap.add_argument("--week", help="ISO week key, e.g. 2026-W24 (default: most recent completed week)")
    args = ap.parse_args(argv)
    run(week_key=args.week)


if __name__ == "__main__":
    main()
