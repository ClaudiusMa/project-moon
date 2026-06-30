"""Moon Engine A — shared helpers.

Pure stdlib. Paths, the identity category set (loaded from config/categories.yaml),
the all-day-event policy, timezone resolution, ISO-week math, feed-config loading
(a markdown feed list, or YAML with a zero-dependency fallback), and small
formatting helpers. Imported by ingest.py, engine.py, and moon-weekly.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

# --- Paths (anchored on the Moon/ dir, independent of CWD) -------------------
MOON_DIR = Path(__file__).resolve().parents[1]          # .../Moon
SCRIPTS_DIR = MOON_DIR / "scripts"
CONFIG_DIR = MOON_DIR / "config"
WEEKS_DIR = MOON_DIR / "weeks"
TRENDS_CSV = MOON_DIR / "trends.csv"
DEFAULT_FEEDS = CONFIG_DIR / "feeds.yaml"
CATEGORIES_YAML = CONFIG_DIR / "categories.yaml"

# The astronaut's private workspace (sibling of Moon/, gitignored). The user-facing
# feed list lives here so secret iCal URLs never touch the shareable product folder.
ASTRONAUT_DIR = MOON_DIR.parent / "Astronaut"
DEFAULT_FEEDS_MD = ASTRONAUT_DIR / "rocket.md"

# Diagnostic, non-identity bucket: scheduled time on calendars that aren't an
# identity (your primary/Trash calendars). Surfaced in the report as "invisible"
# so drift is visible, but it is NOT an identity account (no core question, not in
# categories.yaml).
INVISIBLE_ID = "invisible"
INVISIBLE_DISPLAY = "Invisible (unallocated)"
TRASH_ID = "trash_time"
TRASH_DISPLAY = "Trash time"
# Non-identity diagnostic buckets, in report order. Not identities (no core question,
# not in categories.yaml) — shown as their own rows so trash/drift stays visible and
# can be examined in the reflection.
SPECIAL_BUCKETS = {TRASH_ID: TRASH_DISPLAY, INVISIBLE_ID: INVISIBLE_DISPLAY}

# --- All-day-event policy ----------------------------------------------------
# What to do with all-day events when computing cognitive hours. They are always
# recorded in events.json (with `all_day: true`) so the reflection recap still
# sees them; this only controls whether they COUNT toward cognitive hours.
#   "exclude" — recommended default. An all-day event (e.g. a family trip) would
#               otherwise add a full 24h block and swamp the week's totals.
#   "include" — count each all-day event at its full local-day span (a 1-day
#               all-day event = 24 cognitive hours).
ALL_DAY_POLICY = "exclude"   # "exclude" | "include"

# Sanity guardrail: a single local day should never legitimately exceed this many
# cognitive hours. Exceeding it signals heavy double-booking or a data bug, so the
# engine warns (it does not silently trust the number). See engine.run().
MAX_COGNITIVE_HOURS_PER_DAY = 24


# --- The identity category set (the contract; from config/categories.yaml) ---
@dataclass(frozen=True)
class CategorySet:
    """The canonical identity set: ordered ids plus their display names and core
    questions, and the version stamp written into reports and trends.csv."""
    version: str
    ids: tuple                  # ordered category ids (display + sort order)
    display: dict               # id -> display_name
    core_question: dict         # id -> core question

    def __contains__(self, cid) -> bool:
        return cid in self.display

    def name(self, cid) -> str:
        """display_name for a known id, a special-bucket label, or the raw id."""
        if cid in SPECIAL_BUCKETS:
            return SPECIAL_BUCKETS[cid]
        return self.display.get(cid, cid)

    def order(self, cid) -> int:
        """Sort key: canonical position for known ids, last for unexpected ones."""
        return self.ids.index(cid) if cid in self.display else len(self.ids)


def _parse_categories_yaml(text: str) -> dict:
    """Zero-dependency parser for the fixed categories.yaml shape: a top-level
    `version:` scalar and an `identities:` list of `{id, display_name,
    core_question}` maps. Mirrors the PyYAML result so the engine stays
    stdlib-only. Not a general YAML parser."""
    version, identities, cur, in_identities = None, [], None, False
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if " #" in raw:                       # strip inline comments
            raw = raw.split(" #", 1)[0]
        stripped = raw.strip()
        if not raw[:1].isspace():             # top-level key
            in_identities, cur = False, None
            key, _, val = stripped.partition(":")
            if key.strip() == "version":
                version = val.strip() or None
            elif key.strip() == "identities":
                in_identities = True
            continue
        if not in_identities:
            continue
        if stripped.startswith("- "):         # new list item
            cur = {}
            identities.append(cur)
            stripped = stripped[2:].strip()
            if not stripped:
                continue
        if cur is None:
            continue
        key, _, val = stripped.partition(":")
        cur[key.strip()] = val.strip()
    return {"version": version, "identities": identities}


def _build_category_set(data, path) -> CategorySet:
    if not isinstance(data, dict):
        raise SystemExit(f"Malformed {path}: expected a mapping at the top level.")
    version = str(data.get("version") or "").strip()
    if not version:
        raise SystemExit(f"Malformed {path}: missing `version:`.")
    raw = data.get("identities")
    if not isinstance(raw, list) or not raw:
        raise SystemExit(f"Malformed {path}: `identities:` must be a non-empty list.")
    ids, display, core_q = [], {}, {}
    for i, ent in enumerate(raw, 1):
        if not isinstance(ent, dict):
            raise SystemExit(f"Malformed {path}: identity #{i} is not a mapping.")
        cid = str(ent.get("id") or "").strip()
        name = str(ent.get("display_name") or "").strip()
        if not cid or not name:
            raise SystemExit(f"Malformed {path}: identity #{i} needs `id` and `display_name`.")
        if cid in display:
            raise SystemExit(f"Malformed {path}: duplicate id {cid!r}.")
        ids.append(cid)
        display[cid] = name
        core_q[cid] = str(ent.get("core_question") or "").strip()
    return CategorySet(version, tuple(ids), display, core_q)


def load_categories(path) -> CategorySet:
    """Parse a categories.yaml (PyYAML if available, else the stdlib fallback)."""
    text = Path(path).read_text()
    try:
        import yaml
        data = yaml.safe_load(text)
    except ModuleNotFoundError:
        data = _parse_categories_yaml(text)
    return _build_category_set(data, path)


@lru_cache(maxsize=None)
def get_categories() -> CategorySet:
    """The canonical identity set from config/categories.yaml (loaded once)."""
    return load_categories(CATEGORIES_YAML)


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


# --- Feed config: a markdown feed list, or YAML -----------------------------
def _parse_feeds_md(text: str) -> dict:
    """Parse Astronaut/rocket.md. Bullet lines `- <key>: <value>` where <key> is an
    identity id, `invisible`, or `timezone`, and <value> is a secret iCal URL or a
    local .ics path. Placeholder values (empty or starting with `<`) are skipped.
    `invisible` may appear multiple times (e.g. your primary and Trash calendars).
    Everything else in the file is prose and ignored."""
    feeds, invisible, tz = {}, [], None
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith(("-", "*")):
            continue
        line = line[1:].strip().lstrip("`").rstrip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().strip("`"), val.strip().strip("`")
        if not val or val.startswith("<"):
            continue
        if key == "invisible":
            invisible.append(val)
        elif key == "timezone":
            tz = val
        else:
            feeds[key] = val
    return {"timezone": tz, "feeds": feeds, "invisible": invisible}


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
        return {"timezone": None, "feeds": {}, "invisible": []}
    tz = raw.get("timezone")
    feeds = {}
    if isinstance(raw.get("feeds"), dict):
        feeds = {str(k): str(v) for k, v in raw["feeds"].items()}
    else:
        for k, v in raw.items():
            if k not in ("timezone", "invisible") and isinstance(v, str):
                feeds[str(k)] = v
    inv = raw.get("invisible") or []
    if isinstance(inv, str):
        inv = [inv]
    invisible = [str(x) for x in inv] if isinstance(inv, list) else []
    return {"timezone": tz, "feeds": feeds, "invisible": invisible}


def load_feeds(path) -> dict:
    """Load a feed config. Returns {timezone, feeds: {id: source}, invisible: [src]}.
    A `.md` file uses the markdown feed list; anything else is parsed as YAML
    (PyYAML if available, else the stdlib fallback)."""
    path = Path(path)
    text = path.read_text()
    if path.suffix.lower() == ".md":
        return _parse_feeds_md(text)
    try:
        import yaml
        return _normalize_config(yaml.safe_load(text))
    except ModuleNotFoundError:
        return _normalize_config(_parse_simple_yaml(text))


def resolve_feeds_path(explicit=None):
    """Pick the feed config: an explicit path, else Astronaut/rocket.md, else the
    legacy Moon/config/feeds.yaml."""
    if explicit:
        return Path(explicit)
    if DEFAULT_FEEDS_MD.exists():
        return DEFAULT_FEEDS_MD
    return DEFAULT_FEEDS


# --- Formatting -------------------------------------------------------------
def fmt_hm(minutes) -> str:
    minutes = int(round(minutes))
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"
