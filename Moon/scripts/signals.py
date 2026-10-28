#!/usr/bin/env python3
"""Moon Engine A — M3 signals.

Turn the week's `events.json` and the longitudinal `trends.csv` into
`signals.md` + `signals.json`: deterministic observations that the reflection
shows before the questions and that the coach must answer. The ledger says how
many hours each identity got; this stage says what *changed*, what the schedule's
*shape* was (late nights, lost mornings, early long days, deep blocks), which
days *followed* which, where Trash time actually sat, and which plan and
commitments from last week are due for a check.

Rules and thresholds live in `config/signals.yaml`. Nothing here assigns a
category or changes a cognitive-hour number. Title lexicons only point the
reader at events worth reading; they never decide anything. Pure stdlib.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import moon_common as mc
import engine

SIGNALS_YAML = mc.CONFIG_DIR / "signals.yaml"
THREADS_MD = mc.MOON_DIR / "threads.md"

DEFAULT_CONFIG = {
    "version": "signals_v1",
    "focus_identities": ["builder", "designer_taste"],
    "thresholds": {
        "baseline_weeks": 6,
        "drop_ratio": 0.5,
        "drop_min_hours": 4,
        "surge_ratio": 2.0,
        "surge_min_hours": 6,
        "zero_streak_weeks": 3,
        "trash_rise_hours": 3,
        "invisible_surge_ratio": 1.5,
        "invisible_surge_min_hours": 8,
        "late_night_end": "23:00",
        "lost_morning_start": "06:00",
        "lost_morning_latest_start": "10:00",
        "lost_morning_min_minutes": 90,
        "lost_mornings_attention": 2,
        "late_nights_attention": 3,
        "early_long_day_start": "07:00",
        "early_long_day_min_hours": 5,
        "deep_block_minutes": 90,
        "deep_block_min_hours": 3,
        "empty_weekdays_notice": 2,
    },
    "markers": {"focus_session": "🍅", "not_done": "✖️"},
    "lexicons": {},
}

ATTENTION, NOTICE = "attention", "notice"
ICON = {ATTENTION: "⚠", NOTICE: "ℹ"}
# flag kinds whose evidence is a list of days/events, rendered as sub-bullets
LISTED_KINDS = {"late_nights", "lost_mornings", "late_then_lost_morning", "empty_weekdays"}


# --- Config -------------------------------------------------------------------
def _coerce(val):
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        return [_coerce(x) for x in _split_list(inner)] if inner else []
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        return val[1:-1]
    low = val.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        return val


def _split_list(inner):
    out, cur, quote = [], "", None
    for ch in inner:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur += ch
        elif ch == ",":
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [x.strip() for x in out if x.strip()]


def _strip_comment(raw):
    # strip a trailing ` # comment` that is not inside quotes
    quote, out = None, ""
    for i, ch in enumerate(raw):
        if quote:
            out += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out += ch
        elif ch == "#" and (i == 0 or raw[i - 1].isspace()):
            break
        else:
            out += ch
    return out.rstrip()


def _parse_signals_yaml(text):
    """Zero-dependency parser for signals.yaml: top-level scalars/inline lists and
    one level of nested `key:` blocks of scalars/inline lists. Not general YAML."""
    data, block = {}, None
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indented = line[:1].isspace()
        key, _, val = line.strip().partition(":")
        key = key.strip()
        if not indented:
            if val.strip():
                data[key] = _coerce(val)
                block = None
            else:
                data[key] = {}
                block = data[key]
        elif block is not None:
            block[key] = _coerce(val)
    return data


def load_config(path=SIGNALS_YAML):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))     # deep copy of the defaults
    p = Path(path)
    if p.exists():
        text = p.read_text()
        try:
            import yaml
            data = yaml.safe_load(text) or {}
        except ModuleNotFoundError:
            data = _parse_signals_yaml(text)
        for k, v in data.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


def _t(s):
    """'23:00' -> time(23, 0)."""
    if isinstance(s, time):
        return s
    h, m = str(s).split(":")
    return time(int(h), int(m))


# --- Trends -------------------------------------------------------------------
def load_trends(path=mc.TRENDS_CSV):
    """trends.csv -> {week_key: {category_id: cognitive_hours}} (all versions kept
    separate is unnecessary here: the current set is the only one written)."""
    out = {}
    p = Path(path)
    if not p.exists():
        return out
    with p.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != engine.TRENDS_HEADER:
            return out
        for r in reader:
            out.setdefault(r["week_iso"], {})[r["category_id"]] = int(r["cognitive_hours"])
    return out


def prior_weeks(trends, week_key, n):
    """The last `n` recorded weeks strictly before `week_key`, oldest first."""
    weeks = sorted(w for w in trends if w < week_key)
    return weeks[-n:] if n else weeks


def _fmt_h(x):
    if isinstance(x, float) and not x.is_integer():
        return f"{x:g}h"
    return f"{int(x)}h"


def week_over_week(cats, trends, week_key, this_week, cfg):
    """Per category: this week vs previous recorded week vs trailing median, plus
    zero-hour streaks. Returns (rows, flags, baseline_weeks)."""
    th = cfg["thresholds"]
    base = prior_weeks(trends, week_key, int(th["baseline_weeks"]))
    prev = base[-1] if base else None
    all_prior = sorted(w for w in trends if w < week_key)
    rows, flags = [], []
    order = list(cats.ids) + list(mc.SPECIAL_BUCKETS)
    for cat in order:
        hours = this_week.get(cat, 0)
        name = cats.name(cat)
        # only weeks that actually recorded this category count as history, so a
        # newly added identity is not judged against weeks that never tracked it
        hist = [trends[w][cat] for w in base if cat in trends[w]]
        prev_h = trends[prev].get(cat) if prev else None
        median = statistics.median(hist) if hist else None
        streak = 0
        if hours == 0:
            streak = 1
            for w in reversed(all_prior):
                if trends[w].get(cat) == 0:
                    streak += 1
                else:
                    break
        row = {"category": cat, "display_name": name, "hours": hours,
               "prev_week": prev, "prev_hours": prev_h, "median": median,
               "baseline_n": len(hist), "zero_streak": streak}
        rows.append(row)
        if cat == mc.TRASH_ID:
            ref = max(x for x in (prev_h, median) if x is not None) if (prev_h is not None or median is not None) else 0
            if hours > 0 and hours - ref >= th["trash_rise_hours"]:
                flags.append(_flag(ATTENTION, "trash_rise", cat,
                                   f"Trash time rose to {hours}h",
                                   [_cmp(prev, prev_h, median, len(hist))]))
            continue
        if cat == mc.INVISIBLE_ID:
            if median is not None and median > 0 and hours >= th["invisible_surge_ratio"] * median \
                    and hours - median >= th["invisible_surge_min_hours"]:
                flags.append(_flag(NOTICE, "invisible_surge", cat,
                                   f"Invisible surged to {hours}h",
                                   [_cmp(prev, prev_h, median, len(hist))]))
            continue
        # identities
        if streak >= th["zero_streak_weeks"]:
            since = all_prior[-(streak - 1)] if streak > 1 else week_key
            flags.append(_flag(ATTENTION, "zero_streak", cat,
                               f"{name}: 0h for {streak} recorded weeks in a row",
                               [f"0h every recorded week since {since}."]))
            continue
        if median is not None and len(hist) >= 2:
            if hours <= th["drop_ratio"] * median and median - hours >= th["drop_min_hours"]:
                if hours == 0 and prev_h == 0:
                    title = f"{name} still at 0h ({_ordinal(streak)} recorded week)"
                else:
                    title = f"{name} dropped to {hours}h"
                flags.append(_flag(ATTENTION, "identity_drop", cat, title,
                                   [_cmp(prev, prev_h, median, len(hist))]))
            elif hours >= th["surge_ratio"] * median and hours - median >= th["surge_min_hours"]:
                flags.append(_flag(NOTICE, "identity_surge", cat,
                                   f"{name} surged to {hours}h",
                                   [_cmp(prev, prev_h, median, len(hist))]))
        elif prev_h is not None and len(hist) == 1:
            if hours <= th["drop_ratio"] * prev_h and prev_h - hours >= th["drop_min_hours"]:
                flags.append(_flag(ATTENTION, "identity_drop", cat,
                                   f"{name} dropped to {hours}h",
                                   [f"{prev_h}h in {prev} (only one prior recorded week)."]))
    return rows, flags, base


def _ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _cmp(prev, prev_h, median, n):
    parts = []
    if prev is not None:
        parts.append(f"{_fmt_h(prev_h)} in {prev} (previous recorded week)")
    if median is not None and n:
        parts.append(f"median {_fmt_h(median)} over the {n} prior recorded weeks")
    return "; ".join(parts) + "." if parts else "No prior weeks recorded."


def _flag(severity, kind, category, title, evidence):
    return {"severity": severity, "kind": kind, "category": category,
            "title": title, "evidence": list(evidence)}


# --- Schedule shape -------------------------------------------------------------
def _dt(s):
    return datetime.fromisoformat(s)


def _counted(events):
    return [e for e in engine._counted(events)
            if _dt(e["end_local"]) - _dt(e["start_local"]) < timedelta(hours=mc.MULTI_DAY_EVENT_MIN_HOURS)]


def _envelopes(events):
    return [e for e in engine._counted(events)
            if _dt(e["end_local"]) - _dt(e["start_local"]) >= timedelta(hours=mc.MULTI_DAY_EVENT_MIN_HOURS)]


def _label(e, cats):
    return f"{cats.name(e['category'])}: {e['title'] or '(untitled)'}"


def _hhmm(dt_, day):
    s = dt_.strftime("%H:%M")
    extra = (dt_.date() - day).days
    return s + (f" (+{extra})" if extra > 0 else "")


def _is_lost_morning(e, th):
    if e["category"] not in mc.SPECIAL_BUCKETS:
        return False
    st = _dt(e["start_local"])
    return (_t(th["lost_morning_start"]) <= st.time() <= _t(th["lost_morning_latest_start"])
            and e["duration_min"] >= th["lost_morning_min_minutes"])


def _is_early_long(e, th):
    st = _dt(e["start_local"])
    return st.time() <= _t(th["early_long_day_start"]) and \
        e["duration_min"] >= th["early_long_day_min_hours"] * 60


def _ends_late(e, day, th):
    en = _dt(e["end_local"])
    if en.date() > day and en.time() != time(0, 0):
        return True                             # crosses midnight
    if en.date() > day:
        return True                             # ends exactly at midnight
    return en.time() >= _t(th["late_night_end"])


def day_shape(cats, events, week_key, cfg, prev_week_events=None, history=None):
    """One row per local day of the week (Mon–Sun) plus sequences across days.
    `history` is a list of prior weeks' shape counts (see `shape_history`) so the
    late-night / lost-morning flags are judged against the person's own normal."""
    th = cfg["thresholds"]
    year, week = mc.parse_week_key(week_key)
    monday = date.fromisocalendar(year, week, 1)
    counted = _counted(events)
    prev_counted = _counted(prev_week_events or [])
    by_day = {}
    for e in counted + prev_counted:
        by_day.setdefault(_dt(e["start_local"]).date(), []).append(e)

    days = []
    for i in range(7):
        d = monday + timedelta(days=i)
        evs = sorted(by_day.get(d, []), key=lambda e: e["start_local"])
        ident = [e for e in evs if e["category"] in cats]
        first_ident = min((_dt(e["start_local"]) for e in ident), default=None)
        last_end_ev = max(evs, key=lambda e: _dt(e["end_local"]), default=None)
        last_end = _dt(last_end_ev["end_local"]) if last_end_ev else None
        ident_min = sum((b[1] - b[0]).total_seconds() / 60 for b in engine.merge_blocks(ident)) if ident else 0
        trash_min = sum(e["duration_min"] for e in evs if e["category"] == mc.TRASH_ID)
        inv_min = sum(e["duration_min"] for e in evs if e["category"] == mc.INVISIBLE_ID)
        lost = [e for e in evs if _is_lost_morning(e, th)]
        early = [e for e in evs if _is_early_long(e, th)]
        late = [e for e in evs if _ends_late(e, d, th)]
        days.append({
            "date": d.isoformat(), "dow": d.strftime("%a"),
            "first_identity_start": _hhmm(first_ident, d) if first_ident else None,
            "first_identity_event": _label(min(ident, key=lambda e: e["start_local"]), cats) if ident else None,
            "last_end": _hhmm(last_end, d) if last_end else None,
            "last_event": _label(last_end_ev, cats) if last_end_ev else None,
            "identity_minutes": int(round(ident_min)),
            "trash_minutes": trash_min, "invisible_minutes": inv_min,
            "late_night": bool(late), "late_events": [_label(e, cats) for e in late],
            "lost_mornings": [f"{_dt(e['start_local']).strftime('%H:%M')}–{_hhmm(_dt(e['end_local']), d)} {_label(e, cats)}" for e in lost],
            "early_long_days": [f"{_dt(e['start_local']).strftime('%H:%M')}–{_hhmm(_dt(e['end_local']), d)} {_label(e, cats)}" for e in early],
            "events": len([e for e in evs]),
        })

    # the day before Monday (previous week's Sunday) for cross-week sequences
    before = monday - timedelta(days=1)
    bevs = by_day.get(before, [])
    before_row = None
    if bevs:
        last_end_ev = max(bevs, key=lambda e: _dt(e["end_local"]))
        before_row = {"date": before.isoformat(), "dow": before.strftime("%a"),
                      "late_night": any(_ends_late(e, before, th) for e in bevs),
                      "late_events": [_label(e, cats) for e in bevs if _ends_late(e, before, th)],
                      "last_end": _hhmm(_dt(last_end_ev["end_local"]), before),
                      "early_long_days": [f"{_dt(e['start_local']).strftime('%H:%M')}–{_hhmm(_dt(e['end_local']), before)} {_label(e, cats)}" for e in bevs if _is_early_long(e, th)]}

    sequences = []
    chain = ([before_row] if before_row else []) + days
    for a, b in zip(chain, chain[1:]):
        if b is None or b not in days:
            continue
        if a["late_night"] and b["lost_mornings"]:
            sequences.append({
                "kind": "late_night_then_lost_morning",
                "day": a["date"], "next_day": b["date"],
                "text": (f"{a['dow']} {a['date'][5:]} ended {a['last_end']} ({'; '.join(a['late_events'])}) → "
                         f"{b['dow']} {b['date'][5:]} lost morning {'; '.join(b['lost_mornings'])}")})
        if a.get("early_long_days"):
            nxt = b.get("first_identity_start")
            tail = f"lost morning {'; '.join(b['lost_mornings'])}" if b["lost_mornings"] else \
                (f"first identity event at {nxt}" if nxt else "no identity event")
            sequences.append({
                "kind": "early_long_day_then_next_day",
                "day": a["date"], "next_day": b["date"],
                "text": f"{a['dow']} {a['date'][5:]} early long day ({'; '.join(a['early_long_days'])}) → {b['dow']} {b['date'][5:]}: {tail}"})

    # late-night drift: a Trash/Invisible event at night whose title hits screen_drift
    lex = cfg.get("lexicons") or {}
    drift_terms = lex.get("screen_drift") or []
    for e in counted:
        if e["category"] in mc.SPECIAL_BUCKETS and _ends_late(e, _dt(e["start_local"]).date(), th):
            hits = _lexicon_hits(e["title"], {"screen_drift": drift_terms})
            if hits:
                d = _dt(e["start_local"])
                sequences.append({"kind": "late_night_drift", "day": d.date().isoformat(),
                                  "text": f"{d.strftime('%a %m/%d %H:%M')}–{_hhmm(_dt(e['end_local']), d.date())} {_label(e, cats)}"})

    flags = []
    late_days = [d for d in days if d["late_night"]]
    lost_days = [d for d in days if d["lost_mornings"]]
    n_lost = sum(len(d["lost_mornings"]) for d in days)
    n_early = sum(len(d["early_long_days"]) for d in days)
    counts = {"late_nights": len(late_days), "lost_mornings": n_lost, "early_long_days": n_early}
    hist = history or []
    if late_days:
        med = statistics.median(h["late_nights"] for h in hist) if len(hist) >= 2 else None
        # attention only when it is both frequent and above the person's own normal
        sev = ATTENTION if len(late_days) >= th["late_nights_attention"] and (med is None or len(late_days) > med) else NOTICE
        flags.append(_flag(sev, "late_nights", None,
                           f"{len(late_days)} late night{'s' if len(late_days) != 1 else ''} (ended at/after {th['late_night_end']})"
                           + (f" — your median is {_fmt_n(med)} over {len(hist)} prior weeks" if med is not None else ""),
                           [f"{d['dow']} {d['date'][5:]} ended {d['last_end']} — {'; '.join(d['late_events'])}" for d in late_days]))
    if n_lost:
        med = statistics.median(h["lost_mornings"] for h in hist) if len(hist) >= 2 else None
        sev = ATTENTION if n_lost >= th["lost_mornings_attention"] and (med is None or n_lost > med) else NOTICE
        flags.append(_flag(sev, "lost_mornings", None,
                           f"{n_lost} lost morning{'s' if n_lost != 1 else ''} (Trash/Invisible block of {th['lost_morning_min_minutes']}m+ starting {th['lost_morning_start']}–{th['lost_morning_latest_start']})"
                           + (f" — your median is {_fmt_n(med)} over {len(hist)} prior weeks" if med is not None else ""),
                           [f"{d['dow']} {d['date'][5:]} {m}" for d in lost_days for m in d["lost_mornings"]]))
    chained = [s for s in sequences if s["kind"] == "late_night_then_lost_morning"]
    if chained:
        flags.append(_flag(ATTENTION, "late_then_lost_morning", None,
                           f"{len(chained)} of {n_lost} lost morning{'s' if n_lost != 1 else ''} followed a late night",
                           [s["text"] for s in chained]))
    weekdays_empty = [d for d in days[:5] if d["identity_minutes"] == 0]
    if len(weekdays_empty) >= th["empty_weekdays_notice"]:
        flags.append(_flag(NOTICE, "empty_weekdays", None,
                           f"{len(weekdays_empty)} weekdays with no identity event",
                           [f"{d['dow']} {d['date'][5:]}" + (f" — {d['events']} non-identity event(s)" if d['events'] else " — nothing scheduled") for d in weekdays_empty]))
    return days, sequences, flags, counts


