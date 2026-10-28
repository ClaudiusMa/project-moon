#!/usr/bin/env python3
"""Moon Engine A — review-guard guardrail.

Locks the snapshot and re-pull diff behaviour for reviewed weeks. Pure stdlib,
temporary directories only:

    python3 Moon/scripts/test_review_guard.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_guard as rg

CHECKS = []


def check(name, got, want):
    CHECKS.append((name, got, want, got == want))


def ev(uid, cat, title, s, e):
    return {"uid": uid, "category": cat, "title": title, "start_local": s, "end_local": e,
            "duration_min": 60, "all_day": False}


REPORT = """---
week: 2026-W42
---

# Time Report

## Summary

| Identity | Cognitive hours | Share | Raw time | Events |
| --- | ---: | ---: | ---: | ---: |
| I'm a builder | {builder} | 10% | 1h | 1 |
| _Trash time_ | {trash} | 5% | 1h | 1 |
| **Total** | **{total}** | **100%** | **2h** | **2** |

## Event log
"""


def make_week(tmp, reviewed=True, builder=12, trash=0):
    d = Path(tmp) / "2026-W42"
    d.mkdir()
    (d / "events.json").write_text(json.dumps([
        ev("a", "builder", "build", "2026-10-12T10:00:00-07:00", "2026-10-12T11:00:00-07:00"),
        ev("b", "support_self_family", "apply jobs", "2026-10-13T10:00:00-07:00", "2026-10-13T11:00:00-07:00"),
    ]))
    (d / "time-report.md").write_text(REPORT.format(builder=builder, trash=trash, total=builder + trash))
    (d / "signals.md").write_text("# Signals\n")
    if reviewed:
        (d / "reflection.md").write_text("---\nweek: 2026-W42\ndate: 2026-10-20\ntype: reflection\n---\n")
    return d


with tempfile.TemporaryDirectory() as tmp:
    d = make_week(tmp, reviewed=False)
    check("unreviewed week: no snapshot", rg.snapshot_if_reviewed(d), False)
    check("unreviewed week: no snapshot dir", (d / "reviewed").exists(), False)
    check("unreviewed week: no drift report", rg.report_drift("2026-W42", d), [])

with tempfile.TemporaryDirectory() as tmp:
    d = make_week(tmp)
    check("reviewed week: snapshot taken", rg.snapshot_if_reviewed(d), True)
    check("snapshot holds the computed files", sorted(p.name for p in (d / "reviewed").iterdir()),
          ["SNAPSHOT.md", "events.json", "signals.md", "time-report.md"])
    check("snapshot records the reflection date", "reflection_date: 2026-10-20" in (d / "reviewed" / "SNAPSHOT.md").read_text(), True)
    check("second call never re-snapshots", rg.snapshot_if_reviewed(d), False)
    # identical re-pull: nothing to report
    check("identical pull: no warning", rg.report_drift("2026-W42", d), [])
    check("identical pull: no diff file", (d / "repull-diff.md").exists(), False)
    # the calendar changed after the review
    (d / "events.json").write_text(json.dumps([
        ev("a", "builder", "build", "2026-10-12T10:00:00-07:00", "2026-10-12T11:30:00-07:00"),    # end moved
        ev("c", "trash_time", "job apps ✖️", "2026-10-13T15:00:00-07:00", "2026-10-13T17:00:00-07:00"),  # new
    ]))                                                                                        # "b" removed
    (d / "time-report.md").write_text(REPORT.format(builder=9, trash=3, total=12))
    warn = rg.report_drift("2026-W42", d)
    check("drift: warning printed", len(warn), 2)
    check("drift: counts in warning", "1 removed, 1 added, 1 changed" in warn[0], True)
    check("drift: hours in warning", "I'm a builder 12h → 9h; Trash time 0h → 3h" in warn[0], True)
    check("drift: reviewed date in warning", "reviewed on 2026-10-20" in warn[0], True)
    diff = (d / "repull-diff.md").read_text()
    check("diff: frontmatter type", "type: repull-diff" in diff, True)
    check("diff: removed event", "- removed: 2026-10-13 10:00–11:00 support_self_family: apply jobs" in diff, True)
    check("diff: added event", "- added: 2026-10-13 15:00–17:00 trash_time: job apps ✖️" in diff, True)
    check("diff: changed fields named", "- changed (end_local): " in diff, True)
    check("diff: hours table", "| I'm a builder | 12h | 9h |" in diff, True)
    check("snapshot untouched by drift", json.loads((d / "reviewed" / "events.json").read_text())[1]["uid"], "b")
    # the calendar is restored: stale diff is removed
    d.joinpath("events.json").write_text((d / "reviewed" / "events.json").read_text())
    d.joinpath("time-report.md").write_text((d / "reviewed" / "time-report.md").read_text())
    check("restored pull: no warning", rg.report_drift("2026-W42", d), [])
    check("restored pull: stale diff removed", (d / "repull-diff.md").exists(), False)

with tempfile.TemporaryDirectory() as tmp:
    d = make_week(tmp)
    rg.snapshot_if_reviewed(d)
    (d / "time-report.md").write_text(REPORT.format(builder=11, trash=0, total=11))   # rule change, same events
    warn = rg.report_drift("2026-W42", d)
    check("hours moved without event changes still warns", "0 removed, 0 added, 0 changed" in warn[0], True)
    check("diff says so", "_No event-level changes" in (d / "repull-diff.md").read_text(), True)

failed = [c for c in CHECKS if not c[3]]
for name, got, want, ok in CHECKS:
    print(("PASS" if ok else "FAIL") + f" {name} => {got!r}" + ("" if ok else f" (want {want!r})"))
print()
print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} passed" + ("  ✓" if not failed else "  ✗"))
sys.exit(1 if failed else 0)
