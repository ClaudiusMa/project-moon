"""Moon Engine A — shared helpers.

Pure stdlib. Paths, the fixed category set, timezone resolution, ISO-week math,
feed-config loading (PyYAML with a zero-dependency fallback), and small
formatting helpers. Imported by ingest.py, engine.py, and moon-weekly.
"""
from __future__ import annotations

import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# --- Paths (anchored on the Moon/ dir, independent of CWD) -------------------
MOON_DIR = Path(__file__).resolve().parents[1]          # .../Moon
SCRIPTS_DIR = MOON_DIR / "scripts"
CONFIG_DIR = MOON_DIR / "config"
WEEKS_DIR = MOON_DIR / "weeks"
TRENDS_CSV = MOON_DIR / "trends.csv"
DEFAULT_FEEDS = CONFIG_DIR / "feeds.yaml"

# --- The fixed category set (the contract; mirrors config/categories.md) -----
CATEGORIES = [
    "Learn", "Build", "Career", "Habit",
    "Workout", "Social", "Exploration", "Trash",
]
CATEGORY_SET = set(CATEGORIES)


# --- Timezone ---------------------------------------------------------------
def detect_local_tz_name() -> str | None:
    """Best-effort IANA name for the system timezone (macOS / Linux)."""
    p = Path("/etc/localtime")
    try:
        if p.is_symlink():
            target = os.readlink(p)
            if "zoneinfo/" in target:
                return target.split("zoneinfo/", 1)[1]
    except OSError:
        pass
    tzenv = os.environ.get("TZ")
    return tzenv or None


def resolve_tz(name: str | None = None):
    """Return (tzinfo, label). Prefers an IANA name; falls back to the current
    fixed local offset (correct except across a DST change inside the week)."""
    if not name:
        name = detect_local_tz_name()
    if name:
        try:
            return ZoneInfo(name), name
        except Exception:
            pass
    local = datetime.now().astimezone()
    return local.tzinfo, (local.tzname() or str(local.utcoffset()))


# --- ISO-week math ----------------------------------------------------------
def parse_week_key(s: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d{4})-W(\d{2})", s.strip())
    if not m:
        raise SystemExit(f"Bad week key {s!r}; expected e.g. 2026-W24")
    return int(m.group(1)), int(m.group(2))


def week_key_for_date(d: date) -> tuple[str, int, int]:
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}", iso[0], iso[1]


def week_bounds(year: int, week: int, tz):
    """[Monday 00:00, next Monday 00:00) in `tz` for an ISO week."""
    monday = date.fromisocalendar(year, week, 1)
    start = datetime(monday.year, monday.month, monday.day, tzinfo=tz)
    end = start + timedelta(days=7)
    return start, end


def most_recent_completed_week(today: date) -> tuple[str, int, int]:
    """The last full Mon–Sun week that has already ended."""
    this_monday = today - timedelta(days=today.weekday())
    last_sunday = this_monday - timedelta(days=1)
    return week_key_for_date(last_sunday)


# --- Feed config (PyYAML + zero-dependency fallback) ------------------------
def _parse_simple_yaml(text: str) -> dict:
    """Minimal parser for the flat feeds.yaml shape so the tool keeps working
    when PyYAML is not installed. Supports a top-level `timezone:` scalar and a
    `feeds:` block of `Category: source` lines (or a flat `Category: source`)."""
    result: dict = {"timezone": None, "feeds": {}}
    in_feeds = False
    for raw in text.splitlines():
        if raw.lstrip().startswith("#"):
            continue
        if " #" in raw:                       # strip inline comments
            raw = raw.split(" #", 1)[0]
        if not raw.strip():
            continue
        indented = raw[:1].isspace()
        line = raw.strip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if indented and in_feeds:
            if val:
                result["feeds"][key] = val
            continue
        in_feeds = False
        if key == "timezone":
            result["timezone"] = val or None
        elif key == "feeds" and not val:
            in_feeds = True
        elif val:                             # tolerate flat `Category: source`
            result["feeds"][key] = val
    return result


def _normalize_config(raw) -> dict:
    if not isinstance(raw, dict):
        return {"timezone": None, "feeds": {}}
    tz = raw.get("timezone")
    feeds = {}
    if isinstance(raw.get("feeds"), dict):
        feeds = {str(k): str(v) for k, v in raw["feeds"].items()}
    else:
        for k, v in raw.items():
            if k != "timezone" and isinstance(v, str):
                feeds[str(k)] = v
    return {"timezone": tz, "feeds": feeds}


def load_feeds(path) -> dict:
    text = Path(path).read_text()
    try:
        import yaml
        return _normalize_config(yaml.safe_load(text))
    except ModuleNotFoundError:
        return _normalize_config(_parse_simple_yaml(text))


# --- Formatting -------------------------------------------------------------
def fmt_hm(minutes) -> str:
    minutes = int(round(minutes))
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"
