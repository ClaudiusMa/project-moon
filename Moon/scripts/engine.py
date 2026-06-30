#!/usr/bin/env python3
"""Moon Engine A — M2 cognitive-hour engine.

Consume `Moon/weeks/<ISO-week>/events.json`. Per identity (category id): merge
overlapping/adjacent events into blocks, round each block UP to whole hours,
then sum. Everything counts (no minimum-duration floor); cross-category
overlaps count in both identities because merging is per-category. All-day
events are handled per `moon_common.ALL_DAY_POLICY`.

The report lists all eight identities (including those at 0 hours) plus an
"Invisible (unallocated)" slice for time on non-identity calendars, so the week
reads as an honest mirror. Percentages are share of the week's total cognitive
hours (identities + invisible). Writes `time-report.md` (Obsidian-friendly) and
upserts the week's rows into `Moon/trends.csv`. Pure stdlib.
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

TRENDS_HEADER = [
    "week_iso", "category_set_version", "category_id",
    "cognitive_hours", "raw_minutes", "event_count",
]


def _counted(events):
    """The events that count toward cognitive hours, per the all-day policy.
    All-day events stay in events.json regardless; this only filters counting."""
    if mc.ALL_DAY_POLICY == "exclude":
        return [e for e in events if not e.get("all_day")]
    return events


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


def _daily_sanity_warnings(counted_by_cat, cats):
    """Guardrail: within ONE category, a single local day cannot legitimately
    exceed 24 cognitive hours. Exceeding it signals a bad event time / parse bug,
    so warn rather than silently trust the number."""
    warns = []
    for cat, evs in counted_by_cat.items():
        per_day = {}
        for e in evs:
            per_day.setdefault(e["start_local"][:10], []).append(e)
        for d, dayevs in per_day.items():
            ch, _ = compute_category(dayevs)
            if ch > mc.MAX_COGNITIVE_HOURS_PER_DAY:
                warns.append(f"{cats.name(cat)} on {d}: {ch} cognitive hours "
                             f"(> {mc.MAX_COGNITIVE_HOURS_PER_DAY}) — check for a bad event time")
    return warns


def _pct(part, total) -> int:
    return round(100 * part / total) if total else 0


def render_report(week_key, year, week, id_rows, extra_rows, counted_by_cat, cats, n_excluded) -> str:
    monday = date.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)
    rows = id_rows + extra_rows
    total_ch = sum(r[1] for r in rows)
    total_rm = sum(r[2] for r in rows)
    total_ev = sum(r[3] for r in rows)

    L = [
        "---",
        f"week: {week_key}",
        f"start: {monday.isoformat()}",
        f"end: {sunday.isoformat()}",
        f"category_set_version: {cats.version}",
        f"cognitive_hours: {total_ch}",
        "generator: moon engine-a",
        "---",
        "",
        f"# Time Report — {week_key}",
        "",
        f"_{monday.strftime('%a %b %d')} – {sunday.strftime('%a %b %d, %Y')} · local timezone_",
        "",
        ("Cognitive hours: within each identity, overlapping/adjacent events are merged "
         "into blocks, each block is rounded **up** to whole hours, then summed. Everything "
         "counts (no minimum-duration floor); a cross-category overlap counts in both. "
         "**Share** is each row's percentage of the week's total cognitive hours, including "
         "the **Invisible** slice — time on calendars that aren't an identity (your "
         "primary/Trash calendars). All eight identities are listed even at 0h, so an "
         "underfunded identity stays visible."),
        "",
        "## Summary",
        "",
        "| Identity | Cognitive hours | Share | Raw time | Events |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for cat, ch, rm, n in id_rows:
        L.append(f"| {cats.name(cat)} | {ch} | {_pct(ch, total_ch)}% | {mc.fmt_hm(rm)} | {n} |")
    for cat, ch, rm, n in extra_rows:        # invisible / unexpected, italicized
        L.append(f"| _{cats.name(cat)}_ | {ch} | {_pct(ch, total_ch)}% | {mc.fmt_hm(rm)} | {n} |")
    total_share = "100%" if total_ch else "—"
    L.append(f"| **Total** | **{total_ch}** | **{total_share}** | "
             f"**{mc.fmt_hm(total_rm)}** | **{total_ev}** |")
    L += [
        "",
        ("> Total cognitive hours can exceed wall-clock time: cross-category overlaps are "
         "counted in every identity they touch, and each block rounds up independently."),
    ]
    if n_excluded:
        L += [
            "",
            (f"> {n_excluded} all-day event(s) are recorded in `events.json` but excluded "
             f"from cognitive hours (`ALL_DAY_POLICY=exclude`). Change the policy in "
             f"`moon_common.py` to count them."),
        ]

    # Event log — only rows that actually have events
    L += ["", "## Event log"]
    logged = [(c, ch) for c, ch, _r, n in rows if n]
    if not logged:
        L += ["", "_No events this week._", ""]
        return "\n".join(L)
    for cat, ch in logged:
        L += ["", f"### {cats.name(cat)} — {ch} h", ""]
        for e in sorted(counted_by_cat.get(cat, []), key=lambda x: x["start_local"]):
            s = datetime.fromisoformat(e["start_local"])
            en = datetime.fromisoformat(e["end_local"])
            title = e["title"] or "(untitled)"
            L.append(f"- {s.strftime('%a %m/%d %H:%M')}–{en.strftime('%H:%M')}  "
                     f"{title}  ({e['duration_min']}m)")
    L.append("")
    return "\n".join(L)


def update_trends(week_key, rows, version, cats):
    """Upsert this week's rows: drop any existing rows for the week, add the new
    ones, and rewrite in a deterministic order (idempotent across reruns).

    If trends.csv exists with an incompatible (pre-identity_v1) header, preserve
    it once as a `.bak` and start a clean file — the identity set is a breaking
    change with no lossless mapping."""
    path = mc.TRENDS_CSV
    kept = []
    if path.exists():
        with path.open(newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header == TRENDS_HEADER:
                kept = [r for r in reader if r and r[0] != week_key]
            else:
                backup = path.parent / (path.name + ".pre-identity_v1.bak")
                if not backup.exists():
                    path.replace(backup)
                    print(f"  note: existing {path.name} used an older schema; "
                          f"preserved as {backup.name} and started fresh.")
    for cat, ch, rm, n in rows:
        kept.append([week_key, version, cat, str(ch), str(rm), str(n)])
    kept.sort(key=lambda r: (r[0], cats.order(r[2]), r[2]))   # week, identity order, id
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(TRENDS_HEADER)
        w.writerows(kept)


def run(week_key=None, today=None, verbose=True):
    cats = mc.get_categories()
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

    counted_by_cat, n_excluded = {}, 0

    # all eight identities in canonical order, including zero-hour ones
    id_rows = []
    for cat in cats.ids:
        evs = by_cat.get(cat, [])
        counted = _counted(evs)
        n_excluded += len(evs) - len(counted)
        counted_by_cat[cat] = counted
        ch, rm = compute_category(counted) if counted else (0, 0)
        id_rows.append((cat, ch, rm, len(counted)))

    # diagnostic / non-identity rows. Trash time is always shown (even 0h) so it's
    # confronted in reflection; invisible and any stragglers show only when present.
    extra_rows = []
    specials = [c for c in mc.SPECIAL_BUCKETS if c in by_cat or c == mc.TRASH_ID]
    others = sorted(c for c in by_cat if c not in cats and c not in mc.SPECIAL_BUCKETS)
    for cat in specials + others:
        evs = by_cat.get(cat, [])
        counted = _counted(evs)
        n_excluded += len(evs) - len(counted)
        if not counted and cat != mc.TRASH_ID:
            continue
        counted_by_cat[cat] = counted
        ch, rm = compute_category(counted) if counted else (0, 0)
        extra_rows.append((cat, ch, rm, len(counted)))

    rows = id_rows + extra_rows

    report_path = week_dir / "time-report.md"
    report_path.write_text(render_report(week_key, year, week, id_rows, extra_rows,
                                          counted_by_cat, cats, n_excluded))
    update_trends(week_key, rows, cats.version, cats)

    if verbose:
        total_ch = sum(r[1] for r in rows)
        print(f"Week {week_key}: {total_ch} cognitive hours  (set {cats.version})")
        for cat, ch, rm, n in rows:
            label = cats.name(cat)
            print(f"  {ch:>3} h  {_pct(ch, total_ch):>3}%  {label}  ({n} ev, raw {mc.fmt_hm(rm)})")
        if n_excluded:
            print(f"  ({n_excluded} all-day event(s) excluded from cognitive hours)")
        for w in _daily_sanity_warnings(counted_by_cat, cats):
            print(f"  WARNING: {w}")
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
