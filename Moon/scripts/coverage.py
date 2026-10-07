"""Private source expectations and evidence for a complete calendar pull (stdlib)."""
import hashlib
import json
from datetime import datetime, timezone
import moon_common as mc


def digest(data):
    return hashlib.sha256(data).hexdigest()


def signature(items, tz_label):
    # Only the digest is saved; calendar URLs never enter reports or evidence.
    return digest(json.dumps({"sources": sorted(items), "timezone": tz_label}, ensure_ascii=False).encode())


def expected_path():
    return mc.ASTRONAUT_DIR / "expected-calendars.json"


def counts(items):
    result = {}
    for category, source in items:
        if source and not source.startswith("<"):
            result[category] = result.get(category, 0) + 1
    return result


def validate(items, confirm=False):
    actual = counts(items)
    allowed = set(mc.get_categories().ids) | set(mc.SPECIAL_BUCKETS)
    missing = set(mc.get_categories().ids) - set(actual)
    unknown = set(actual) - allowed
    if missing or unknown:
        raise SystemExit("Calendar coverage incomplete: missing identities " +
                         str(sorted(missing)) + "; unknown IDs " + str(sorted(unknown)) +
                         ". Restore the feed list before reviewing. No weekly files written.")
    path = expected_path()
    if confirm:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(actual, indent=2) + "\n")
        return actual
    if not path.exists():
        raise SystemExit("Expected calendars not registered. Review the complete feed list with "
                         "the user, then run moon-weekly --confirm-sources. Do not confirm "
                         "automatically to unblock a review. No weekly files written.")
    expected = json.loads(path.read_text())
    if expected != actual:
        raise SystemExit("Calendar sources changed: expected " + str(expected) +
                         ", configured " + str(actual) + ". Restore missing feeds; confirm "
                         "only an intentional user-approved change. No weekly files written.")
    return actual


def write(week_key, events_path, items, source_results, tz_label):
    evidence = {"week": week_key, "checked_at": datetime.now(timezone.utc).isoformat(),
                "expected_sha256": digest(expected_path().read_bytes()),
                "sources_sha256": signature(items, tz_label),
                "timezone": tz_label,
                "categories_sha256": digest(mc.CATEGORIES_YAML.read_bytes()),
                "events_sha256": digest(events_path.read_bytes()),
                "sources": source_results}
    (events_path.parent / "coverage.json").write_text(json.dumps(evidence, indent=2) + "\n")


def read_valid(week_key, items=None, require_report=False, tz_label=None):
    directory = mc.WEEKS_DIR / week_key
    try:
        evidence = json.loads((directory / "coverage.json").read_text())
        if evidence["week"] != week_key:
            return None
        for key, path in (("expected_sha256", expected_path()),
                          ("categories_sha256", mc.CATEGORIES_YAML),
                          ("events_sha256", directory / "events.json")):
            if evidence[key] != digest(path.read_bytes()):
                return None
        if items is not None:
            validate(items)
            if tz_label is None:
                import ingest
                _, cfg_tz = ingest.configured_sources()
                _, tz_label = mc.resolve_tz(cfg_tz)
            if evidence["sources_sha256"] != signature(items, tz_label):
                return None
        if require_report and evidence.get("report_sha256") != digest((directory / "time-report.md").read_bytes()):
            return None
        return evidence
    except (OSError, ValueError, KeyError):
        return None


def finish_report(week_key, report_path, evidence):
    evidence["report_sha256"] = digest(report_path.read_bytes())
    (report_path.parent / "coverage.json").write_text(json.dumps(evidence, indent=2) + "\n")
