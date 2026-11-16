"""Focused tests for PH-11 production hardening items."""

from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from stealth_engine import ProfileConfig, ProxyConfig
from stealth_engine.engine import BrowserSession, StealthEngine
from stealth_engine.exceptions import AutomationError, ProxyError
from stealth_engine.orchestrator import BulkRunner, ProfileStatus
from stealth_engine.proxy import GeoInfo, ProxyManager


def _geo(country="US") -> GeoInfo:
    return GeoInfo(
        ip="203.0.113.1", country=country,
        timezone_id="America/New_York", locale="en-US", currency="USD",
    )


_GEO_JSON = {"ip": "203.0.113.1", "country": "US", "timezone": "America/New_York"}


class _FakeResp:
    def __init__(self, payload, status=200):
        self.status = status
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return None

    async def json(self, **kw):
        return self._payload


def _session_get_seq(responses):
    """Session whose .get returns responses in order, recording calls."""
    calls = []
    it = iter(responses)

    def _get(url, **kw):
        calls.append(url)
        return next(it)

    return SimpleNamespace(
        get=Mock(side_effect=_get), closed=False, close=AsyncMock()
    ), calls


class GeoRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolve_geo_retries_then_succeeds(self):
        session, calls = _session_get_seq([
            _FakeResp({}, status=500),
            _FakeResp(_GEO_JSON),
        ])
        manager = ProxyManager(
            [ProxyConfig(server="http://h:1")], geo_retries=2
        )
        manager._session = session
        geo = await manager.resolve_geo(manager._proxies[0])
        self.assertEqual(geo.country, "US")
        self.assertEqual(len(calls), 2)

    async def test_resolve_geo_retries_exhausted_raises(self):
        session, calls = _session_get_seq([
            _FakeResp({}, status=500),
            _FakeResp({}, status=500),
            _FakeResp({}, status=500),
        ])
        manager = ProxyManager(
            [ProxyConfig(server="http://h:1")], geo_retries=2
        )
        manager._session = session
        with self.assertRaises(ProxyError):
            await manager.resolve_geo(manager._proxies[0])
        self.assertEqual(len(calls), 3)  # 1 + 2 retries

    async def test_invalid_retry_and_threshold_rejected(self):
        with self.assertRaises(ProxyError):
            ProxyManager([ProxyConfig(server="http://h:1")], geo_retries=-1)
        with self.assertRaises(ProxyError):
            ProxyManager(
                [ProxyConfig(server="http://h:1")], health_threshold_ms=0
            )

    async def test_health_threshold_filters_slow_proxy(self):
        """pick_healthy uses health_threshold_ms instead of hardcoded 5000."""
        manager = ProxyManager(
            [ProxyConfig(server="http://a:1"), ProxyConfig(server="http://b:2")],
            health_threshold_ms=7000.0,
        )
        manager.resolve_geo = AsyncMock(return_value=_geo("US"))
        # perf_counter: t0=0, after-first=0.001 (1ms ok for first pick attempt)
        # Make every candidate look 6s slow → fails default 5000 but passes 7000.
        ticks = iter([0.0, 6.0, 6.0, 12.0])
        with patch("stealth_engine.proxy.time.perf_counter", side_effect=lambda: next(ticks)):
            proxy, geo = await manager.pick_healthy()
        self.assertIsNotNone(proxy)
        self.assertEqual(geo.country, "US")


class _FakeMouse:
    def __init__(self):
        self.position = {"x": 0, "y": 0}
        self.moves = []
        self.wheels = []

    async def move(self, x, y):
        self.moves.append((x, y))
        self.position = {"x": x, "y": y}

    async def wheel(self, dx, dy):
        self.wheels.append((dx, dy))


class _FakeKeyboard:
    def __init__(self):
        self.typed = []

    async def type(self, char):
        self.typed.append(char)


class _FakePage:
    def __init__(self):
        self.mouse = _FakeMouse()
        self.keyboard = _FakeKeyboard()
        self.clicks = []

    async def click(self, selector):
        self.clicks.append(selector)


class AsyncHumanHookTests(unittest.IsolatedAsyncioTestCase):
    async def test_ahuman_type_types_chars(self):
        import tempfile, shutil
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        cfg = ProfileConfig(
            profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=3
        )
        engine = StealthEngine(cfg)
        bs = BrowserSession.__new__(BrowserSession)
        bs._rng = engine._identity._rng
        from stealth_engine.behavior import BehaviorProfile
        bs._behavior = BehaviorProfile(BehaviorProfile._generate(__import__('random').Random(3)))
        page = _FakePage()
        await bs.ahuman_type(page, "#inp", "hi")
        self.assertEqual("".join(page.keyboard.typed), "hi")
        self.assertEqual(page.clicks, ["#inp"])

    async def test_ahuman_move_and_scroll(self):
        import random
        bs = BrowserSession.__new__(BrowserSession)
        bs._rng = random.Random(1)
        from stealth_engine.behavior import BehaviorProfile
        bs._behavior = BehaviorProfile(BehaviorProfile._generate(random.Random(1)))
        page = _FakePage()
        await bs.ahuman_move(page, 100, 50)
        self.assertEqual(page.mouse.position, {"x": 100, "y": 50})
        await bs.ahuman_scroll(page, 300)
        self.assertTrue(page.mouse.wheels)

    async def test_ahuman_type_error_wrapped(self):
        import random
        bs = BrowserSession.__new__(BrowserSession)
        bs._rng = random.Random(1)
        from stealth_engine.behavior import BehaviorProfile
        bs._behavior = BehaviorProfile(BehaviorProfile._generate(random.Random(1)))

        class BadPage(_FakePage):
            async def click(self, selector):
                raise RuntimeError("boom")

        with self.assertRaises(AutomationError):
            await bs.ahuman_type(BadPage(), "#x", "t")