def shape_history(cats, weeks, cfg):
    """Shape counts for prior weeks whose events.json is still on disk (read-only).
    Weeks without local events are skipped, never guessed."""
    out = []
    for w in weeks:
        path = mc.WEEKS_DIR / w / "events.json"
        if not path.exists():
            continue
        try:
            evs = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        counts = day_shape(cats, evs, w, cfg)[3]
        counts["week"] = w
        out.append(counts)
    return out


def _fmt_n(x):
    return f"{x:g}"


# --- Blocks per identity -----------------------------------------------------------
def deep_blocks(cats, events, this_week, cfg):
    th = cfg["thresholds"]
    out, flags = {}, []
    by_cat = {}
    for e in _counted(events):
        by_cat.setdefault(e["category"], []).append(e)
    for cat in list(cats.ids) + list(mc.SPECIAL_BUCKETS):
        blocks = engine.merge_blocks(by_cat.get(cat, []))
        longest = max(((b[1] - b[0]).total_seconds() / 60 for b in blocks), default=0)
        out[cat] = {"blocks": len(blocks), "longest_block_minutes": int(round(longest))}
        if cat in (cfg.get("focus_identities") or []) and this_week.get(cat, 0) >= th["deep_block_min_hours"] \
                and longest < th["deep_block_minutes"]:
            flags.append(_flag(NOTICE, "no_deep_block", cat,
                               f"{cats.name(cat)}: {this_week.get(cat, 0)}h but no block of {th['deep_block_minutes']}m+",
                               [f"{len(blocks)} blocks, longest {mc.fmt_hm(longest)}."]))
    return out, flags


