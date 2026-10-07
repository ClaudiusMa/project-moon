#!/usr/bin/env python3
"""Calendar completeness regressions. Uses only temporary local fixtures."""
import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import coverage
import ingest
import engine
import moon_common as mc

loader = importlib.machinery.SourceFileLoader("weekly", str(Path(__file__).with_name("moon-weekly")))
spec = importlib.util.spec_from_loader(loader.name, loader)
weekly = importlib.util.module_from_spec(spec)
loader.exec_module(weekly)


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.patches = [patch.object(mc, "ASTRONAUT_DIR", self.root / "Astronaut"),
                        patch.object(mc, "WEEKS_DIR", self.root / "weeks"),
                        patch.object(mc, "TRENDS_CSV", self.root / "trends.csv")]
        for p in self.patches:
            p.start()
        self.ics = self.root / "empty.ics"
        self.ics.write_text("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Moon Test//EN\r\nEND:VCALENDAR\r\n")
        self.feeds = self.root / "rocket.md"
        self.items = [(cid, str(self.ics)) for cid in mc.get_categories().ids]
        self.items += [("trash_time", str(self.ics)), ("invisible", str(self.ics))]
        self.write_feeds(self.items)
        self.weekdir = mc.WEEKS_DIR / "2026-W40"
        self.weekdir.mkdir(parents=True)
        for name in ("events.json", "time-report.md", "coverage.json", "reflection.md", "coaching.md"):
            (self.weekdir / name).write_text("sentinel")
        mc.TRENDS_CSV.write_text("sentinel")
        self.before = self.snapshot()
        coverage.validate(self.items, confirm=True)

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def write_feeds(self, items):
        self.feeds.write_text("- timezone: America/Los_Angeles\n" + "\n".join(f"- {cid}: {src}" for cid, src in items))

    def snapshot(self):
        return {str(p): p.read_bytes() for p in [*self.weekdir.iterdir(), mc.TRENDS_CSV]}

    def run_week(self):
        weekly.main(["--week", "2026-W40", "--feeds", str(self.feeds)])

    def assert_blocked(self):
        with self.assertRaises(SystemExit):
            self.run_week()
        self.assertEqual(self.before, self.snapshot())

    def test_original_placeholder_failure_preserves_week(self):
        self.write_feeds([(cid, "<secret URL>") for cid in mc.get_categories().ids] + [("invisible", str(self.ics))])
        self.assert_blocked()

    def test_direct_ingestion_also_blocks_incomplete_sources(self):
        self.write_feeds([("invisible", str(self.ics))])
        with self.assertRaises(SystemExit):
            ingest.main(["--week", "2026-W40", "--feeds", str(self.feeds)])
        self.assertEqual(self.before, self.snapshot())

    def test_check_coverage_is_read_only_and_refuses_old_report(self):
        with self.assertRaises(SystemExit):
            weekly.main(["--week", "2026-W40", "--feeds", str(self.feeds), "--check-coverage"])
        self.assertEqual(self.before, self.snapshot())

    def test_missing_trash_preserves_week(self):
        self.write_feeds([(cid, src) for cid, src in self.items if cid != "trash_time"])
        self.assert_blocked()

    def test_missing_one_of_multiple_invisible_sources(self):
        coverage.validate(self.items + [("invisible", str(self.ics))], confirm=True)
        self.assert_blocked()

    def test_missing_manifest_does_not_auto_register(self):
        coverage.expected_path().unlink()
        self.assert_blocked()
        self.assertFalse(coverage.expected_path().exists())

    def test_fetch_failure_preserves_week_and_hides_source(self):
        self.write_feeds([(cid, "/missing/secret-calendar.ics" if cid == "trash_time" else src) for cid, src in self.items])
        with self.assertRaises(SystemExit) as error:
            self.run_week()
        self.assertNotIn("secret-calendar", str(error.exception))
        self.assertEqual(self.before, self.snapshot())

    def test_malformed_calendar_preserves_week(self):
        self.ics.write_text("this is not an iCalendar")
        self.assert_blocked()

    def test_empty_success_is_verified_and_personal_records_preserved(self):
        mc.TRENDS_CSV.unlink()
        self.run_week()
        self.assertTrue(coverage.read_valid("2026-W40", self.items, require_report=True, tz_label="America/Los_Angeles"))
        self.assertIn("| trash_time | fetched | 0 |", (self.weekdir / "time-report.md").read_text())
        self.assertEqual("sentinel", (self.weekdir / "reflection.md").read_text())
        self.assertEqual("sentinel", (self.weekdir / "coaching.md").read_text())
        weekly.main(["--week", "2026-W40", "--feeds", str(self.feeds), "--check-coverage"])
        for filename in ("events.json", "time-report.md"):
            p = self.weekdir / filename
            original = p.read_bytes()
            p.write_bytes(original + b" ")
            self.assertIsNone(coverage.read_valid("2026-W40", self.items, require_report=True, tz_label="America/Los_Angeles"))
            p.write_bytes(original)
        changed = [(cid, src + "-changed") for cid, src in self.items]
        self.assertIsNone(coverage.read_valid("2026-W40", changed, require_report=True, tz_label="America/Los_Angeles"))

    def test_timezone_change_requires_fresh_pull(self):
        mc.TRENDS_CSV.unlink()
        self.run_week()
        self.feeds.write_text(self.feeds.read_text().replace("America/Los_Angeles", "UTC"))
        before = self.snapshot()
        with self.assertRaises(SystemExit):
            weekly.main(["--week", "2026-W40", "--feeds", str(self.feeds), "--check-coverage"])
        self.assertEqual(before, self.snapshot())

    def test_timezone_override_matches_only_same_effective_timezone(self):
        mc.TRENDS_CSV.unlink()
        args = ["--week", "2026-W40", "--feeds", str(self.feeds)]
        weekly.main(args + ["--timezone", "UTC"])
        weekly.main(args + ["--timezone", "UTC", "--check-coverage"])
        with self.assertRaises(SystemExit):
            weekly.main(args + ["--check-coverage"])
        engine.run("2026-W40", verbose=False, source_items=self.items, tz_name="America/Los_Angeles")
        self.assertIn("calendar_coverage: unverified", (self.weekdir / "time-report.md").read_text())

    def test_sample_is_unverified(self):
        mc.TRENDS_CSV.unlink()
        coverage.expected_path().unlink()
        ingest.run("2026-W40", self.feeds, verified=False, verbose=False)
        engine.run("2026-W40", verbose=False)
        self.assertIn("calendar_coverage: unverified", (self.weekdir / "time-report.md").read_text())
        self.assertIsNone(coverage.read_valid("2026-W40", require_report=True))

    def test_initial_confirmation_cannot_bless_incomplete_identities(self):
        coverage.expected_path().unlink()
        with self.assertRaises(SystemExit):
            coverage.validate([("invisible", str(self.ics))], confirm=True)
        self.assertFalse(coverage.expected_path().exists())


if __name__ == "__main__":
    unittest.main()
