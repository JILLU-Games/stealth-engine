"""PH-18 practical UX pack tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from stealth_engine import (
    GeoDriftMonitor,
    StickyGeoStore,
    load_proxies,
    preset_names,
    validate_fingerprint,
)
from stealth_engine.config import ProfileConfig
from stealth_engine.exceptions import ConfigError, ProxyError
from stealth_engine.proxy import GeoInfo
from stealth_engine.session import SessionManager


class ProxyFileImportTests(unittest.TestCase):
    def _write(self, content: str) -> str:
        f = tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        )
        f.write(content)
        f.close()
        self.addCleanup(lambda: Path(f.name).unlink(missing_ok=True))
        return f.name

    def test_host_port_user_pass_format(self):
        path = self._write("1.2.3.4:8080:user1:pass1\n")
        proxies = load_proxies(path)
        self.assertEqual(len(proxies), 1)
        self.assertIn("1.2.3.4:8080", proxies[0].server)
        self.assertIn("user1", proxies[0].server)

    def test_url_format(self):
        path = self._write("http://u:p@h:3128\nsocks5://h2:1080\n")
        proxies = load_proxies(path)
        self.assertEqual(len(proxies), 2)
        self.assertTrue(proxies[1].server.startswith("socks5://"))

    def test_comments_and_blanks_skipped(self):
        path = self._write("# comment\n\n1.2.3.4:80\n   \n")
        self.assertEqual(len(load_proxies(path)), 1)

    def test_bad_line_reports_line_number(self):
        path = self._write("1.2.3.4:80\nbogus line here\n")
        with self.assertRaises(ProxyError) as ctx:
            load_proxies(path)
        self.assertIn("line 2", str(ctx.exception))

    def test_missing_file_raises(self):
        with self.assertRaises(ProxyError):
            load_proxies("C:/nonexistent/proxies.txt")

    def test_empty_file_raises(self):
        path = self._write("# only comments\n")
        with self.assertRaises(ProxyError):
            load_proxies(path)


_GOOD_FP = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "viewport": {"width": 1920, "height": 1080},
    "screen": {"width": 1920, "height": 1080},
    "locale": "en-US",
    "timezone_id": "America/New_York",
    "platform": "Win32",
    "os": "windows",
    "hardware_concurrency": 8,
    "device_memory": 8,
}


class FingerprintValidatorTests(unittest.TestCase):
    def test_good_fp_consistent(self):
        result = validate_fingerprint(_GOOD_FP)
        self.assertTrue(result["consistent"])
        self.assertEqual(result["score"], 100)

    def test_missing_keys_flagged(self):
        result = validate_fingerprint({"user_agent": "x"})
        self.assertFalse(result["consistent"])
        self.assertTrue(any("user_agent" not in i for i in result["issues"]))

    def test_viewport_exceeds_screen_flagged(self):
        fp = dict(_GOOD_FP, viewport={"width": 2560, "height": 1440})
        result = validate_fingerprint(fp)
        self.assertTrue(any("exceeds screen" in i for i in result["issues"]))

    def test_bad_timezone_flagged(self):
        result = validate_fingerprint(dict(_GOOD_FP, timezone_id="Not/AZone"))
        self.assertTrue(any("timezone" in i for i in result["issues"]))

    def test_os_mismatch_flagged(self):
        fp = dict(_GOOD_FP, os="macos")
        result = validate_fingerprint(fp)
        self.assertTrue(result["issues"])


class StickyGeoStoreTests(unittest.TestCase):
    def test_put_get_remove_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            store = StickyGeoStore(str(Path(d) / "bind.json"))
            geo = GeoInfo(
                ip="1.2.3.4", country="US", timezone_id="America/New_York",
                locale="en-US", currency="USD",
            )
            store.put("acct1", "http://p:1", geo)
            self.assertIsNotNone(store.get("acct1"))
            self.assertEqual(store.get("acct1")["proxy"], "http://p:1")
            self.assertTrue(store.remove("acct1"))
            self.assertIsNone(store.get("acct1"))

    def test_persistence_across_instances(self):
        with tempfile.TemporaryDirectory() as d:
            p = str(Path(d) / "bind.json")
            s1 = StickyGeoStore(p)
            s1.put("a", "http://x", {"country": "DE"})
            s2 = StickyGeoStore(p)
            self.assertEqual(s2.get("a")["geo"]["country"], "DE")


class GeoDriftMonitorTests(unittest.TestCase):
    def _geo(self, country="US", tz="America/New_York", city=None):
        return GeoInfo(
            ip="1.2.3.4", country=country, timezone_id=tz,
            locale="en-US", currency="USD", city=city,
        )

    def test_first_seen_no_drift(self):
        m = GeoDriftMonitor()
        r = m.check("t1", self._geo())
        self.assertTrue(r["first_seen"])
        self.assertFalse(r["drifted"])

    def test_drift_detected_on_change(self):
        m = GeoDriftMonitor()
        m.check("t1", self._geo())
        r = m.check("t1", self._geo(country="DE", tz="Europe/Berlin"))
        self.assertTrue(r["drifted"])
        self.assertIn("country", r["changes"])

    def test_no_drift_same_geo(self):
        m = GeoDriftMonitor()
        m.check("t1", self._geo())
        r = m.check("t1", self._geo())
        self.assertFalse(r["drifted"])

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            p = str(Path(d) / "drift.json")
            m1 = GeoDriftMonitor(store_path=p)
            m1.check("t", self._geo())
            m2 = GeoDriftMonitor(store_path=p)
            r = m2.check("t", self._geo(country="FR"))
            self.assertTrue(r["drifted"])


class PresetTests(unittest.TestCase):
    def test_preset_names(self):
        self.assertIn("us-desktop", preset_names())

    def test_preset_builds_config(self):
        c = ProfileConfig.preset(
            "us-desktop", profile_name="x",
            user_data_dir="./profiles/x",
        )
        self.assertEqual(c.os, "windows")
        self.assertEqual(c.locale, "en-US")

    def test_unknown_preset_raises(self):
        with self.assertRaises(ConfigError):
            ProfileConfig.preset("nope", profile_name="x", user_data_dir="./x")

    def test_override_wins(self):
        c = ProfileConfig.preset(
            "us-desktop", profile_name="x", user_data_dir="./x",
            headless=False,
        )
        self.assertFalse(c.headless)


class SelectiveExportTests(unittest.TestCase):
    def test_domain_filter(self):
        with tempfile.TemporaryDirectory() as d:
            s = SessionManager(ProfileConfig(
                profile_name="a", user_data_dir=str(Path(d) / "a"), seed=1))
            s.ensure_dirs()
            state = {
                "cookies": [
                    {"name": "c1", "domain": ".example.com"},
                    {"name": "c2", "domain": ".other.com"},
                ],
                "origins": [
                    {"origin": "https://example.com", "localStorage": []},
                    {"origin": "https://other.com", "localStorage": []},
                ],
            }
            s.export_state(state, domains=["example.com"])
            loaded = s.import_state()
            self.assertEqual(len(loaded["cookies"]), 1)
            self.assertEqual(loaded["cookies"][0]["name"], "c1")
            self.assertEqual(len(loaded["origins"]), 1)

    def test_no_filter_exports_all(self):
        with tempfile.TemporaryDirectory() as d:
            s = SessionManager(ProfileConfig(
                profile_name="a", user_data_dir=str(Path(d) / "a"), seed=1))
            s.ensure_dirs()
            state = {"cookies": [{"name": "c", "domain": ".x.com"}],
                     "origins": []}
            s.export_state(state)
            loaded = s.import_state()
            self.assertEqual(len(loaded["cookies"]), 1)


if __name__ == "__main__":
    unittest.main()