# --- Trash breakdown ---------------------------------------------------------------
BANDS = [("morning", time(6, 0), time(12, 0)), ("afternoon", time(12, 0), time(18, 0)),
         ("evening", time(18, 0), time(23, 0)), ("late night", time(23, 0), time(6, 0))]


def _band(t):
    for name, a, b in BANDS:
        if a < b and a <= t < b:
            return name
    return "late night"


def trash_breakdown(cats, events, cfg):
    trash = sorted((e for e in _counted(events) if e["category"] == mc.TRASH_ID), key=lambda e: e["start_local"])
    if not trash:
        return None
    bands = {}
    for e in trash:
        b = _band(_dt(e["start_local"]).time())
        bands.setdefault(b, {"events": 0, "minutes": 0})
        bands[b]["events"] += 1
        bands[b]["minutes"] += e["duration_min"]
    items = []
    for e in trash:
        d = _dt(e["start_local"])
        items.append({"when": f"{d.strftime('%a %m/%d %H:%M')}–{_hhmm(_dt(e['end_local']), d.date())}",
                      "title": e["title"], "minutes": e["duration_min"],
                      "band": _band(d.time()),
                      "lexicon": _lexicon_hits(e["title"], cfg.get("lexicons") or {})})
    return {"bands": {k: bands[k] for k, _a, _b in BANDS if k in bands}, "events": items}