class _FakeSession:
    def __init__(self):
        self.closed = False

    async def aclose(self):
        self.closed = True


class _FakeEngine:
    def __init__(self, session):
        self._s = session

    async def alaunch(self):
        return self._s


class BulkRunnerTimeoutTests(unittest.IsolatedAsyncioTestCase):
    async def test_task_timeout_marks_failed(self):
        import tempfile, shutil
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        cfg = ProfileConfig(
            profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=1
        )
        session = _FakeSession()

        async def slow_task(sess):
            await asyncio.sleep(10)

        runner = BulkRunner([cfg], concurrency=1, max_attempts=1,
                            task_timeout_s=0.05)
        with patch(
            "stealth_engine.orchestrator.StealthEngine",
            return_value=_FakeEngine(session),
        ):
            results = await runner.run(slow_task)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, ProfileStatus.FAILED)
        self.assertIn("TimeoutError", results[0].error or "")
        self.assertTrue(session.closed)

    async def test_no_timeout_runs_normally(self):
        import tempfile, shutil
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        cfg = ProfileConfig(
            profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=1
        )
        session = _FakeSession()

        async def fast_task(sess):
            await asyncio.sleep(0.01)

        runner = BulkRunner([cfg], concurrency=1, max_attempts=1)
        with patch(
            "stealth_engine.orchestrator.StealthEngine",
            return_value=_FakeEngine(session),
        ):
            results = await runner.run(fast_task)
        self.assertEqual(results[0].status, ProfileStatus.SUCCESS)

    async def test_invalid_timeout_rejected(self):
        import tempfile, shutil
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        cfg = ProfileConfig(
            profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=1
        )
        with self.assertRaises(AutomationError):
            BulkRunner([cfg], task_timeout_s=0)


