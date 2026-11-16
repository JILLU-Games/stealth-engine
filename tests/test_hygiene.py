"""PH-16 session hygiene tests."""

from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from stealth_engine.config import ProfileConfig
from stealth_engine.engine import BrowserSession, _localstorage_init_script
from stealth_engine.exceptions import AutomationError
from stealth_engine.session import SessionManager


class StorageIsolationAuditTests(unittest.TestCase):
    """Cross-profile storage_state leak audit (N42)."""

    def test_profiles_have_isolated_state_paths(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            s1 = SessionManager(ProfileConfig(
                profile_name="a", user_data_dir=str(base / "a"), seed=1))
            s2 = SessionManager(ProfileConfig(
                profile_name="b", user_data_dir=str(base / "b"), seed=2))
            self.assertNotEqual(s1.storage_state_path, s2.storage_state_path)
            self.assertNotEqual(s1.user_data_dir, s2.user_data_dir)
            # each state file lives under its own profile-named dir
            self.assertTrue(s1.storage_state_path.replace("\\", "/").endswith("/a/storage_state.json"))
            self.assertTrue(s2.storage_state_path.replace("\\", "/").endswith("/b/storage_state.json"))

    def test_export_state_writes_only_own_profile(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            s1 = SessionManager(ProfileConfig(
                profile_name="a", user_data_dir=str(base / "a"), seed=1))
            s2 = SessionManager(ProfileConfig(
                profile_name="b", user_data_dir=str(base / "b"), seed=2))
            s1.ensure_dirs()
            s1.export_state({"cookies": [{"name": "c1"}], "origins": []})
            self.assertTrue(Path(s1.storage_state_path).exists())
            self.assertFalse(Path(s2.storage_state_path).exists())
            # s2 import returns None — no leak
            self.assertIsNone(s2.import_state())

    def test_same_profile_state_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            s = SessionManager(ProfileConfig(
                profile_name="a", user_data_dir=str(Path(d) / "a"), seed=1))
            s.ensure_dirs()
            s.export_state({"cookies": [{"name": "x"}], "origins": []})
            loaded = s.import_state()
            self.assertEqual(loaded["cookies"][0]["name"], "x")


class LocalStorageSeedTests(unittest.TestCase):
    def test_init_script_deterministic_per_seed(self):
        a = _localstorage_init_script(42)
        b = _localstorage_init_script(42)
        c = _localstorage_init_script(43)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertIn("localStorage.setItem", a)

    def test_init_script_handles_none_seed(self):
        js = _localstorage_init_script(None)
        self.assertIn("_sp_id", js)


class _FakePage:
    async def evaluate(self, js):
        return {
            "canvas_hash": "123:abc",
            "webgl_renderer": "ANGLE (Intel)",
            "user_agent": "UA",
            "language": "en-US",
            "languages": ["en-US"],
            "hardware_concurrency": 8,
            "device_memory": 8,
            "max_touch_points": 0,
            "gamepad_count": 0,
            "has_usb": False,
            "has_serial": False,
            "notification_permission": "default",
            "timezone": "America/New_York",
        }


class _FakeCtx:
    def __init__(self):
        self.request = self
        self.last_url = None

    async def get(self, url, timeout=None):
        self.last_url = url
        resp = self
        return resp

    async def all_headers(self):
        return {"Content-Type": "text/html", "Cache-Control": "no-cache"}


def _bs() -> BrowserSession:
    bs = BrowserSession.__new__(BrowserSession)
    bs._rng = random.Random(1)
    return bs


class ProbeTests(unittest.IsolatedAsyncioTestCase):
    async def test_probe_fingerprint_returns_dict(self):
        bs = _bs()
        bs._ctx = _FakeCtx()
        result = await bs.probe_fingerprint(_FakePage())
        self.assertEqual(result["webgl_renderer"], "ANGLE (Intel)")
        self.assertEqual(result["hardware_concurrency"], 8)
        self.assertFalse(result["has_usb"])

    async def test_probe_error_wrapped(self):
        bs = _bs()

        class BadPage:
            async def evaluate(self, js):
                raise RuntimeError("dead")

        with self.assertRaises(AutomationError):
            await bs.probe_fingerprint(BadPage())

    async def test_fetch_headers(self):
        bs = _bs()
        bs._ctx = _FakeCtx()
        headers = await bs.fetch_headers("https://example.com")
        self.assertEqual(headers["content-type"], "text/html")
        self.assertEqual(bs._ctx.last_url, "https://example.com")

    async def test_fetch_headers_error(self):
        bs = _bs()

        class BadCtx:
            class request:
                @staticmethod
                async def get(url, timeout=None):
                    raise RuntimeError("net down")

        bs._ctx = BadCtx()
        with self.assertRaises(AutomationError):
            await bs.fetch_headers("https://x")


if __name__ == "__main__":
    unittest.main()