# --- Markers and lexicons ------------------------------------------------------------
def _lexicon_hits(title, lexicons):
    t = (title or "").lower()
    hits = {}
    for family, terms in (lexicons or {}).items():
        for term in terms or []:
            term = str(term).lower()
            if " " in term:
                ok = term in t
            else:
                ok = re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", t) is not None
            if ok:
                hits.setdefault(family, []).append(term)
    return hits


def focus_sessions(title, marker):
    """Count 🍅 sessions in a title: `🍅 2`, `🍅 x 2`, `3 🍅`, `2x 🍅` -> 2, 2, 3, 2.
    A bare marker returns None (count unspecified) — never invented."""
    if not title or marker not in title:
        return 0, False
    m = re.search(r"(\d+)\s*[x×]?\s*" + re.escape(marker), title) or \
        re.search(re.escape(marker) + r"\s*[x×]?\s*(\d+)", title)
    if m:
        return int(m.group(1)), True
    return None, True


def markers(cats, events, cfg):
    mk = cfg.get("markers") or {}
    lex = cfg.get("lexicons") or {}
    focus, not_done, lexicon = [], [], {}
    total, unspecified = 0, 0
    for e in sorted(_counted(events), key=lambda x: x["start_local"]):
        d = _dt(e["start_local"])
        when = f"{d.strftime('%a %m/%d %H:%M')}"
        if mk.get("focus_session"):
            n, present = focus_sessions(e["title"], mk["focus_session"])
            if present:
                focus.append({"when": when, "title": e["title"], "category": e["category"], "sessions": n})
                if n is None:
                    unspecified += 1
                else:
                    total += n
        if mk.get("not_done") and e["title"] and mk["not_done"] in e["title"]:
            not_done.append({"when": when, "title": e["title"], "category": e["category"]})
        for fam, terms in _lexicon_hits(e["title"], lex).items():
            lexicon.setdefault(fam, []).append({"when": when, "title": e["title"], "category": e["category"], "terms": terms})
    return {"focus_sessions_total": total, "focus_sessions_unspecified_events": unspecified,
            "focus_events": focus, "not_done_events": not_done, "lexicon": lexicon}


