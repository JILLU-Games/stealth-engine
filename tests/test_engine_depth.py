"""PH-19 engine-depth tests (M1-M4)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from stealth_engine.config import ProfileConfig
from stealth_engine.engine import BrowserSession
from stealth_engine.exceptions import AutomationError
from stealth_engine.proxy import GeoInfo

_GOOD_PROBE = {
    "canvas_hash": "100:abc",
    "webgl_renderer": "ANGLE (NVIDIA GeForce RTX 3060)",
    "user_agent": "Mozilla/5.0",
    "language": "en-US",
    "languages": ["en-US", "en"],
    "hardware_concurrency": 8,
    "device_memory": 8,
    "max_touch_points": 0,
    "gamepad_count": 0,
    "has_usb": False,
    "has_serial": False,
    "notification_permission": "default",
    "timezone": "America/New_York",
}


class _FakePage:
    def __init__(self, probe=None):
        self._probe = probe if probe is not None else _GOOD_PROBE

    async def evaluate(self, js):
        return dict(self._probe)


class _FakeCtx:
    def __init__(self, page=None, browser=None, cdp_ok=True):
        self._page = page or _FakePage()
        self.pages = [self._page]
        self.browser = browser
        self._cdp_ok = cdp_ok
        self.routes = []
        self.listeners = {}

    def new_page(self):
        return _FakePage()

    async def new_cdp_session(self, page):
        if not self._cdp_ok:
            raise RuntimeError("CDP not supported")
        return object()

    async def route(self, pattern, handler):
        self.routes.append((pattern, handler))

    def on(self, event, cb):
        self.listeners[event] = cb

    def storage_state(self):
        return {"cookies": [], "origins": []}

    async def close(self):
        pass


class _FakeHandle:
    async def __aexit__(self, *a):
        pass


def _session(ctx=None, **cfg_kw) -> BrowserSession:
    tmp = tempfile.mkdtemp()
    cfg = ProfileConfig(
        profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=1, **cfg_kw
    )
    from stealth_engine.session import SessionManager

    sm = SessionManager(cfg)
    return BrowserSession(
        ctx=ctx or _FakeCtx(),
        ctx_handle=_FakeHandle(),
        session=sm,
        proxy_manager=None,
        config=cfg,
    )


class VerifyStealthTests(unittest.IsolatedAsyncioTestCase):
    async def test_good_probe_low_risk_consistent(self):
        s = _session()
        report = await s.verify_stealth()
        self.assertIn("risk", report)
        self.assertIn("probe", report)
        self.assertTrue(report["consistent"])
        self.assertIn("risk=", report["summary"])

    async def test_swiftshader_makes_inconsistent(self):
        bad = dict(_GOOD_PROBE, webgl_renderer="WebKit WebGL SwiftShader")
        s = _session(_FakeCtx(page=_FakePage(probe=bad)))
        report = await s.verify_stealth()
        self.assertFalse(report["consistent"])
        self.assertEqual(report["risk"]["level"], "high")

    async def test_geo_and_fp_optional(self):
        s = _session()
        geo = GeoInfo(
            ip="1.2.3.4", country="US", timezone_id="America/New_York",
            locale="en-US", currency="USD",
        )
        fp = {
            "user_agent": "Mozilla/5.0",
            "viewport": {"width": 100, "height": 100},
            "screen": {"width": 200, "height": 200},
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "platform": "Win32",
            "os": "windows",
            "hardware_concurrency": 4,
            "device_memory": 8,
        }
        report = await s.verify_stealth(geo=geo, fingerprint=fp)
        self.assertIsNotNone(report["geo"])
        self.assertIsNotNone(report["fp"])


class CdpSessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_session(self):
        s = _session()
        sess = await s.cdp_session(s.page)
        self.assertIsNotNone(sess)

    async def test_unsupported_raises_automation_error(self):
        s = _session(_FakeCtx(cdp_ok=False))
        with self.assertRaises(AutomationError) as ctx:
            await s.cdp_session(s.page)
        self.assertIn("cdp_session", str(ctx.exception))

    async def test_closed_session_raises(self):
        s = _session()
        s._closed = True
        with self.assertRaises(AutomationError):
            await s.cdp_session(s.page)


class _FakeBrowser:
    version = "135.0"

    async def new_context(self, **kw):
        return object()


class NewContextTests(unittest.IsolatedAsyncioTestCase):
    async def test_camoufox_async_new_context_used(self):
        ctx = _FakeCtx(browser=_FakeBrowser())
        s = _session(ctx)
        fake_ctx_obj = object()

        async def fake_async_new_context(browser, **kw):
            return fake_ctx_obj

        import camoufox.async_api as camoufox_async

        with mock.patch.object(
            camoufox_async, "AsyncNewContext", fake_async_new_context
        ):
            result = await s.new_context(os="windows")
        self.assertIs(result, fake_ctx_obj)

    async def test_no_browser_raises(self):
        s = _session(_FakeCtx(browser=None))
        with self.assertRaises(AutomationError):
            await s.new_context()

    async def test_closed_raises(self):
        s = _session(_FakeCtx(browser=_FakeBrowser()))
        s._closed = True
        with self.assertRaises(AutomationError):
            await s.new_context()


class RecordingConfigTests(unittest.TestCase):
    def test_relative_paths_resolve_under_profile_dir(self):
        tmp = tempfile.mkdtemp()
        cfg = ProfileConfig(
            profile_name="p",
            user_data_dir=str(Path(tmp) / "p"),
            seed=1,
            record_har_path="logs/session.har",
            record_har_content="embed",
        )
        from stealth_engine.engine import StealthEngine

        engine = StealthEngine(cfg)
        kwargs = engine._build_launch_kwargs(
            {"locale": "en-US", "viewport": {"width": 1, "height": 1}},
            None,
            seeds={"canvas": 1, "audio": 2, "fonts": 3},
        )
        self.assertIn("record_har_path", kwargs)
        self.assertTrue(kwargs["record_har_path"].endswith("session.har"))
        self.assertIn(str(engine._session.profile_dir).replace("\\", "/"),
                      kwargs["record_har_path"].replace("\\", "/"))
        # PF-03/B-33: record_video_dir is rejected (Chromium-only) —
        # covered by test_bugfix.PF03RecordingTests.
        self.assertEqual(kwargs["record_har_content"], "embed")

    def test_absent_by_default(self):
        tmp = tempfile.mkdtemp()
        cfg = ProfileConfig(
            profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=1
        )
        from stealth_engine.engine import StealthEngine

        engine = StealthEngine(cfg)
        kwargs = engine._build_launch_kwargs(
            {"locale": "en-US"}, None,
            seeds={"canvas": 1, "audio": 2, "fonts": 3},
        )
        self.assertNotIn("record_har_path", kwargs)
        self.assertNotIn("record_video_dir", kwargs)


if __name__ == "__main__":
    unittest.main()
