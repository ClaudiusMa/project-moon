#!/usr/bin/env python3
"""Moon Engine A — review guard.

A week that already has a `reflection.md` was *reviewed*: the person answered the
questions, and a coach advised, against that week's numbers. Google Calendar keeps
moving afterwards (a block gets shortened, deleted, or moved to another identity), so
a later re-pull silently changes the record those notes were written against.

This module keeps that honest, with no change to what the engine computes:

- `snapshot_if_reviewed(week_dir)` — before a re-pull, if the week is reviewed and no
  snapshot exists yet, copy `events.json`, `time-report.md`, `signals.md`, and
  `coverage.json` to `<week>/reviewed/`. Taken once; later pulls never overwrite it,
  so it stays the state the review was based on.
- `report_drift(week_dir)` — after a re-pull of a reviewed week, compare the new
  `events.json` and `time-report.md` with the snapshot, write `repull-diff.md`
  (removed / added / changed events, and identity rows whose hours moved), and
  return the warning lines to print. Removes a stale `repull-diff.md` when nothing
  differs any more.

Pure stdlib. Reads and writes only inside the week's directory.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

SNAPSHOT_DIR = "reviewed"
SNAPSHOT_FILES = ("events.json", "time-report.md", "signals.md", "coverage.json")
DIFF_FILE = "repull-diff.md"


def is_reviewed(week_dir) -> bool:
    return (Path(week_dir) / "reflection.md").exists()


def snapshot_path(week_dir) -> Path:
    return Path(week_dir) / SNAPSHOT_DIR


def snapshot_if_reviewed(week_dir) -> bool:
    """Freeze the reviewed state once. Returns True when a snapshot was taken now."""
    week_dir = Path(week_dir)
    snap = snapshot_path(week_dir)
    if not is_reviewed(week_dir) or snap.exists() or not (week_dir / "events.json").exists():
        return False
    snap.mkdir(parents=True)
    for name in SNAPSHOT_FILES:
        src = week_dir / name
        if src.exists():
            shutil.copy2(src, snap / name)
    (snap / "SNAPSHOT.md").write_text(
        "---\n"
        f"taken: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"reflection_date: {_frontmatter_date(week_dir / 'reflection.md') or 'unknown'}\n"
        "---\n\n"
        "The computed files as they were when this week was reviewed (first re-pull after\n"
        "`reflection.md` existed). Never regenerated. `repull-diff.md` in the week folder\n"
        "compares the current pull against these.\n")
    return True


def _frontmatter_date(path):
    try:
        text = Path(path).read_text()
    except OSError:
        return None
    m = re.search(r"^date:\s*(\S+)", text, re.M)
    return m.group(1) if m else None


def _events_by_uid(path):
    try:
        events = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}
    out = {}
    for e in events:
        key = e.get("uid") or f"{e.get('category')}|{e.get('start_local')}|{e.get('title')}"
        out[key] = e
    return out


def _summary_rows(path):
    """{identity label: cognitive hours} from a time-report's Summary table."""
    try:
        text = Path(path).read_text()
    except OSError:
        return {}
    rows = {}
    in_summary = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_summary = line.strip() == "## Summary"
            continue
        if not in_summary or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("Identity", "---") or cells[0].startswith("---"):
            continue
        label = cells[0].strip("*_ ")
        try:
            rows[label] = int(cells[1].strip("*_ "))
        except ValueError:
            continue
    return rows


def _fmt(e):
    s = e.get("start_local", "")[:16].replace("T", " ")
    en = e.get("end_local", "")[11:16]
    return f"{s}–{en} {e.get('category')}: {e.get('title') or '(untitled)'}"


def compute_drift(week_dir):
    """Compare the current pull with the snapshot. Returns None when there is no
    snapshot, else a dict with removed/added/changed events and hour deltas."""
    week_dir = Path(week_dir)
    snap = snapshot_path(week_dir)
    if not snap.exists():
        return None
    old = _events_by_uid(snap / "events.json")
    new = _events_by_uid(week_dir / "events.json")
    removed = [old[k] for k in old if k not in new]
    added = [new[k] for k in new if k not in old]
    changed = []
    for k in old:
        if k in new:
            a, b = old[k], new[k]
            fields = [f for f in ("category", "title", "start_local", "end_local")
                      if a.get(f) != b.get(f)]
            if fields:
                changed.append((a, b, fields))
    before = _summary_rows(snap / "time-report.md")
    after = _summary_rows(week_dir / "time-report.md")
    hours = [(label, before.get(label), after.get(label))
             for label in list(before) + [l for l in after if l not in before]
             if before.get(label) != after.get(label)]
    return {"removed": removed, "added": added, "changed": changed, "hours": hours,
            "reflection_date": _frontmatter_date(week_dir / "reflection.md"),
            "snapshot_taken": _taken(snap)}


def _taken(snap):
    m = re.search(r"^taken:\s*(\S+)", (snap / "SNAPSHOT.md").read_text(), re.M) if (snap / "SNAPSHOT.md").exists() else None
    return m.group(1) if m else "unknown"


def report_drift(week_key, week_dir):
    """Write `repull-diff.md` for a reviewed week whose pull differs from its snapshot.
    Returns the warning lines to print (empty when nothing drifted)."""
    week_dir = Path(week_dir)
    drift = compute_drift(week_dir)
    diff_path = week_dir / DIFF_FILE
    if drift is None:
        return []
    if not (drift["removed"] or drift["added"] or drift["changed"] or drift["hours"]):
        if diff_path.exists():
            diff_path.unlink()
        return []
    L = ["---", f"week: {week_key}", "type: repull-diff",
         f"reviewed: {drift['reflection_date'] or 'unknown'}",
         f"snapshot_taken: {drift['snapshot_taken']}",
         f"generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
         "---", "", f"# Re-pull diff — {week_key}", "",
         ("_This week was reviewed (its `reflection.md` is dated "
          f"{drift['reflection_date'] or 'unknown'}) and the calendars have changed since. "
          "The reviewed state is frozen in `reviewed/`; the current files reflect today's "
          "calendars. The reflection and any coaching written at review time cite the "
          "reviewed numbers. Coach on the current numbers, and say which ones moved._"), ""]
    if drift["hours"]:
        L += ["## Cognitive hours that moved", "", "| Identity | At review | Now |", "| --- | ---: | ---: |"]
        for label, b, a in drift["hours"]:
            L.append(f"| {label} | {b if b is not None else '—'}h | {a if a is not None else '—'}h |")
        L.append("")
    L += ["## Events", ""]
    for e in drift["removed"]:
        L.append(f"- removed: {_fmt(e)}")
    for e in drift["added"]:
        L.append(f"- added: {_fmt(e)}")
    for a, b, fields in drift["changed"]:
        L.append(f"- changed ({', '.join(fields)}): {_fmt(a)} → {_fmt(b)}")
    if not (drift["removed"] or drift["added"] or drift["changed"]):
        L.append("_No event-level changes; hours moved through a rule or config change._")
    L.append("")
    diff_path.write_text("\n".join(L))
    n = len(drift["removed"]), len(drift["added"]), len(drift["changed"])
    moved = "; ".join(f"{label} {b if b is not None else '—'}h → {a if a is not None else '—'}h"
                      for label, b, a in drift["hours"]) or "no identity totals changed"
    return [f"WARNING: {week_key} was reviewed on {drift['reflection_date'] or 'an unknown date'} "
            f"and its calendars have changed since: {n[0]} removed, {n[1]} added, {n[2]} changed "
            f"event(s); {moved}.",
            f"         See {diff_path} — the reviewed state is kept in {snapshot_path(week_dir)}/"]