# --- Carry-ins: last week's plan, commitments, open threads ----------------------------
def _sections(text, heading_pred):
    """The body lines of every `## ` section whose heading satisfies pred, in order."""
    out, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("## "):
            cur = [] if heading_pred(ln[3:].strip()) else None
            if cur is not None:
                out.append(cur)
            continue
        if cur is not None:
            cur.append(ln)
    return out


def _section(text, heading_pred):
    """Return the body lines of the first `## ` section whose heading satisfies pred."""
    found = _sections(text, heading_pred)
    return found[0] if found else []


def extract_plan(reflection_text):
    body = _section(reflection_text, lambda h: h.lower().startswith("what do you plan to do"))
    return "\n".join(body).strip()


def extract_commitments(coaching_text):
    """Numbered or bulleted items under any `## ` heading mentioning commitments,
    moves, or an experiment. Verbatim; the coach grades them."""
    def is_forward(h):
        # "Last week's commitments" is the grading table, not this week's promises
        return (re.search(r"commit|moves|experiment|action", h, re.I) is not None
                and re.search(r"last week|previous|prior|graded", h, re.I) is None)
    for body in _sections(coaching_text, is_forward):
        items = [re.sub(r"^\s*(\d+[.)]|[-*])\s+", "", ln).strip()
                 for ln in body if re.match(r"^\s*(\d+[.)]|[-*])\s+", ln)]
        if items:
            return items
    return []


