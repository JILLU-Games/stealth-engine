"""BF-01 critical-correctness regression tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from stealth_engine.config import ProfileConfig
from stealth_engine.engine import BrowserSession, StealthEngine
from stealth_engine.exceptions import AutomationError
from stealth_engine.session import SessionManager, _pid_alive


class _FakePage:
    pass


class _FakeCtx:
    """Async-shaped fake context — storage_state/close are coroutines."""

    def __init__(self):
        self.pages = []
        self.closed = False
        self.saved_state = None

    def new_page(self):
        return _FakePage()

    async def storage_state(self):
        return {"cookies": [{"name": "c"}], "origins": []}

    async def close(self):
        self.closed = True


class _FakeHandle:
    async def __aexit__(self, *a):
        pass


def _session() -> BrowserSession:
    tmp = tempfile.mkdtemp()
    cfg = ProfileConfig(
        profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=1
    )
    ctx = _FakeCtx()
    s = BrowserSession(
        ctx=ctx,
        ctx_handle=_FakeHandle(),
        session=SessionManager(cfg, base_dir=tmp),
        proxy_manager=None,
        config=cfg,
    )
    return s


class SaveStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_save_state_async_writes_file(self):
        s = _session()
        await s.save_state_async()
        state_path = Path(s._session.profile_dir) / "storage_state.json"
        self.assertTrue(state_path.exists())
        import json

        data = json.loads(state_path.read_text())
        self.assertEqual(data["cookies"][0]["name"], "c")

    async def test_sync_save_state_raises_clear_error(self):
        s = _session()
        with self.assertRaises(AutomationError) as ctx:
            s.save_state()
        self.assertIn("save_state_async", str(ctx.exception))

    async def test_aclose_saves_state(self):
        s = _session()
        await s.aclose()
        state_path = Path(s._session.profile_dir) / "storage_state.json"
        self.assertTrue(state_path.exists())


class PidAliveTests(unittest.TestCase):
    def test_self_pid_alive(self):
        self.assertTrue(_pid_alive(os.getpid()))

    def test_dead_pid_false(self):
        # Very high PID unlikely to exist.
        self.assertFalse(_pid_alive(2**22 + 12345))

    def test_invalid_pid_false(self):
        self.assertFalse(_pid_alive(0))
        self.assertFalse(_pid_alive(-5))

    def test_does_not_kill_caller(self):
        # Regression for B-02: on Windows os.kill(pid,0) would terminate
        # the process — reaching this assertion proves it didn't.
        self.assertTrue(_pid_alive(os.getpid()))


class CloseNoUnawaitedTests(unittest.TestCase):
    def test_close_does_not_call_ctx_close_directly(self):
        """B-03: close() must not invoke the async ctx.close() sync."""
        s = _session()
        # Spy on the coroutine function — if close() called it without
        # await we'd get 'coroutine was never awaited' warnings; the real
        # check is that close() completes via asyncio.run path.
        # We verify by checking _ctx.closed stays False until handle exit
        # (fake handle doesn't close ctx) — the important part is no
        # RuntimeWarning / no direct call.  Use warnings capture.
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                s.close()
            except Exception:
                pass  # ctx_handle fake exit is fine
        never_awaited = [
            x for x in w
            if "never awaited" in str(x.message).lower()
        ]
        self.assertEqual(never_awaited, [])


if __name__ == "__main__":
    unittest.main()


class DomainFilterTests(unittest.TestCase):
    """BF-02/B-04: dot-boundary domain matching."""

    def _export(self, cookies, domains):
        tmp = tempfile.mkdtemp()
        cfg = ProfileConfig(
            profile_name="a", user_data_dir=str(Path(tmp) / "a"), seed=1
        )
        s = SessionManager(cfg, base_dir=tmp)
        s.ensure_dirs()
        s.export_state(
            {"cookies": cookies, "origins": []}, domains=domains
        )
        return s.import_state()["cookies"]

    def test_notexample_com_excluded(self):
        cookies = [
            {"name": "bad", "domain": ".notexample.com"},
            {"name": "good", "domain": ".example.com"},
        ]
        out = self._export(cookies, ["example.com"])
        self.assertEqual([c["name"] for c in out], ["good"])

    def test_xample_com_excluded(self):
        cookies = [{"name": "bad", "domain": ".xample.com"}]
        out = self._export(cookies, ["example.com"])
        self.assertEqual(out, [])

    def test_subdomain_cookie_included(self):
        cookies = [{"name": "c", "domain": ".sub.example.com"}]
        out = self._export(cookies, ["example.com"])
        self.assertEqual(len(out), 1)

    def test_parent_cookie_included_for_subdomain_filter(self):
        # .example.com cookie applies to sub.example.com — semantically
        # correct to include when filtering the subdomain.
        cookies = [{"name": "c", "domain": ".example.com"}]
        out = self._export(cookies, ["sub.example.com"])
        self.assertEqual(len(out), 1)

    def test_empty_domain_excluded(self):
        cookies = [{"name": "c", "domain": ""}]
        out = self._export(cookies, ["example.com"])
        self.assertEqual(out, [])


class ResolveIpUrlTests(unittest.IsolatedAsyncioTestCase):
    async def test_candidates_cover_both_provider_shapes(self):
        from stealth_engine.geo import GeoResolver

        r = GeoResolver(endpoint="https://ipinfo.io/json", cache_ttl_s=0)
        captured = []

        class FakeResp:
            status = 200

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def json(self, content_type=None):
                return {
                    "ip": "1.2.3.4", "country": "US",
                    "timezone": "America/New_York",
                }

        class FakeSession:
            closed = False

            def get(self, url, **kw):
                captured.append(url)
                return FakeResp()

            async def close(self):
                pass

        r._session = FakeSession()
        try:
            await r.resolve_ip("8.8.8.8")
        finally:
            r._session = None
        # First candidate must be ipinfo-style /{ip}/json — and must NOT
        # contain the doubled "/json/{ip}/json" bug.
        self.assertTrue(
            any(u.endswith("/8.8.8.8/json") for u in captured),
            captured,
        )
        self.assertFalse(
            any("/json/8.8.8.8/json" in u for u in captured),
            captured,
        )


class HostIpFallbackTests(unittest.TestCase):
    def test_returns_string_never_raises(self):
        from stealth_engine.engine import StealthEngine

        ip = StealthEngine._resolve_host_ip()
        self.assertIsInstance(ip, str)
        self.assertTrue(ip)


class JsNoiseCanvasTests(unittest.TestCase):
    def test_no_putimagedata_on_live_context(self):
        from stealth_engine.engine import _js_noise_init_script

        js = _js_noise_init_script(3)
        # The live-context variable is `cx`; offscreen is `tctx`.
        self.assertNotIn("cx.putImageData", js)
        self.assertIn("tctx.putImageData", js)
        self.assertIn("drawImage", js)


class MinorFixTests(unittest.TestCase):
    """BF-03 regression coverage."""

    def test_timezone_lowercase_locale(self):
        from stealth_engine.identity import BrowserForgeIdentityProvider

        p = BrowserForgeIdentityProvider()
        self.assertEqual(p._derive_timezone("en-us"), "America/New_York")
        self.assertEqual(p._derive_timezone("FR-fr"), "Europe/Paris")
        self.assertEqual(p._derive_timezone("fr"), "Europe/Paris")

    def test_validate_fingerprint_infers_os_from_ua(self):
        from stealth_engine.identity import validate_fingerprint

        fp = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "viewport": {"width": 1920, "height": 1080},
            "screen": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "platform": "Win32",
            "hardware_concurrency": 8,
            "device_memory": 8,
            "color_scheme": "light",
            "reduced_motion": "no-preference",
            "is_mobile": False,
            "has_touch": False,
        }
        out = validate_fingerprint(fp)
        # No "os" key — coherence check now infers windows from UA and
        # Win32 platform is coherent → no platform/os mismatch issue.
        self.assertFalse(
            any("platform" in i and "os" in i for i in out["issues"]),
            out["issues"],
        )

    def test_js_noise_webgl2_covered(self):
        from stealth_engine.engine import _js_noise_init_script

        js = _js_noise_init_script(7)
        self.assertIn("WebGL2RenderingContext", js)

    def test_geo_cache_key_masked(self):
        from stealth_engine.config import ProxyConfig
        from stealth_engine.proxy import ProxyManager

        pm = ProxyManager(
            [ProxyConfig(server="http://user:secret@proxy.example:8080")]
        )
        key = str(pm.mask(pm._proxies[0])["server"])
        self.assertNotIn("secret", key)
        self.assertNotIn("user", key.split("@")[-1])

    def test_resolve_geo_wraps_unexpected(self):
        import asyncio
        from stealth_engine.config import ProxyConfig
        from stealth_engine.proxy import ProxyManager
        from stealth_engine.exceptions import ProxyError

        async def run():
            pm = ProxyManager(
                [ProxyConfig(server="http://proxy.example:8080")],
                geo_retries=0,
            )

            class BadSession:
                closed = False

                def get(self, *a, **k):
                    raise ValueError("boom")

                async def close(self):
                    pass

            pm._session = BadSession()
            try:
                await pm.resolve_geo(pm._proxies[0])
            finally:
                pm._session = None

        with self.assertRaises(ProxyError):
            asyncio.run(run())


class VerifyStealthShapeTests(unittest.TestCase):
    def test_mismatches_normalized(self):
        # verify_stealth returns structured mismatches — check the code
        # path statically since it needs a live page.
        import inspect
        from stealth_engine.engine import BrowserSession, StealthEngine

        src = inspect.getsource(BrowserSession.verify_stealth)
        self.assertIn('"source": "geo"', src)
        self.assertIn('"source": "fingerprint"', src)
        self.assertIn('"mismatches": mismatches', src)


class BulkRunnerGuardTests(unittest.TestCase):
    def test_run_active_flag_guard(self):
        from stealth_engine.orchestrator import BulkRunner
        from stealth_engine.exceptions import AutomationError
        import asyncio
        import tempfile
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        cfg = ProfileConfig(
            profile_name="g", user_data_dir=str(Path(tmp) / "g"), seed=1
        )
        runner = BulkRunner([cfg], concurrency=1)
        runner._run_active = True

        async def fake(task):
            return None

        with self.assertRaises(AutomationError):
            asyncio.run(runner.run(fake))


class PF03RecordingTests(unittest.TestCase):
    """PF-03/B-33: record_video_dir must fail fast — Playwright video
    recording is Chromium-only and crashes the Firefox driver."""

    def test_record_video_dir_raises_clear_error(self):
        import tempfile, shutil
        from pathlib import Path

        from stealth_engine.exceptions import AutomationError

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        cfg = ProfileConfig(
            profile_name="p",
            user_data_dir=str(Path(tmp) / "p"),
            seed=1,
            record_video_dir="vid",
        )
        engine = StealthEngine(cfg)
        engine._session.ensure_dirs()
        with self.assertRaises(AutomationError) as cm:
            engine._build_launch_kwargs(
                {"locale": "en-US", "timezone_id": "UTC"},
                None,
                {"canvas": 1, "audio": 2, "fonts": 3},
            )
        self.assertIn("record_video_dir", str(cm.exception))

    def test_record_har_path_still_works(self):
        import tempfile, shutil
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        cfg = ProfileConfig(
            profile_name="p",
            user_data_dir=str(Path(tmp) / "p"),
            seed=1,
            record_har_path="rec.har",
        )
        engine = StealthEngine(cfg)
        engine._session.ensure_dirs()
        kwargs = engine._build_launch_kwargs(
            {"locale": "en-US", "timezone_id": "UTC"},
            None,
            {"canvas": 1, "audio": 2, "fonts": 3},
        )
        self.assertIn("record_har_path", kwargs)
