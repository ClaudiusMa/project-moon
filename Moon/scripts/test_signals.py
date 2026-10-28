#!/usr/bin/env python3
"""Moon Engine A — signals guardrail.

Locks the signal rules (week-over-week flags, schedule shape, sequences, trash
breakdown, markers, carry-ins) so an edit can't silently change what gets
flagged. Pure stdlib — run it directly:

    python3 Moon/scripts/test_signals.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import moon_common as mc
import signals as sg

CHECKS = []


def check(name, got, want):
    CHECKS.append((name, got, want, got == want))


def ev(cat, title, s, e):
    start, end = sg._dt(s), sg._dt(e)
    return {"uid": f"{cat}-{s}", "category": cat, "title": title,
            "start_local": s, "end_local": e,
            "duration_min": int((end - start).total_seconds() // 60), "all_day": False}


CATS = mc.get_categories()
CFG = sg.load_config(Path("/nonexistent"))          # defaults only, independent of the yaml
CFG["lexicons"] = {"sleep_disruption": ["sleep", "wake", "late", "get up"],
                   "screen_drift": ["bilibili", "game", "waste time"]}
kinds = lambda flags: [f["kind"] for f in flags]
sev = lambda flags, kind: next(f["severity"] for f in flags if f["kind"] == kind)

# --- config parser ------------------------------------------------------------
yaml_text = '''version: signals_v1
focus_identities: [builder, designer_taste]   # trailing comment
thresholds:
  baseline_weeks: 6
  drop_ratio: 0.5
  late_night_end: "23:00"
markers:
  focus_session: "🍅"
lexicons:
  sleep: [sleep, "get up", late]
'''
parsed = sg._parse_signals_yaml(yaml_text)
check("yaml: version scalar", parsed["version"], "signals_v1")
check("yaml: inline list", parsed["focus_identities"], ["builder", "designer_taste"])
check("yaml: nested int", parsed["thresholds"]["baseline_weeks"], 6)
check("yaml: nested float", parsed["thresholds"]["drop_ratio"], 0.5)
check("yaml: quoted time stays a string", parsed["thresholds"]["late_night_end"], "23:00")
check("yaml: emoji marker", parsed["markers"]["focus_session"], "🍅")
check("yaml: quoted phrase in list", parsed["lexicons"]["sleep"], ["sleep", "get up", "late"])
check("config: defaults survive a missing file", sg.load_config(Path("/nonexistent"))["thresholds"]["drop_min_hours"], 4)

# --- markers and lexicons ------------------------------------------------------
check("🍅 2", sg.focus_sessions("portfolio 🍅 2", "🍅"), (2, True))
check("🍅 x 2", sg.focus_sessions("portfolio 🍅 x 2", "🍅"), (2, True))
check("3 🍅", sg.focus_sessions("portfolio 3 🍅", "🍅"), (3, True))
check("4x 🍅", sg.focus_sessions("design 4x 🍅", "🍅"), (4, True))
check("bare 🍅 -> unspecified, never invented", sg.focus_sessions("portfolio 🍅", "🍅"), (None, True))
check("no 🍅", sg.focus_sessions("portfolio", "🍅"), (0, False))
check("lexicon: whole word", sg._lexicon_hits("woke up late", CFG["lexicons"]), {"sleep_disruption": ["late"]})
check("lexicon: 'late' does not match 'later'", sg._lexicon_hits("see you later", CFG["lexicons"]), {})
check("lexicon: phrase substring", sg._lexicon_hits("couldnt get up", CFG["lexicons"]), {"sleep_disruption": ["get up"]})
check("lexicon: case-insensitive", sg._lexicon_hits("Bilibili again", CFG["lexicons"]), {"screen_drift": ["bilibili"]})

# --- week over week --------------------------------------------------------------
W = ["2026-W20", "2026-W21", "2026-W22", "2026-W23", "2026-W24", "2026-W25"]
trends = {w: {"builder": 16, "designer_taste": 4, "grateful_son": 0, "trash_time": 0, "invisible": 10,
              "support_self_family": 8} for w in W}
trends["2026-W23"]["grateful_son"] = 2                      # breaks the zero streak at W23
this = {"builder": 2, "designer_taste": 14, "grateful_son": 0, "trash_time": 5, "invisible": 30,
        "support_self_family": 7}
rows, flags, base = sg.week_over_week(CATS, trends, "2026-W26", this, CFG)
check("baseline = last 6 recorded weeks", base, W)
check("builder 16 -> 2 is a drop", sev(flags, "identity_drop"), sg.ATTENTION)
check("drop names builder", [f["category"] for f in flags if f["kind"] == "identity_drop"], ["builder"])
check("designer 4 -> 14 is a surge notice", [f["category"] for f in flags if f["kind"] == "identity_surge"], ["designer_taste"])
check("trash 0 -> 5 rises", "trash_rise" in kinds(flags), True)
check("invisible 10 -> 30 surges", "invisible_surge" in kinds(flags), True)
check("ssf 8 -> 7 is nothing", any(f["category"] == "support_self_family" for f in flags), False)
gs = next(r for r in rows if r["category"] == "grateful_son")
check("zero streak counts consecutive recorded 0h weeks incl. this one", gs["zero_streak"], 3)
check("3-week zero streak flags", any(f["kind"] == "zero_streak" and f["category"] == "grateful_son" for f in flags), True)
check("zero streak since the right week", next(f["evidence"][0] for f in flags if f["kind"] == "zero_streak" and f["category"] == "grateful_son"), "0h every recorded week since 2026-W24.")
check("a category never recorded in trends has no streak", next(r["zero_streak"] for r in rows if r["category"] == "superman"), 1)
rows1, flags1, _ = sg.week_over_week(CATS, {"2026-W25": {"builder": 12}}, "2026-W26", {"builder": 3}, CFG)
check("one prior week: compare to it directly", "identity_drop" in kinds(flags1), True)
rows0, flags0, base0 = sg.week_over_week(CATS, {}, "2026-W26", {"builder": 3}, CFG)
check("no history: no flags, no baseline", (flags0, base0), ([], []))
check("prior weeks ignore later weeks", sg.prior_weeks({"2026-W30": {}, "2026-W25": {}}, "2026-W26", 6), ["2026-W25"])
check("gap note names missing weeks", sg._gap_note(["2026-W33", "2026-W37"], "2026-W38"), " Not recorded: 2026-W34, 2026-W35, 2026-W36.")
check("gap note silent when contiguous", sg._gap_note(["2026-W36", "2026-W37"], "2026-W38"), "")

# --- schedule shape and sequences -----------------------------------------------------
# Week 2026-W42: Mon 10/12 .. Sun 10/18
events = [
    ev("superman", "ride bike", "2026-10-12T21:00:00-07:00", "2026-10-12T23:15:00-07:00"),      # Mon late
    ev("trash_time", "couldnt get up", "2026-10-13T07:45:00-07:00", "2026-10-13T11:00:00-07:00"),  # Tue lost morning
    ev("builder", "build", "2026-10-13T13:00:00-07:00", "2026-10-13T14:00:00-07:00"),
    ev("builder", "build", "2026-10-14T20:00:00-07:00", "2026-10-14T23:00:00-07:00"),         # Wed ends exactly 23:00 -> late
    ev("invisible", "sleep", "2026-10-15T08:00:00-07:00", "2026-10-15T09:00:00-07:00"),         # Thu 60m: too short to be lost
    ev("trash_time", "bilibili", "2026-10-16T23:30:00-07:00", "2026-10-17T00:15:00-07:00"),    # Fri crosses midnight, drift
    ev("superman", "hang gliding", "2026-10-18T06:00:00-07:00", "2026-10-18T14:55:00-07:00"),   # Sun early long day
    ev("loyal_friend", "trip", "2026-10-16T18:00:00-07:00", "2026-10-18T12:00:00-07:00"),       # multi-day envelope
]
days, seqs, sflags, counts = sg.day_shape(CATS, events, "2026-W42", CFG)
check("seven day rows", [d["dow"] for d in days], ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
check("Mon is a late night (23:15)", days[0]["late_night"], True)
check("Wed ending exactly 23:00 is late", days[2]["late_night"], True)
check("Fri crossing midnight is late", days[4]["late_night"], True)
check("Fri last end shows next-day marker", days[4]["last_end"], "00:15 (+1)")
check("Tue lost morning detected", len(days[1]["lost_mornings"]), 1)
check("Thu 60m block is not a lost morning", days[3]["lost_mornings"], [])
check("identity-calendar mornings are never 'lost'", days[6]["lost_mornings"], [])
check("Sun early long day", len(days[6]["early_long_days"]), 1)
check("first identity event on Tue skips the trash block", days[1]["first_identity_start"], "13:00")
check("multi-day envelope stays out of the day table", days[5]["events"], 0)
check("counts", counts, {"late_nights": 3, "lost_mornings": 1, "early_long_days": 1})
check("late night -> lost morning sequence", [s["kind"] for s in seqs if s["kind"] == "late_night_then_lost_morning"], ["late_night_then_lost_morning"])
check("sequence names both days", (seqs[0]["day"], seqs[0]["next_day"]), ("2026-10-12", "2026-10-13"))
check("late-night drift detected", any(s["kind"] == "late_night_drift" for s in seqs), True)
check("early long day -> next day is only reported when a next day exists", any(s["kind"] == "early_long_day_then_next_day" for s in seqs), False)
check("chained flag: 1 of 1 lost mornings followed a late night", sev(sflags, "late_then_lost_morning"), sg.ATTENTION)
check("3 late nights with no history = attention", sev(sflags, "late_nights"), sg.ATTENTION)
hist = [{"late_nights": 4, "lost_mornings": 0}, {"late_nights": 5, "lost_mornings": 0}]
_, _, sflags_rel, _ = sg.day_shape(CATS, events, "2026-W42", CFG, history=hist)
check("3 late nights below the person's median = notice", sev(sflags_rel, "late_nights"), sg.NOTICE)
# previous Sunday feeds Monday's sequence
prev = [ev("trash_time", "game", "2026-10-11T22:00:00-07:00", "2026-10-12T01:00:00-07:00")]
mon_lost = [ev("trash_time", "late", "2026-10-12T07:00:00-07:00", "2026-10-12T10:00:00-07:00")]
_, seqs2, _, _ = sg.day_shape(CATS, mon_lost, "2026-W42", CFG, prev_week_events=prev)
check("previous week's Sunday late night chains into Monday", [(s["kind"], s["day"]) for s in seqs2], [("late_night_then_lost_morning", "2026-10-11")])
# early long day -> next day
early = [ev("superman", "hang gliding", "2026-10-17T06:00:00-07:00", "2026-10-17T14:00:00-07:00"),
         ev("builder", "build", "2026-10-18T11:00:00-07:00", "2026-10-18T12:00:00-07:00")]
_, seqs3, _, _ = sg.day_shape(CATS, early, "2026-W42", CFG)
check("early long day reports next day's first identity event", seqs3[0]["text"].endswith("first identity event at 11:00"), True)
# empty weekdays
sparse = [ev("builder", "b", "2026-10-14T10:00:00-07:00", "2026-10-14T11:00:00-07:00")]
_, _, sflags4, _ = sg.day_shape(CATS, sparse, "2026-W42", CFG)
check("4 empty weekdays -> notice", (sev(sflags4, "empty_weekdays"), next(f["title"] for f in sflags4 if f["kind"] == "empty_weekdays")), (sg.NOTICE, "4 weekdays with no identity event"))

# --- deep blocks ----------------------------------------------------------------------
frag = [ev("builder", "b", f"2026-10-1{d}T10:00:00-07:00", f"2026-10-1{d}T10:45:00-07:00") for d in range(2, 7)]
blocks, bflags = sg.deep_blocks(CATS, frag, {"builder": 5}, CFG)
check("5 x 45m builder blocks: no deep block notice", kinds(bflags), ["no_deep_block"])
check("longest block recorded", blocks["builder"]["longest_block_minutes"], 45)
deep = [ev("builder", "b", "2026-10-12T10:00:00-07:00", "2026-10-12T11:00:00-07:00"),
        ev("builder", "b2", "2026-10-12T11:00:00-07:00", "2026-10-12T12:30:00-07:00")]
blocks2, bflags2 = sg.deep_blocks(CATS, deep, {"builder": 3}, CFG)
check("touching blocks merge into one 150m block", (blocks2["builder"]["blocks"], blocks2["builder"]["longest_block_minutes"], bflags2), (1, 150, []))

# --- trash breakdown ---------------------------------------------------------------------
tb = sg.trash_breakdown(CATS, events, CFG)
check("trash bands", {k: v["events"] for k, v in tb["bands"].items()}, {"morning": 1, "late night": 1})
check("trash band minutes", tb["bands"]["morning"]["minutes"], 195)
check("trash event lexicon pointer", tb["events"][0]["lexicon"], {"sleep_disruption": ["get up"]})
check("no trash -> None", sg.trash_breakdown(CATS, [], CFG), None)

# --- markers --------------------------------------------------------------------------------
mk = sg.markers(CATS, [ev("designer_taste", "portfolio 🍅 2", "2026-10-12T10:00:00-07:00", "2026-10-12T11:00:00-07:00"),
                       ev("designer_taste", "portfolio 🍅", "2026-10-13T10:00:00-07:00", "2026-10-13T11:00:00-07:00"),
                       ev("builder", "job apps ✖️", "2026-10-14T10:00:00-07:00", "2026-10-14T11:00:00-07:00")], CFG)
check("🍅 total counts only explicit numbers", (mk["focus_sessions_total"], mk["focus_sessions_unspecified_events"]), (2, 1))
check("✖️ events listed", [m["title"] for m in mk["not_done_events"]], ["job apps ✖️"])

# --- carry-ins -------------------------------------------------------------------------------
refl = "# Reflection\n\n## What's your plan?\n\nold\n\n## What do you plan to do this week?\n\nShip the thing.\nRest on Sunday.\n\n## What might stress you up?\n\nx\n"
check("plan extracted verbatim", sg.extract_plan(refl), "Ship the thing.\nRest on Sunday.")
coach = "## The truth\n\nx\n\n## Commitments for this week\n\n1. **Career bet —** two blocks. calendar: Tue/Thu. done: both attended.\n2. **Life anchor —** call home.\n\n## Question to carry\n\nq\n"
check("commitments extracted from the numbered list", sg.extract_commitments(coach),
      ["**Career bet —** two blocks. calendar: Tue/Thu. done: both attended.", "**Life anchor —** call home."])
coach2 = "## A small experiment for this week\n\n- one\n- two\n"
check("bulleted experiment items count too", sg.extract_commitments(coach2), ["one", "two"])
check("no commitments section -> empty", sg.extract_commitments("## Nothing\n\n1. x\n"), [])
threads = "# Threads\n\n## Open\n\n- 2026-10-13 — what happened after Burning Man?\n- hyp: late builds cost mornings\n\n## Closed\n\n- old\n"
check("open threads extracted", sg.extract_open_threads(threads), ["- 2026-10-13 — what happened after Burning Man?", "- hyp: late builds cost mornings"])

# --- compute + render ---------------------------------------------------------------------------
sig = sg.compute("2026-W42", events, {}, CATS, CFG)
check("standalone compute derives this week's hours through the engine", sig["week_over_week"][2]["hours"], 4)   # builder: 13–14 (1h) + 20–23 (3h)
md = sg.render_md(sig, CATS)
for heading in ("## Flags", "## Week over week", "## Schedule shape", "## Sequences", "## Trash time breakdown", "## Markers in titles", "## To check this week"):
    check(f"render has {heading}", heading in md, True)
check("render: attention flags sort first", md.index("⚠") < md.index("ℹ") if "ℹ" in md else True, True)
check("render: no prior weeks message", "nothing to compare against yet" in md, True)

# --- report -----------------------------------------------------------------------------------------
failed = [c for c in CHECKS if not c[3]]
for name, got, want, ok in CHECKS:
    print(("PASS" if ok else "FAIL") + f" {name} => {got!r}" + ("" if ok else f" (want {want!r})"))
print()
print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} passed" + ("  ✓" if not failed else "  ✗"))
sys.exit(1 if failed else 0)