def extract_open_threads(threads_text):
    body = _section(threads_text, lambda h: h.lower().startswith("open"))
    return [ln.strip() for ln in body if ln.strip().startswith(("-", "*"))]


def _frontmatter_date(text):
    m = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
    return m.group(1) if m else ""


def latest_coaching_file(week_dir):
    """The coaching note whose commitments carry forward: `coaching.md` or any
    `coaching-revised*.md`, whichever has the newest frontmatter `date:` (ties and
    undated files fall back to the original). A revision replaces the original's
    commitments only by being newer; nothing else is inferred."""
    week_dir = Path(week_dir)
    candidates = [p for p in [week_dir / "coaching.md"] + sorted(week_dir.glob("coaching-revised*.md")) if p.exists()]
    if not candidates:
        return None
    dated = [(_frontmatter_date(p.read_text()), i, p) for i, p in enumerate(candidates)]
    dated.sort(key=lambda t: (t[0], -t[1]), reverse=True)
    return dated[0][2]


def carry_ins(week_key, prev_week):
    out = {"previous_week": prev_week, "plan": None, "commitments": [], "commitments_source": None,
           "open_threads": [], "repull_diff": None}
    if prev_week:
        refl = mc.WEEKS_DIR / prev_week / "reflection.md"
        coach = latest_coaching_file(mc.WEEKS_DIR / prev_week)
        if refl.exists():
            out["plan"] = extract_plan(refl.read_text()) or None
        if coach is not None:
            out["commitments"] = extract_commitments(coach.read_text())
            out["commitments_source"] = coach.name
    diff = mc.WEEKS_DIR / week_key / "repull-diff.md"
    if diff.exists():
        out["repull_diff"] = diff.name
    if THREADS_MD.exists():
        out["open_threads"] = extract_open_threads(THREADS_MD.read_text())
    return out


# --- Assemble ----------------------------------------------------------------------
def compute(week_key, events, trends, cats, cfg, prev_week_events=None, carry=None, history=None):
    this_week = trends.get(week_key)
    if this_week is None:
        # standalone use without trends: derive from events through the engine's rules
        this_week = {}
        by_cat = {}
        for e in events:
            by_cat.setdefault(e["category"], []).append(e)
        for cat in list(cats.ids) + list(mc.SPECIAL_BUCKETS):
            segs = engine._prepare_category_events(by_cat.get(cat, []), cat)[0]
            this_week[cat] = engine.compute_category(segs)[0] if segs else 0
    rows, wow_flags, base = week_over_week(cats, trends, week_key, this_week, cfg)
    days, sequences, shape_flags, shape_counts = day_shape(cats, events, week_key, cfg, prev_week_events, history)
    blocks, block_flags = deep_blocks(cats, events, this_week, cfg)
    for r in rows:
        r.update(blocks.get(r["category"], {}))
    trash = trash_breakdown(cats, events, cfg)
    mk = markers(cats, events, cfg)
    flags = wow_flags + shape_flags + block_flags
    if trash:
        for f in flags:
            if f["kind"] == "trash_rise":
                f["evidence"].append("Breakdown: " + ", ".join(
                    f"{b} {v['events']} event{'s' if v['events'] != 1 else ''} / {mc.fmt_hm(v['minutes'])}"
                    for b, v in trash["bands"].items()) + ".")
    flags.sort(key=lambda f: (0 if f["severity"] == ATTENTION else 1))
    envelopes = [f"{_dt(e['start_local']).strftime('%a %m/%d %H:%M')}–{_dt(e['end_local']).strftime('%a %m/%d %H:%M')} {_label(e, cats)}"
                 for e in _envelopes(events)]
    return {
        "week": week_key, "generator": "moon signals", "config_version": cfg.get("version"),
        "baseline_weeks": base, "previous_week": base[-1] if base else None,
        "flags": flags, "week_over_week": rows, "days": days, "sequences": sequences,
        "shape": shape_counts, "shape_history": history or [],
        "multi_day_envelopes": envelopes, "trash": trash, "markers": mk,
        "carry": carry or {"previous_week": None, "plan": None, "commitments": [], "commitments_source": None,
                           "open_threads": [], "repull_diff": None},
    }