class ProxySchemeTests(unittest.TestCase):
    def test_socks5h_normalized_to_socks5(self):
        p = ProxyConfig(server="socks5h://user:pw@host:1080")
        self.assertEqual(p.server, "socks5://user:pw@host:1080")

    def test_socks4_accepted(self):
        p = ProxyConfig(server="socks4://host:1080")
        self.assertEqual(p.server, "socks4://host:1080")

    def test_bad_scheme_rejected(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            ProxyConfig(server="ftp://host:21")


class NetworkLeakGuardTests(unittest.TestCase):
    def _kwargs(self, **cfg_kw):
        import tempfile, shutil
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        cfg = ProfileConfig(
            profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=1,
            **cfg_kw,
        )
        engine = StealthEngine(cfg)
        fp = {"locale": "en-US", "timezone_id": "UTC"}
        seeds = {"canvas": 1, "audio": 2, "fonts": 3}
        proxy = cfg_kw.get("proxy")
        return engine._build_launch_kwargs(fp, proxy, seeds)

    def test_disable_ipv6_sets_pref(self):
        kwargs = self._kwargs(disable_ipv6=True)
        self.assertEqual(
            kwargs["firefox_user_prefs"]["network.dns.disableIPv6"], True
        )

    def test_socks_proxy_sets_remote_dns(self):
        kwargs = self._kwargs(proxy=ProxyConfig(server="socks5://h:1080"))
        self.assertEqual(
            kwargs["firefox_user_prefs"]["network.proxy.socks_remote_dns"], True
        )

    def test_http_proxy_no_remote_dns_pref(self):
        kwargs = self._kwargs(proxy=ProxyConfig(server="http://h:8080"))
        self.assertNotIn("firefox_user_prefs", kwargs)

    def test_remote_dns_disabled_by_config(self):
        kwargs = self._kwargs(
            proxy=ProxyConfig(server="socks5://h:1080"), proxy_remote_dns=False
        )
        self.assertNotIn("firefox_user_prefs", kwargs)

    def test_no_prefs_by_default(self):
        kwargs = self._kwargs()
        self.assertNotIn("firefox_user_prefs", kwargs)


class FingerprintDepthTests(unittest.TestCase):
    def _kwargs(self, **cfg_kw):
        import tempfile, shutil
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        cfg = ProfileConfig(
            profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=1,
            **cfg_kw,
        )
        engine = StealthEngine(cfg)
        fp = {"locale": "en-US", "timezone_id": "UTC"}
        seeds = {"canvas": 1, "audio": 2, "fonts": 3}
        return engine._build_launch_kwargs(fp, None, seeds)

    def test_webgl_config_passed(self):
        kwargs = self._kwargs(webgl_config=("Google Inc.", "ANGLE"))
        self.assertEqual(kwargs["webgl_config"], ("Google Inc.", "ANGLE"))

    def test_fonts_and_custom_only(self):
        kwargs = self._kwargs(fonts=["Arial", "Times"], custom_fonts_only=True)
        self.assertEqual(kwargs["fonts"], ["Arial", "Times"])
        self.assertTrue(kwargs["custom_fonts_only"])

    def test_screen_bounds_builds_screen_obj(self):
        kwargs = self._kwargs(screen_bounds=(1920, 2560, 1080, 1440))
        screen = kwargs["screen"]
        self.assertEqual(screen.min_width, 1920)
        self.assertEqual(screen.max_width, 2560)
        self.assertEqual(screen.min_height, 1080)
        self.assertEqual(screen.max_height, 1440)

    def test_hardware_concurrency_in_config(self):
        kwargs = self._kwargs(hardware_concurrency=8)
        self.assertEqual(kwargs["config"]["navigator.hardwareConcurrency"], 8)

    def test_hardware_concurrency_merges_with_timezone(self):
        kwargs = self._kwargs(hardware_concurrency=4)
        self.assertIn("timezone", kwargs["config"])
        self.assertEqual(kwargs["config"]["navigator.hardwareConcurrency"], 4)

    def test_no_fingerprint_kwargs_by_default(self):
        kwargs = self._kwargs()
        for key in ("webgl_config", "fonts", "screen", "custom_fonts_only"):
            self.assertNotIn(key, kwargs)
        # PF-01/B-27: config dict always carries camoufox patch seeds;
        # assert the timezone entry specifically.
        self.assertEqual(kwargs["config"]["timezone"], "UTC")
        self.assertEqual(kwargs["config"]["canvas:seed"], 1)
        self.assertEqual(kwargs["config"]["audio:seed"], 2)
        self.assertEqual(kwargs["config"]["fonts:spacing_seed"], 3)

    def test_bad_webgl_config_rejected(self):
        from pydantic import ValidationError
        import tempfile, shutil
        from pathlib import Path
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        with self.assertRaises(ValidationError):
            ProfileConfig(
                profile_name="p",
                user_data_dir=str(Path(tmp) / "p"),
                webgl_config=("only-one",),  # type: ignore[arg-type]
            )


class AttachFileTests(unittest.IsolatedAsyncioTestCase):
    async def test_attach_file_success(self):
        import random
        from stealth_engine.engine import BrowserSession
        bs = BrowserSession.__new__(BrowserSession)
        bs._rng = random.Random(1)
        calls = []

        class P:
            async def set_input_files(self, sel, path):
                calls.append((sel, path))

        await bs.attach_file(P(), "#f", "/tmp/a.txt")
        self.assertEqual(calls, [("#f", "/tmp/a.txt")])

    async def test_attach_file_error_wrapped(self):
        import random
        from stealth_engine.engine import BrowserSession
        bs = BrowserSession.__new__(BrowserSession)
        bs._rng = random.Random(1)

        class P:
            async def set_input_files(self, sel, path):
                raise RuntimeError("no input")

        with self.assertRaises(AutomationError):
            await bs.attach_file(P(), "#f", "/x")


class ModeATimezoneTests(unittest.TestCase):
    def test_launch_kwargs_config_timezone_when_geoip_false(self):
        import tempfile, shutil
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        cfg = ProfileConfig(
            profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=1
        )
        engine = StealthEngine(cfg)
        fp = {"locale": "en-US", "timezone_id": "America/New_York"}
        seeds = {"canvas": 1, "audio": 2, "fonts": 3}
        kwargs = engine._build_launch_kwargs(fp, None, seeds)
        self.assertEqual(kwargs.get("geoip"), False)
        self.assertEqual(kwargs["config"]["timezone"], "America/New_York")

    def test_no_config_timezone_when_geoip_true(self):
        import tempfile, shutil
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        cfg = ProfileConfig(
            profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=1,
            proxy=ProxyConfig(server="http://h:1"), geoip=True,
        )
        engine = StealthEngine(cfg)
        engine._resolve_host_ip = lambda: "203.0.113.9"
        fp = {"locale": "en-US", "timezone_id": "America/New_York"}
        seeds = {"canvas": 1, "audio": 2, "fonts": 3}
        kwargs = engine._build_launch_kwargs(
            fp, ProxyConfig(server="http://h:1"), seeds
        )
        self.assertEqual(kwargs.get("geoip"), True)
        # PF-01: config dict always present (seed keys); only the
        # timezone/webrtc overrides are geoip-gated.
        self.assertNotIn("timezone", kwargs.get("config", {}))
        self.assertNotIn("webrtc:ipv4", kwargs.get("config", {}))


if __name__ == "__main__":
    unittest.main()