def render_md(sig, cats):
    week = sig["week"]
    L = ["---", f"week: {week}", "type: signals", "generator: moon signals",
         f"baseline_weeks: {', '.join(sig['baseline_weeks']) if sig['baseline_weeks'] else 'none'}",
         "---", "", f"# Signals — {week}", "",
         ("_Deterministic observations from `events.json` and `trends.csv`. Facts, not advice. "
          "The reflection shows the flags before the questions; the coach must answer every ⚠ "
          "item and may use the rest as evidence. Numbers are cognitive hours from Engine A._"), ""]
    if sig["carry"].get("repull_diff"):
        L += [(f"> **Re-pulled after review.** This week's calendars changed after its reflection was "
               f"written; the reflection and the coaching of that date cite the reviewed numbers. "
               f"See `{sig['carry']['repull_diff']}` and `reviewed/`. Everything below is from the current pull."), ""]
    # Flags
    L += ["## Flags", ""]
    if sig["flags"]:
        for f in sig["flags"]:
            if len(f["evidence"]) > 1 and f["kind"] in LISTED_KINDS:
                L.append(f"- {ICON[f['severity']]} **{f['title']}**")
                L += [f"  - {ev}" for ev in f["evidence"]]
            else:
                L.append(f"- {ICON[f['severity']]} **{f['title']}** — " + " ".join(f["evidence"]))
    else:
        L.append("_No flags this week._")
    # Week over week
    prev = sig["previous_week"]
    n = len(sig["baseline_weeks"])
    L += ["", "## Week over week", ""]
    if n:
        gaps = _gap_note(sig["baseline_weeks"], week)
        L.append(f"Previous recorded week: **{prev}**. Median over the {n} prior recorded weeks "
                 f"({sig['baseline_weeks'][0]}–{sig['baseline_weeks'][-1]}).{gaps}")
        L += ["", "| Identity | This week | Prev | Median | 0h streak | Blocks | Longest block |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for r in sig["week_over_week"]:
            name = r["display_name"] if r["category"] in cats else f"_{r['display_name']}_"
            med = _fmt_h(r["median"]) if r["median"] is not None else "—"
            pv = _fmt_h(r["prev_hours"]) if r["prev_hours"] is not None else "—"
            streak = str(r["zero_streak"]) if r["zero_streak"] else ""
            L.append(f"| {name} | {r['hours']}h | {pv} | {med} | {streak} | {r.get('blocks', 0)} | "
                     f"{mc.fmt_hm(r.get('longest_block_minutes', 0)) if r.get('longest_block_minutes') else '—'} |")
    else:
        L.append("_No prior weeks in `trends.csv`; nothing to compare against yet._")
    # Schedule shape
    L += ["", "## Schedule shape", "",
          "| Day | First identity event | Last event ended | Identity time | Trash | Invisible | Notes |",
          "| --- | --- | --- | ---: | ---: | ---: | --- |"]
    for d in sig["days"]:
        notes = []
        if d["lost_mornings"]:
            notes.append("lost morning")
        if d["late_night"]:
            notes.append("late night")
        if d["early_long_days"]:
            notes.append("early long day")
        if d["identity_minutes"] == 0:
            notes.append("no identity event")
        first = f"{d['first_identity_start']} {d['first_identity_event']}" if d["first_identity_start"] else "—"
        last = f"{d['last_end']} {d['last_event']}" if d["last_end"] else "—"
        L.append(f"| {d['dow']} {d['date'][5:]} | {_short(first)} | {_short(last)} | "
                 f"{mc.fmt_hm(d['identity_minutes']) if d['identity_minutes'] else '—'} | "
                 f"{mc.fmt_hm(d['trash_minutes']) if d['trash_minutes'] else '—'} | "
                 f"{mc.fmt_hm(d['invisible_minutes']) if d['invisible_minutes'] else '—'} | {', '.join(notes)} |")
    if sig["multi_day_envelopes"]:
        L += ["", "Multi-day envelopes (not in the day table): " + "; ".join(sig["multi_day_envelopes"]) + "."]
    # Sequences
    L += ["", "## Sequences", ""]
    if sig["sequences"]:
        for s in sig["sequences"]:
            kind = {"late_night_then_lost_morning": "Late night → lost morning",
                    "early_long_day_then_next_day": "Early long day → next day",
                    "late_night_drift": "Late-night drift"}.get(s["kind"], s["kind"])
            L.append(f"- **{kind}:** {s['text']}")
    else:
        L.append("_No cross-day sequences detected._")
    # Trash
    L += ["", "## Trash time breakdown", ""]
    if sig["trash"]:
        L.append("By time of day: " + ", ".join(
            f"**{b}** {v['events']} event{'s' if v['events'] != 1 else ''} / {mc.fmt_hm(v['minutes'])}"
            for b, v in sig["trash"]["bands"].items()) + ".")
        L.append("")
        for e in sig["trash"]["events"]:
            lex = "; ".join(f"{fam}: {', '.join(t)}" for fam, t in e["lexicon"].items())
            L.append(f"- {e['when']}  {e['title'] or '(untitled)'}  ({e['minutes']}m, {e['band']})" + (f" — _{lex}_" if lex else ""))
    else:
        L.append("_No Trash time recorded._")
    # Markers
    mk = sig["markers"]
    L += ["", "## Markers in titles", ""]
    any_marker = False
    if mk["focus_events"]:
        any_marker = True
        unspec = f" + {mk['focus_sessions_unspecified_events']} event(s) with no count" if mk["focus_sessions_unspecified_events"] else ""
        L.append(f"- 🍅 **{mk['focus_sessions_total']} focus sessions counted**{unspec}: " +
                 "; ".join(f"{f['when']} {f['title']}" for f in mk["focus_events"]))
    if mk["not_done_events"]:
        any_marker = True
        L.append("- ✖️ **planned but not done** (the person's own marker): " +
                 "; ".join(f"{f['when']} {f['title']}" for f in mk["not_done_events"]))
    for fam, items in mk["lexicon"].items():
        any_marker = True
        L.append(f"- _{fam}_ ({len(items)}): " + "; ".join(f"{i['when']} {i['title']} [{cats.name(i['category'])}]" for i in items))
    if not any_marker:
        L.append("_No markers or lexicon hits._")
    # Carry-ins
    c = sig["carry"]
    L += ["", "## To check this week", ""]
    if c["plan"]:
        L += [f"**Plan set in the {c['previous_week']} reflection:**", "", "> " + c["plan"].replace("\n", "\n> "), ""]
    else:
        L += ["_No plan carried from a previous reflection._", ""]
    if c["commitments"]:
        src = f" (`{c['commitments_source']}`)" if c.get("commitments_source") else ""
        L += [f"**Commitments from the {c['previous_week']} coaching**{src} (grade each: kept / partly / not):", ""]
        L += [f"- [ ] {x}" for x in c["commitments"]]
        L.append("")
    else:
        L += ["_No commitments found in a previous coaching note._", ""]
    if c["open_threads"]:
        L += ["**Open threads** (`Moon/threads.md`):", ""] + c["open_threads"]
    else:
        L += ["_No open threads in `Moon/threads.md`._"]
    L.append("")
    return "\n".join(L)


def _short(s, n=48):
    return s if len(s) <= n else s[: n - 1] + "…"


def _gap_note(base, week):
    """Name recorded-week gaps inside the baseline window so a comparison never
    silently spans a hole in the data."""
    keys = base + [week]
    missing = []
    for a, b in zip(keys, keys[1:]):
        ya, wa = mc.parse_week_key(a)
        yb, wb = mc.parse_week_key(b)
        d = date.fromisocalendar(ya, wa, 1) + timedelta(days=7)
        while d < date.fromisocalendar(yb, wb, 1):
            missing.append(mc.week_key_for_date(d)[0])
            d += timedelta(days=7)
    return f" Not recorded: {', '.join(missing)}." if missing else ""


def run(week_key, verbose=True):
    cats = mc.get_categories()
    cfg = load_config()
    week_dir = mc.WEEKS_DIR / week_key
    events_path = week_dir / "events.json"
    if not events_path.exists():
        raise SystemExit(f"No events.json for {week_key} at {events_path}. Run ingest + engine first.")
    events = json.loads(events_path.read_text())
    trends = load_trends()
    year, week = mc.parse_week_key(week_key)
    prev_key = mc.week_key_for_date(date.fromisocalendar(year, week, 1) - timedelta(days=1))[0]
    prev_events_path = mc.WEEKS_DIR / prev_key / "events.json"
    prev_events = json.loads(prev_events_path.read_text()) if prev_events_path.exists() else None
    base = prior_weeks(trends, week_key, 1)
    carry = carry_ins(week_key, base[-1] if base else None)
    history = shape_history(cats, prior_weeks(trends, week_key, int(cfg["thresholds"]["baseline_weeks"])), cfg)
    sig = compute(week_key, events, trends, cats, cfg, prev_events, carry, history)
    (week_dir / "signals.json").write_text(json.dumps(sig, indent=2, ensure_ascii=False) + "\n")
    md_path = week_dir / "signals.md"
    md_path.write_text(render_md(sig, cats))
    if verbose:
        att = [f for f in sig["flags"] if f["severity"] == ATTENTION]
        print(f"Signals {week_key}: {len(att)} attention, {len(sig['flags']) - len(att)} notice")
        for f in sig["flags"]:
            print(f"  {ICON[f['severity']]} {f['title']}")
        print(f"Wrote {md_path}")
    return md_path, sig


def main(argv=None):
    ap = argparse.ArgumentParser(description="Moon M3 signals: events.json + trends.csv -> signals.md")
    ap.add_argument("--week", help="ISO week key, e.g. 2026-W24 (default: most recent completed week)")
    args = ap.parse_args(argv)
    if args.week:
        y, w = mc.parse_week_key(args.week)
        key = f"{y}-W{w:02d}"
    else:
        key = mc.most_recent_completed_week(date.today())[0]
    run(key)


if __name__ == "__main__":
    main()
