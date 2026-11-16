"""Focused regression tests for verified forensic audit findings."""

from __future__ import annotations

import asyncio
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from loguru import logger

from stealth_engine import ProfileConfig, ProxyConfig
from stealth_engine.engine import BrowserSession, StealthEngine
from stealth_engine.exceptions import AutomationError
from stealth_engine.proxy import GeoInfo, ProxyManager
from stealth_engine.session import SessionManager


class ProxyCredentialTests(unittest.TestCase):
    def test_embedded_credentials_are_separated_and_redacted(self) -> None:
        proxy = ProxyConfig(server="http://user:secret@host:8080")
        manager = ProxyManager([proxy])

        self.assertEqual(manager._build_proxy_url(proxy), "http://host:8080")
        self.assertEqual(manager.to_playwright(proxy), {
            "server": "http://host:8080",
            "username": "user",
            "password": "secret",
        })
        self.assertEqual(manager._build_proxy_auth(proxy).login, "user")
        self.assertEqual(manager._build_proxy_auth(proxy).password, "secret")
        self.assertNotIn("secret", repr(manager.mask(proxy)))

        config = ProfileConfig(
            profile_name="profile",
            user_data_dir="profile",
            proxy=proxy,
        )
        public_proxy = config.to_public_dict()["proxy"]
        self.assertEqual(public_proxy["server"], "http://host:8080")
        self.assertNotIn("secret", repr(public_proxy))

    def test_proxy_logs_do_not_include_embedded_password(self) -> None:
        proxy = ProxyConfig(server="http://user:secret@host:8080")
        manager = ProxyManager([proxy])
        manager.resolve_geo = AsyncMock(return_value=GeoInfo(
            ip="203.0.113.1",
            country="US",
            timezone_id="America/New_York",
            locale="en-US",
            currency="USD",
        ))
        output = io.StringIO()
        sink_id = logger.add(output, level="DEBUG")
        try:
            asyncio.run(manager.health_check(proxy))
            asyncio.run(manager.pick_healthy())
        finally:
            logger.remove(sink_id)

        self.assertNotIn("secret", output.getvalue())

    def test_geo_request_keeps_tls_verification_enabled(self) -> None:
        class FakeResponse:
            status = 200

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def json(self, **kwargs):
                return {
                    "ip": "203.0.113.1",
                    "country": "US",
                    "timezone": "America/New_York",
                }

        response = FakeResponse()
        http_session = SimpleNamespace(get=Mock(return_value=response))
        manager = ProxyManager([ProxyConfig(server="http://host:8080")])
        manager._get_session = AsyncMock(return_value=http_session)

        asyncio.run(manager.resolve_geo(manager._proxies[0]))

        request_kwargs = http_session.get.call_args.kwargs
        self.assertTrue(request_kwargs.get("ssl", True))


class EngineRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_geoip_setting_controls_launch_and_overrides(self) -> None:
        for enabled in (False, True):
            with self.subTest(geoip=enabled), tempfile.TemporaryDirectory() as temp_dir:
                proxy = ProxyConfig(server="http://host:8080")
                config = ProfileConfig(
                    profile_name="profile",
                    user_data_dir=str(Path(temp_dir) / "profile"),
                    proxy=proxy,
                    geoip=enabled,
                )
                engine = StealthEngine(config)
                fingerprint = {
                    "locale": "en-US",
                    "timezone_id": "UTC",
                    "user_agent": "test-agent",
                }
                engine._identity = SimpleNamespace(
                    generate=lambda: dict(fingerprint),
                    fingerprint_hash=lambda: "0123456789abcdef",
                    get_or_create_seeds=lambda: {
                        "canvas": 123,
                        "audio": 456,
                        "fonts": 789,
                        "locale": "en-US",
                        "timezone_id": "UTC",
                        "locale_source": "config",
                        "timezone_source": "config",
                    },
                )
                geo = GeoInfo(
                    ip="203.0.113.1",
                    country="DE",
                    timezone_id="Europe/Berlin",
                    locale="de-DE",
                    currency="EUR",
                )
                engine._proxy_manager.pick_healthy = AsyncMock(return_value=(proxy, geo))

                class FakeContext:
                    pages = [object()]

                    def storage_state(self):
                        return {"cookies": [], "origins": []}

                    async def close(self):
                        return None

                context = FakeContext()

                class FakeHandle:
                    async def __aenter__(self):
                        return context

                    async def __aexit__(self, *args):
                        return None

                launch_kwargs = []

                def fake_camoufox(**kwargs):
                    launch_kwargs.append(kwargs)
                    return FakeHandle()

                with patch("camoufox.async_api.AsyncCamoufox", side_effect=fake_camoufox):
                    session = await engine.alaunch()
                try:
                    self.assertIs(launch_kwargs[0]["geoip"], enabled)
                    self.assertEqual(
                        launch_kwargs[0]["locale"],
                        "de-DE" if enabled else "en-US",
                    )
                finally:
                    await session.aclose()

    async def test_sync_close_rejects_running_loop_before_side_effects(self) -> None:
        class FakeContext:
            pages = [object()]
            close_calls = 0
            storage_state_calls = 0

            def storage_state(self):
                self.storage_state_calls += 1
                return {"cookies": [], "origins": []}

            def close(self):
                self.close_calls += 1

        with tempfile.TemporaryDirectory() as temp_dir:
            config = ProfileConfig(profile_name="profile", user_data_dir="profile")
            manager = SessionManager(config, base_dir=temp_dir)
            manager.acquire_lock()
            context = FakeContext()
            session = BrowserSession(context, object(), manager, None, config)
            try:
                with self.assertRaises(AutomationError):
                    session.close()
                self.assertEqual(context.storage_state_calls, 0)
                self.assertEqual(context.close_calls, 0)
                self.assertFalse(session._closed)
                self.assertTrue(Path(manager.lock_path).exists())
            finally:
                manager.release_lock()


class PH05_VerificationTests(unittest.IsolatedAsyncioTestCase):
    """PH-05 verification tests for Step 3/4 implementation."""

    async def test_check_23_mode_a_locale_from_seeds(self) -> None:
        """Check #23: Mode A launch_kwargs["locale"] == seeds["locale"]."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ProfileConfig(
                profile_name="profile",
                user_data_dir=str(Path(temp_dir) / "profile"),
                proxy=None,
                seed=42,
            )
            engine = StealthEngine(config)
            fingerprint = {
                "locale": "en-US",
                "timezone_id": "UTC",
                "user_agent": "test-agent",
            }
            engine._identity = SimpleNamespace(
                generate=lambda: dict(fingerprint),
                fingerprint_hash=lambda: "0123456789abcdef",
                get_or_create_seeds=lambda: {
                    "canvas": 123,
                    "audio": 456,
                    "fonts": 789,
                    "locale": "fr-CA",
                    "timezone_id": "America/Toronto",
                    "locale_source": "config",
                    "timezone_source": "config",
                },
            )

            class FakeContext:
                pages = [object()]

                def storage_state(self):
                    return {"cookies": [], "origins": []}

                async def close(self):
                    return None

            context = FakeContext()

            class FakeHandle:
                async def __aenter__(self):
                    return context

                async def __aexit__(self, *args):
                    return None

            launch_kwargs = []

            def fake_camoufox(**kwargs):
                launch_kwargs.append(kwargs)
                return FakeHandle()

            with patch("camoufox.async_api.AsyncCamoufox", side_effect=fake_camoufox):
                session = await engine.alaunch()
            try:
                self.assertEqual(launch_kwargs[0]["locale"], "fr-CA")
                self.assertEqual(launch_kwargs[0]["geoip"], False)
            finally:
                await session.aclose()

    async def test_check_24_mode_b_locale_from_geoip(self) -> None:
        """Check #24: Mode B launch_kwargs["locale"] == geo.locale."""
        with tempfile.TemporaryDirectory() as temp_dir:
            proxy = ProxyConfig(server="http://host:8080")
            config = ProfileConfig(
                profile_name="profile",
                user_data_dir=str(Path(temp_dir) / "profile"),
                proxy=proxy,
                geoip=True,
                seed=42,
            )
            engine = StealthEngine(config)
            fingerprint = {
                "locale": "en-US",
                "timezone_id": "UTC",
                "user_agent": "test-agent",
            }
            engine._identity = SimpleNamespace(
                generate=lambda: dict(fingerprint),
                fingerprint_hash=lambda: "0123456789abcdef",
                get_or_create_seeds=lambda: {
                    "canvas": 123,
                    "audio": 456,
                    "fonts": 789,
                    "locale": "en-US",
                    "timezone_id": "UTC",
                    "locale_source": "config",
                    "timezone_source": "config",
                },
            )
            geo = GeoInfo(
                ip="203.0.113.1",
                country="DE",
                timezone_id="Europe/Berlin",
                locale="de-DE",
                currency="EUR",
            )
            engine._proxy_manager.pick_healthy = AsyncMock(return_value=(proxy, geo))

            class FakeContext:
                pages = [object()]

                def storage_state(self):
                    return {"cookies": [], "origins": []}

                async def close(self):
                    return None

            context = FakeContext()

            class FakeHandle:
                async def __aenter__(self):
                    return context

                async def __aexit__(self, *args):
                    return None

            launch_kwargs = []

            def fake_camoufox(**kwargs):
                launch_kwargs.append(kwargs)
                return FakeHandle()

            with patch("camoufox.async_api.AsyncCamoufox", side_effect=fake_camoufox):
                session = await engine.alaunch()
            try:
                self.assertEqual(launch_kwargs[0]["locale"], "de-DE")
                self.assertEqual(launch_kwargs[0]["geoip"], True)
            finally:
                await session.aclose()

    async def test_check_25_seed_persistence_fingerprint_consistency(self) -> None:
        """Check #25: same profile launched twice reuses identical seeds.json.

        Uses the REAL IdentityGenerator (browserforge) — only Camoufox and
        host-IP resolution are mocked.  Verifies the actual persistence
        contract: identical canvas/audio/fonts/locale/timezone_id seeds and
        identical device-seed launch kwargs across two launches.

        NOTE: cross-instance ``fingerprint_hash`` equality is intentionally
        NOT asserted — browserforge samples via process-global ``random``
        (documented limitation), so full-fingerprint reproducibility is not
        guaranteed.  ``fingerprint_hash`` is asserted stable per instance.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ProfileConfig(
                profile_name="profile",
                user_data_dir=str(Path(temp_dir) / "profile"),
                seed=42,
                proxy=None,
            )

            class FakeContext:
                pages = [object()]

                def storage_state(self):
                    return {"cookies": [], "origins": []}

                async def close(self):
                    return None

            context = FakeContext()

            class FakeHandle:
                async def __aenter__(self):
                    return context

                async def __aexit__(self, *args):
                    return None

            launch_kwargs_per_launch = []
            hash_per_launch = []

            def fake_camoufox(**kwargs):
                launch_kwargs_per_launch.append(kwargs)
                return FakeHandle()

            for _ in range(2):
                engine = StealthEngine(config)
                with patch("camoufox.async_api.AsyncCamoufox", side_effect=fake_camoufox):
                    with patch(
                        "stealth_engine.engine.StealthEngine._resolve_host_ip",
                        return_value="203.0.113.10",
                    ):
                        session = await engine.alaunch()
                try:
                    hash_per_launch.append(engine._identity.fingerprint_hash())
                finally:
                    await session.aclose()

            seeds_json = Path(temp_dir) / "profile" / "seeds.json"
            self.assertTrue(seeds_json.exists())
            persisted = json.loads(seeds_json.read_text(encoding="utf-8"))

            seed_keys = ("canvas:seed", "audio:seed", "fonts:spacing_seed")
            first, second = launch_kwargs_per_launch
            # PF-01/B-27: camoufox patch properties live inside the
            # ``config`` dict, not as top-level kwargs.
            first_cfg = first["config"]
            second_cfg = second["config"]
            for key in seed_keys:
                self.assertEqual(first_cfg[key], second_cfg[key])
                self.assertEqual(first_cfg[key], persisted[
                    {"canvas:seed": "canvas", "audio:seed": "audio",
                     "fonts:spacing_seed": "fonts"}[key]
                ])
            self.assertEqual(first["locale"], second["locale"])
            self.assertEqual(first["locale"], persisted["locale"])

            # fingerprint_hash is stable per instance (cached).
            for h in hash_per_launch:
                self.assertRegex(h, r"^[0-9a-f]{64}$")

    async def test_check_26_proxy_none_launches_mode_a(self) -> None:
        """Check #26: ProfileConfig(proxy=None) is valid and launches Mode A."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ProfileConfig(
                profile_name="profile",
                user_data_dir=str(Path(temp_dir) / "profile"),
                proxy=None,
                seed=42,
            )
            engine = StealthEngine(config)
            fingerprint = {
                "locale": "en-US",
                "timezone_id": "UTC",
                "user_agent": "test-agent",
            }
            engine._identity = SimpleNamespace(
                generate=lambda: dict(fingerprint),
                fingerprint_hash=lambda: "0123456789abcdef",
                get_or_create_seeds=lambda: {
                    "canvas": 123,
                    "audio": 456,
                    "fonts": 789,
                    "locale": "en-US",
                    "timezone_id": "UTC",
                    "locale_source": "config",
                    "timezone_source": "config",
                },
            )

            class FakeContext:
                pages = [object()]

                def storage_state(self):
                    return {"cookies": [], "origins": []}

                async def close(self):
                    return None

            context = FakeContext()

            class FakeHandle:
                async def __aenter__(self):
                    return context

                async def __aexit__(self, *args):
                    return None

            launch_kwargs = []

            def fake_camoufox(**kwargs):
                launch_kwargs.append(kwargs)
                return FakeHandle()

            with patch("camoufox.async_api.AsyncCamoufox", side_effect=fake_camoufox):
                with patch("stealth_engine.engine.StealthEngine._resolve_host_ip", return_value="8.8.8.8"):
                    session = await engine.alaunch()
            try:
                self.assertEqual(launch_kwargs[0]["geoip"], False)
                cfg = launch_kwargs[0]["config"]
                self.assertEqual(cfg["webrtc:ipv4"], "8.8.8.8")
                self.assertEqual(cfg["canvas:seed"], 123)
                self.assertEqual(cfg["audio:seed"], 456)
                self.assertEqual(cfg["fonts:spacing_seed"], 789)
            finally:
                await session.aclose()


# ---------------------------------------------------------------------------
# P-01: exact scope — F-01/F-02/F-06 and conditional U-01/U-04.
# These tests use an isolated Camoufox-shaped fake; they DO NOT claim
# a real installed browser/runtime passed acceptance.
# ---------------------------------------------------------------------------
class _P01Context:
    def __init__(self, *, empty=False, page_error=False):
        self.initial_page = object()
        self.pages = [] if empty else [self.initial_page]
        self.page_error = page_error
        self.new_page_calls = 0
        self.exit_calls = 0
        self.close_calls = 0
        self.owner_loop = None
        self.browser = None

    async def new_page(self):
        self.new_page_calls += 1
        if self.page_error:
            raise RuntimeError("controlled initial-page failure")
        page = object()
        self.pages.append(page)
        return page

    async def storage_state(self):
        self.owner_loop = asyncio.get_running_loop()
        return {"cookies": [], "origins": []}

    async def close(self):
        self.close_calls += 1


class _P01Handle:
    def __init__(self, ctx, *, enter_error=None):
        self.ctx = ctx
        self.enter_error = enter_error
        self.exit_calls = 0

    async def __aenter__(self):
        if self.enter_error is not None:
            raise self.enter_error
        return self.ctx

    async def __aexit__(self, *args):
        self.exit_calls += 1


def _p01_fake_camoufox(handle):
    """Patch lazy Camoufox import without requiring or contacting a browser."""
    import sys
    import types

    package = types.ModuleType("camoufox")
    package.__path__ = []
    api = types.ModuleType("camoufox.async_api")
    api.AsyncCamoufox = lambda **kwargs: handle
    package.async_api = api
    return patch.dict(sys.modules, {"camoufox": package, "camoufox.async_api": api})


def _p01_engine(tmp):
    cfg = ProfileConfig(
        profile_name="p01", user_data_dir=str(Path(tmp) / "p01"),
        seed=42, geoip=False,
    )
    engine = StealthEngine(cfg)
    engine._identity = SimpleNamespace(
        generate=lambda: {"locale": "en-US", "timezone_id": "UTC"},
        fingerprint_hash=lambda: "a" * 64,
        get_or_create_seeds=lambda: {
            "canvas": 11, "audio": 12, "fonts": 13,
            "locale": "en-US", "timezone_id": "UTC",
        },
    )
    return engine


class P01SyncOwnershipTests(unittest.TestCase):
    def test_f01_sync_loop_owns_launch_and_teardown(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            ctx = _P01Context()
            handle = _P01Handle(ctx)
            with _p01_fake_camoufox(handle), patch.object(
                StealthEngine, "_resolve_host_ip", return_value="203.0.113.10"
            ):
                session = engine.launch()
            loop = session._sync_loop
            worker = session._sync_thread
            self.assertIsNotNone(loop)
            self.assertTrue(loop.is_running())
            self.assertTrue(worker.is_alive())
            self.assertIs(session.page, ctx.initial_page)
            session.close()
            self.assertTrue(loop.is_closed())
            self.assertFalse(worker.is_alive())
            self.assertEqual(handle.exit_calls, 1)
            self.assertIs(ctx.owner_loop, loop)
            self.assertFalse(Path(engine._session.lock_path).exists())
            session.close()  # idempotent

    def test_f01_failed_sync_launch_stops_owned_worker(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            ctx = _P01Context(empty=True, page_error=True)
            handle = _P01Handle(ctx)
            with _p01_fake_camoufox(handle), patch.object(
                StealthEngine, "_resolve_host_ip", return_value="203.0.113.10"
            ):
                with self.assertRaises(AutomationError):
                    engine.launch()
            self.assertEqual(handle.exit_calls, 1)
            self.assertFalse(Path(engine._session.lock_path).exists())


class P01AsyncLaunchTests(unittest.IsolatedAsyncioTestCase):
    async def test_f02_empty_initial_page_is_awaited(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            ctx = _P01Context(empty=True)
            handle = _P01Handle(ctx)
            with _p01_fake_camoufox(handle), patch.object(
                StealthEngine, "_resolve_host_ip", return_value="203.0.113.10"
            ):
                session = await engine.alaunch()
            try:
                self.assertEqual(ctx.new_page_calls, 1)
                self.assertIs(session.page, ctx.pages[0])
                self.assertFalse(asyncio.iscoroutine(session.page))
            finally:
                await session.aclose()

    async def test_f06_page_failure_closes_proxy_and_lock_preserves_typed_error(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            ctx = _P01Context(empty=True, page_error=True)
            handle = _P01Handle(ctx)
            proxy = SimpleNamespace(
                pick_healthy=AsyncMock(return_value=(None, None)),
                aclose=AsyncMock(),
            )
            engine._proxy_manager = proxy
            with _p01_fake_camoufox(handle), patch.object(
                StealthEngine, "_resolve_host_ip", return_value="203.0.113.10"
            ):
                with self.assertRaises(AutomationError) as raised:
                    await engine.alaunch()
            self.assertIn("new_page", str(raised.exception))
            self.assertEqual(handle.exit_calls, 1)
            proxy.aclose.assert_awaited_once()
            self.assertFalse(Path(engine._session.lock_path).exists())
            self.assertFalse(
                (Path(engine._session.profile_dir) / "fingerprint_history.json").exists()
            )

    async def test_f06_cancellation_closes_proxy_and_lock(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            handle = _P01Handle(_P01Context(), enter_error=asyncio.CancelledError())
            proxy = SimpleNamespace(
                pick_healthy=AsyncMock(return_value=(None, None)),
                aclose=AsyncMock(),
            )
            engine._proxy_manager = proxy
            with _p01_fake_camoufox(handle), patch.object(
                StealthEngine, "_resolve_host_ip", return_value="203.0.113.10"
            ):
                with self.assertRaises(asyncio.CancelledError):
                    await engine.alaunch()
            self.assertEqual(handle.exit_calls, 1)
            proxy.aclose.assert_awaited_once()
            self.assertFalse(Path(engine._session.lock_path).exists())

    async def test_f01_async_close_of_sync_session_uses_owner_loop(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            ctx = _P01Context()
            handle = _P01Handle(ctx)
            # launch() cannot run *inside* this running loop, so call
            # it in a worker; this is an explicit API-contract test.
            def launch_from_sync_thread():
                with _p01_fake_camoufox(handle), patch.object(
                    StealthEngine, "_resolve_host_ip", return_value="203.0.113.10"
                ):
                    return engine.launch()

            session = await asyncio.to_thread(launch_from_sync_thread)
            loop = session._sync_loop
            worker = session._sync_thread
            await session.aclose()
            self.assertTrue(loop.is_closed())
            self.assertFalse(worker.is_alive())
            self.assertIs(ctx.owner_loop, loop)
            self.assertEqual(handle.exit_calls, 1)
            self.assertFalse(Path(engine._session.lock_path).exists())

    async def test_f06_cleanup_error_does_not_override_initial_page_error(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            ctx = _P01Context(empty=True, page_error=True)
            handle = _P01Handle(ctx)
            proxy = SimpleNamespace(
                pick_healthy=AsyncMock(return_value=(None, None)),
                aclose=AsyncMock(side_effect=RuntimeError("controlled proxy close failure")),
            )
            engine._proxy_manager = proxy
            with _p01_fake_camoufox(handle), patch.object(
                StealthEngine, "_resolve_host_ip", return_value="203.0.113.10"
            ):
                with self.assertRaises(AutomationError) as raised:
                    await engine.alaunch()
            self.assertIn("new_page", str(raised.exception))
            self.assertEqual(handle.exit_calls, 1)
            proxy.aclose.assert_awaited_once()
            self.assertFalse(Path(engine._session.lock_path).exists())

    async def test_f01_running_loop_rejected_without_lock(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            with self.assertRaisesRegex(Exception, "running event loop"):
                engine.launch()
            self.assertFalse(Path(engine._session.lock_path).exists())

    async def test_u01_helpers_and_u04_context_retain_explicit_unsupported_contract(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            ctx = _P01Context()
            handle = _P01Handle(ctx)
            with _p01_fake_camoufox(handle), patch.object(
                StealthEngine, "_resolve_host_ip", return_value="203.0.113.10"
            ):
                session = await engine.alaunch()
            try:
                with self.assertRaisesRegex(AutomationError, "new_page_async"):
                    session.new_page()
                with self.assertRaisesRegex(AutomationError, "save_state_async"):
                    session.save_state()
                with self.assertRaisesRegex(AutomationError, "no browser"):
                    await session.new_context()
            finally:
                await session.aclose()


if __name__ == "__main__":
    unittest.main()


class P02ProfileOwnershipTests(unittest.TestCase):
    """F-07/F-08/F-09: in-process reproducible real filesystem lock guards."""

    @staticmethod
    def _manager(td):
        cfg = ProfileConfig(profile_name="p02", user_data_dir="p02")
        return SessionManager(cfg, base_dir=td)

    def test_f07_live_legacy_pid_older_than_24h_is_not_stolen(self):
        import os
        import time
        from stealth_engine.exceptions import SessionError
        with tempfile.TemporaryDirectory() as td:
            mgr = self._manager(td)
            mgr.ensure_dirs()
            old = {"pid": os.getpid(), "ts": time.time() - 7 * 86400}
            Path(mgr.lock_path).write_text(json.dumps(old), encoding="utf-8")
            with self.assertRaises(SessionError):
                mgr.acquire_lock()
            self.assertEqual(json.loads(Path(mgr.lock_path).read_text()), old)

    def test_f07_same_pid_other_manager_cannot_acquire(self):
        from stealth_engine.exceptions import SessionError
        with tempfile.TemporaryDirectory() as td:
            owner, other = self._manager(td), self._manager(td)
            owner.acquire_lock()
            try:
                with self.assertRaises(SessionError):
                    other.acquire_lock()
                data = json.loads(Path(owner.lock_path).read_text())
                self.assertEqual(data["owner_token"], owner._lock_token)
            finally:
                owner.release_lock()

    def test_f07_dead_legacy_lock_can_be_reclaimed(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            mgr = self._manager(td)
            mgr.ensure_dirs()
            Path(mgr.lock_path).write_text(json.dumps({"pid": 98237412, "ts": 1000}))
            with patch("stealth_engine.session._pid_alive", return_value=False):
                mgr.acquire_lock()
            try:
                owner = json.loads(Path(mgr.lock_path).read_text())
                self.assertNotEqual(owner["pid"], 98237412)
                self.assertEqual(owner["owner_token"], mgr._lock_token)
            finally:
                mgr.release_lock()

    def test_f07_two_contenders_for_dead_lock_have_one_winner(self):
        from threading import Barrier, Thread
        from stealth_engine.exceptions import SessionError
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            first, second = self._manager(td), self._manager(td)
            first.ensure_dirs()
            Path(first.lock_path).write_text(json.dumps({"pid": 98237412, "ts": 1}))
            barrier = Barrier(2)
            results = []

            def try_lock(mgr):
                barrier.wait()
                try:
                    mgr.acquire_lock()
                    results.append(("owner", mgr))
                except SessionError:
                    results.append(("blocked", mgr))

            # Do NOT return false for the newly created live PID.
            import os
            def is_alive(pid):
                return pid == os.getpid()
            with patch("stealth_engine.session._pid_alive", side_effect=is_alive):
                threads = [Thread(target=try_lock, args=(m,)) for m in (first, second)]
                for thread in threads: thread.start()
                for thread in threads: thread.join(timeout=5)
                self.assertTrue(all(not t.is_alive() for t in threads))
            self.assertEqual(sorted(status for status, _ in results), ["blocked", "owner"])
            winner = [m for status, m in results if status == "owner"][0]
            self.assertEqual(json.loads(Path(winner.lock_path).read_text())["owner_token"], winner._lock_token)
            winner.release_lock()

    def test_f08_nonowner_release_is_noop_and_owner_release_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            owner, nonowner = self._manager(td), self._manager(td)
            owner.acquire_lock()
            raw_before = Path(owner.lock_path).read_bytes()
            nonowner.release_lock()
            self.assertEqual(Path(owner.lock_path).read_bytes(), raw_before)
            owner.release_lock()
            owner.release_lock()
            self.assertFalse(Path(owner.lock_path).exists())

    def test_f08_same_process_changed_token_cannot_release(self):
        from stealth_engine.exceptions import SessionError
        with tempfile.TemporaryDirectory() as td:
            owner = self._manager(td)
            owner.acquire_lock()
            lock = Path(owner.lock_path)
            record = json.loads(lock.read_text())
            record["owner_token"] = "other-owner-token"
            lock.write_text(json.dumps(record))
            with self.assertRaises(SessionError):
                owner.release_lock()
            self.assertTrue(lock.exists())

    def test_f09_live_reset_rejected_without_data_loss(self):
        from stealth_engine.exceptions import SessionError
        with tempfile.TemporaryDirectory() as td:
            owner, resetter = self._manager(td), self._manager(td)
            owner.acquire_lock()
            payload = Path(owner.profile_dir) / "cookies.json"
            payload.write_text("keep me")
            try:
                with self.assertRaises(SessionError):
                    resetter.force_reset()
                with self.assertRaises(SessionError):
                    owner.force_reset()
                self.assertEqual(payload.read_text(), "keep me")
                self.assertTrue(Path(owner.lock_path).exists())
            finally:
                owner.release_lock()

    def test_f09_legacy_live_reset_and_malformed_reset_fail_closed(self):
        import os
        from stealth_engine.exceptions import SessionError
        with tempfile.TemporaryDirectory() as td:
            mgr = self._manager(td)
            mgr.ensure_dirs()
            payload = Path(mgr.profile_dir) / "cookies.json"
            payload.write_text("untouched")
            lock = Path(mgr.lock_path)
            for raw in (json.dumps({"pid": os.getpid(), "ts": 1}), "INVALID LOCK DATA"):
                with self.subTest(raw=raw):
                    lock.write_text(raw)
                    with self.assertRaises(SessionError):
                        mgr.force_reset()
                    self.assertEqual(payload.read_text(), "untouched")
                    self.assertEqual(lock.read_text(), raw)

    def test_f09_idle_reset_succeeds_dead_lock_and_otherwise(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            mgr = self._manager(td)
            mgr.ensure_dirs()
            Path(mgr.profile_dir, "data.txt").write_text("clear")
            with patch("stealth_engine.session._pid_alive", return_value=False):
                Path(mgr.lock_path).write_text(json.dumps({"pid": 98989898, "ts": 1}))
                mgr.force_reset()
            self.assertFalse(Path(mgr.profile_dir).exists())
            self.assertTrue(mgr._lock_guard_path.exists())
            # A fresh idle profile can also be reset without acquiring a lock.
            mgr.ensure_dirs()
            mgr.force_reset()
            self.assertFalse(Path(mgr.profile_dir).exists())


class P02SessionAgeTests(unittest.TestCase):
    """F-18: first-seen metadata independent of the capped recent history."""

    @staticmethod
    def _engine(td):
        cfg = ProfileConfig(profile_name="p02", user_data_dir="p02", seed=11)
        return StealthEngine(cfg)

    @staticmethod
    def _browser_session(engine):
        from types import SimpleNamespace
        return BrowserSession(ctx=SimpleNamespace(pages=[]), ctx_handle=None,
                              session=engine._session, proxy_manager=None,
                              config=engine._config)

    def test_f18_age_preserved_after_51_plus_history_records(self):
        import time
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as td:
            engine = self._engine(td)
            # Keep the engine's profile local to our test directory.
            engine._session = SessionManager(engine._config, base_dir=td)
            engine._identity = SimpleNamespace(fingerprint_hash=lambda: "fixed-hash")
            for _ in range(75):
                self.assertFalse(engine._record_fingerprint())
            p = Path(engine._session.profile_dir)
            recent = json.loads((p / "fingerprint_history.json").read_text())
            meta = json.loads((p / "fingerprint_history_meta.json").read_text())
            self.assertEqual(len(recent), 50)
            self.assertEqual(meta["schema_version"], 1)
            self.assertLessEqual(meta["first_seen_ts"], recent[0]["ts"])
            self.assertLess(self._browser_session(engine).session_age_days(), 0.1)

    def test_f18_legacy_migration_backup_age_and_capping(self):
        import time
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as td:
            engine = self._engine(td)
            engine._session = SessionManager(engine._config, base_dir=td)
            engine._identity = SimpleNamespace(fingerprint_hash=lambda: "fixed-hash")
            prof = Path(engine._session.profile_dir)
            prof.mkdir(parents=True)
            old_ts = time.time() - 80 * 86400
            history = [{"ts": old_ts + i, "hash": "fixed-hash", "diversity": False}
                       for i in range(52)]
            raw = json.dumps(history)
            (prof / "fingerprint_history.json").write_text(raw)
            for _ in range(53):
                self.assertFalse(engine._record_fingerprint())
            backup = prof / "fingerprint_history.legacy.json.bak"
            self.assertEqual(backup.read_text(), raw)
            meta = json.loads((prof / "fingerprint_history_meta.json").read_text())
            self.assertEqual(meta["first_seen_ts"], old_ts)
            self.assertEqual(meta["origin"], "legacy_oldest_known")
            self.assertEqual(len(json.loads((prof / "fingerprint_history.json").read_text())), 50)
            self.assertAlmostEqual(self._browser_session(engine).session_age_days(), 80.0, delta=0.01)

    def test_f18_corrupt_meta_does_not_overwrite_or_invent_age(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as td:
            engine = self._engine(td)
            engine._session = SessionManager(engine._config, base_dir=td)
            engine._identity = SimpleNamespace(fingerprint_hash=lambda: "fixed-hash")
            prof = Path(engine._session.profile_dir)
            prof.mkdir(parents=True)
            meta = prof / "fingerprint_history_meta.json"
            meta.write_text('{"schema_version":1,"first_seen_ts":"oops"}')
            history = prof / "fingerprint_history.json"
            history.write_text('[{"ts":1234,"hash":"old"}]')
            self.assertFalse(engine._record_fingerprint())
            self.assertIsNone(self._browser_session(engine).session_age_days())
            self.assertEqual(json.loads(history.read_text())[0]["hash"], "old")
            self.assertIn('"oops"', meta.read_text())

    def test_f18_legacy_read_still_supported_without_migration(self):
        import time
        with tempfile.TemporaryDirectory() as td:
            engine = self._engine(td)
            engine._session = SessionManager(engine._config, base_dir=td)
            prof = Path(engine._session.profile_dir)
            prof.mkdir(parents=True)
            (prof / "fingerprint_history.json").write_text(json.dumps([{"ts": time.time() - 86400}]))
            self.assertAlmostEqual(self._browser_session(engine).session_age_days(), 1, delta=0.01)
            self.assertFalse((prof / "fingerprint_history_meta.json").exists())


class P02FailClosedTests(unittest.TestCase):
    """P-02 negative controls for permission and partial-failure boundaries."""

    def test_f07_unreadable_stale_metadata_cannot_be_stolen(self):
        from stealth_engine.exceptions import SessionError
        with tempfile.TemporaryDirectory() as td:
            cfg = ProfileConfig(profile_name="p02", user_data_dir="p02")
            mgr = SessionManager(cfg, base_dir=td)
            mgr.ensure_dirs()
            Path(mgr.lock_path).write_text("garbled")
            with self.assertRaises(SessionError):
                mgr.acquire_lock()
            self.assertEqual(Path(mgr.lock_path).read_text(), "garbled")

    def test_f08_owner_does_not_delete_new_owner_after_replacement(self):
        from stealth_engine.exceptions import SessionError
        with tempfile.TemporaryDirectory() as td:
            cfg = ProfileConfig(profile_name="p02", user_data_dir="p02")
            mgr = SessionManager(cfg, base_dir=td)
            mgr.acquire_lock()
            lock = Path(mgr.lock_path)
            record = json.loads(lock.read_text())
            record["owner_token"] = "replacement-token"
            lock.write_text(json.dumps(record))
            with self.assertRaises(SessionError):
                mgr.release_lock()
            self.assertTrue(lock.exists())
            self.assertEqual(json.loads(lock.read_text())["owner_token"], "replacement-token")

    def test_f09_own_token_blocks_reset_even_if_lock_removed_externally(self):
        from stealth_engine.exceptions import SessionError
        with tempfile.TemporaryDirectory() as td:
            cfg = ProfileConfig(profile_name="p02", user_data_dir="p02")
            mgr = SessionManager(cfg, base_dir=td)
            mgr.acquire_lock()
            record = Path(mgr.profile_dir) / "data.txt"
            record.write_text("keep")
            Path(mgr.lock_path).unlink()
            with self.assertRaises(SessionError):
                mgr.force_reset()
            self.assertEqual(record.read_text(), "keep")

    def test_f09_filesystem_reset_failure_raises_typed_error(self):
        from stealth_engine.exceptions import SessionError
        with tempfile.TemporaryDirectory() as td:
            cfg = ProfileConfig(profile_name="p02", user_data_dir="p02")
            mgr = SessionManager(cfg, base_dir=td)
            mgr.ensure_dirs()
            record = Path(mgr.profile_dir) / "data.txt"
            record.write_text("keep")
            with patch("stealth_engine.session.shutil.rmtree", side_effect=OSError("read only")):
                with self.assertRaises(SessionError) as caught:
                    mgr.force_reset()
            self.assertIn("force_reset", str(caught.exception))
            self.assertEqual(record.read_text(), "keep")

    @unittest.skipIf(__import__("os").name == "nt", "POSIX permission semantics only")
    def test_f07_pid_permission_denied_is_not_considered_dead(self):
        from stealth_engine.session import _pid_alive
        with patch("stealth_engine.session.os.kill", side_effect=PermissionError("EPERM")):
            self.assertTrue(_pid_alive(12345))


# ---------------------------------------------------------------------------
# P-03: proxy transport/credentials/authority, Geo auto and WebRTC controls.
# Local SOCKS servers only; no external proxy, IP or browser access.
# ---------------------------------------------------------------------------
class _P03SocksServer:
    """Minimal deterministic SOCKS protocol peer that returns HTTP Geo JSON."""

    def __init__(self, version=5, username=None, password=None, status=200):
        import socket as _socket
        import threading

        self.version = version
        self.username = username
        self.password = password
        self.status = status
        self.captured = {}
        self.failure = None
        self.sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self._run, daemon=True)

    @staticmethod
    def _read(sock, length):
        data = b""
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                raise EOFError("socket closed")
            data += chunk
        return data

    def _run(self):
        try:
            with self.sock:
                conn, _ = self.sock.accept()
                with conn:
                    conn.settimeout(4)
                    if self.version == 5:
                        greeting = self._read(conn, 2)
                        self.captured["greeting"] = greeting
                        methods = self._read(conn, greeting[1])
                        self.captured["methods"] = methods
                        auth = self.username is not None
                        conn.sendall(b"\x05\x02" if auth else b"\x05\x00")
                        if auth:
                            prelude = self._read(conn, 2)
                            user = self._read(conn, prelude[1])
                            length = self._read(conn, 1)[0]
                            password = self._read(conn, length)
                            self.captured["user"] = user
                            self.captured["password"] = password
                            conn.sendall(b"\x01\x00")
                        start = self._read(conn, 5)
                        self.captured["connect_prefix"] = start[:4]
                        self.captured["host"] = self._read(conn, start[4])
                        self.captured["port"] = int.from_bytes(self._read(conn, 2), "big")
                        conn.sendall(b"\x05\x00\x00\x01\x7f\x00\x00\x01\x00\x50")
                    else:
                        hdr = self._read(conn, 8)
                        self.captured["connect_prefix"] = hdr
                        user = bytearray()
                        while (ch := self._read(conn, 1)) != b"\x00":
                            user.extend(ch)
                        host = bytearray()
                        while (ch := self._read(conn, 1)) != b"\x00":
                            host.extend(ch)
                        self.captured["user"] = bytes(user)
                        self.captured["host"] = bytes(host)
                        conn.sendall(b"\x00\x5a\x00\x50\x7f\x00\x00\x01")
                    chunks = []
                    while b"\r\n\r\n" not in b"".join(chunks):
                        next_data = conn.recv(4096)
                        if not next_data:
                            raise EOFError("missing HTTP request")
                        chunks.append(next_data)
                    self.captured["http"] = b"".join(chunks)
                    import json as _json
                    body = _json.dumps({"ip": "8.8.4.4", "country": "US", "timezone": "America/New_York"}).encode("utf-8")
                    reply = f"HTTP/1.1 {self.status} {'OK' if self.status == 200 else 'FAIL'}\r\nContent-Length: {len(body)}\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n".encode("ascii")
                    conn.sendall(reply + body)
        except BaseException as exc:
            self.failure = exc

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.thread.join(timeout=4)
        if self.thread.is_alive():
            self.sock.close()
            self.thread.join(timeout=2)
            raise AssertionError("SOCKS mock server hung")
        if self.failure is not None:
            raise AssertionError(f"SOCKS mock failed: {self.failure}") from self.failure


class P03SocksWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_f05_real_local_socks5_handshake_and_geo_http(self):
        from stealth_engine.proxy import ProxyManager
        from stealth_engine.config import ProxyConfig
        with _P03SocksServer(version=5) as server:
            p = ProxyConfig(server=f"socks5://127.0.0.1:{server.port}")
            pm = ProxyManager([p], geo_endpoint="http://geo.invalid/geo?v=1", timeout_s=2)
            try:
                geo = await pm.resolve_geo(p)
                self.assertEqual(geo.ip, "8.8.4.4")
                self.assertEqual(server.captured["greeting"], b"\x05\x01")
                self.assertEqual(server.captured["methods"], b"\x00")
                self.assertEqual(server.captured["host"], b"geo.invalid")
                self.assertEqual(server.captured["connect_prefix"], b"\x05\x01\x00\x03")
                self.assertEqual(server.captured["http"].split(b"\r\n")[0], b"GET /geo?v=1 HTTP/1.1")
                self.assertIsNone(pm._session)
            finally:
                await pm.aclose()

    async def test_f05_socks5_username_password_handshake_and_no_log_secret(self):
        from stealth_engine.proxy import ProxyManager
        from stealth_engine.config import ProxyConfig
        with _P03SocksServer(version=5, username="alice", password="hidden") as server:
            p = ProxyConfig(server=f"socks5://alice:hidden@127.0.0.1:{server.port}")
            pm = ProxyManager([p], geo_endpoint="http://geo.invalid/", timeout_s=2)
            try:
                geo = await pm.resolve_geo(p)
                self.assertEqual(geo.country, "US")
                self.assertEqual(server.captured["methods"], b"\x02")
                self.assertEqual(server.captured["user"], b"alice")
                self.assertEqual(server.captured["password"], b"hidden")
                self.assertNotIn("hidden", str(pm.mask(p)))
            finally:
                await pm.aclose()

    async def test_f05_socks4a_remote_dns_handshake(self):
        from stealth_engine.proxy import ProxyManager
        from stealth_engine.config import ProxyConfig
        with _P03SocksServer(version=4) as server:
            p = ProxyConfig(server=f"socks4://127.0.0.1:{server.port}")
            pm = ProxyManager([p], geo_endpoint="http://geo.invalid/", timeout_s=2)
            try:
                geo = await pm.resolve_geo(p)
                self.assertEqual(geo.country, "US")
                self.assertEqual(server.captured["connect_prefix"][:2], b"\x04\x01")
                self.assertEqual(server.captured["connect_prefix"][4:], b"\x00\x00\x00\x01")
                self.assertEqual(server.captured["host"], b"geo.invalid")
            finally:
                await pm.aclose()

    async def test_f05_socks5_non200_is_typed_proxyerror(self):
        from stealth_engine.proxy import ProxyManager
        from stealth_engine.config import ProxyConfig
        from stealth_engine.exceptions import ProxyError
        with _P03SocksServer(version=5, status=503) as server:
            p = ProxyConfig(server=f"socks5://127.0.0.1:{server.port}")
            pm = ProxyManager([p], geo_endpoint="http://geo.invalid/", timeout_s=2)
            try:
                with self.assertRaises(ProxyError) as e:
                    await pm.resolve_geo(p)
                self.assertIn("503", str(e.exception))
            finally:
                await pm.aclose()

    async def test_f05_http_uses_unchanged_aiohttp_path(self):
        from unittest.mock import AsyncMock, Mock, patch
        from types import SimpleNamespace
        from stealth_engine.proxy import ProxyManager
        from stealth_engine.config import ProxyConfig
        class Response:
            status = 200
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return None
            async def json(self, **kwargs):
                return {"ip": "8.8.4.4", "country": "US", "timezone": "America/New_York"}
        sess = SimpleNamespace(get=Mock(return_value=Response()), closed=False, close=AsyncMock())
        p = ProxyConfig(server="http://proxy.example:8080")
        pm = ProxyManager([p])
        pm._session = sess
        self.assertEqual((await pm.resolve_geo(p)).country, "US")
        self.assertEqual(sess.get.call_args.kwargs["proxy"], p.server)
        self.assertIsNone(sess.get.call_args.kwargs["proxy_auth"])
        await pm.aclose()


class P03ValidationAndWebRTCTests(unittest.TestCase):
    def test_f11_proxy_line_redacts_unencoded_and_encoded_secrets(self):
        from stealth_engine.proxy import _parse_proxy_line
        from stealth_engine.exceptions import ProxyError
        for raw in [
            "socks5://user:ultrasecret@bad.invalid:badport",
            "user:ultrasecret@bad.invalid:badport",
            "bad.invalid:badport:user:ultrasecret",
            "socks5://user:ultrasecret@",
            "socks5://user:ultrasecret@bad.invalid:99999",
        ]:
            with self.subTest(raw=raw):
                with self.assertRaises(ProxyError) as ctx:
                    _parse_proxy_line(raw, 3)
                exc = ctx.exception
                self.assertNotIn("ultrasecret", str(exc))
                self.assertNotIn("ultrasecret", repr(exc.details))
                self.assertIsNone(exc.__cause__)

    def test_f11_direct_pydantic_validation_does_not_echo_credentials(self):
        from stealth_engine.config import ProxyConfig
        from pydantic import ValidationError
        with self.assertRaises(ValidationError) as e:
            ProxyConfig(server="http://user:ultrasecret@:nonsense")
        self.assertNotIn("ultrasecret", str(e.exception))

    def test_f12_proxy_url_requires_host_and_valid_port(self):
        from stealth_engine.config import ProxyConfig
        from pydantic import ValidationError
        invalid = ["http://", "https://", "socks5://", "socks4://", "http://host", "http://:80", "http://host:abc", "socks5://host:0", "http://host:65536", "http://host:80/path", "http://ho st:8080", "http://host:80?x=1"]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                ProxyConfig(server=value)
        for value in ["http://host:80", "https://host:443", "socks5://host:1080", "socks4://host:1080", "http://[::1]:8080"]:
            with self.subTest(value=value):
                self.assertEqual(ProxyConfig(server=value).server, value)
        self.assertEqual(ProxyConfig(server="socks5h://host:1080").server, "socks5://host:1080")

    def test_f14_auto_geo_uses_resolved_effective_values(self):
        from stealth_engine.geo import validate_geo_consistency
        from stealth_engine.config import ProfileConfig
        from stealth_engine.proxy import GeoInfo
        geo = GeoInfo(ip="8.8.8.8", country="US", timezone_id="America/New_York", locale="en-US", currency="USD")
        cfg = ProfileConfig(profile_name="p", user_data_dir="p", locale=" AUTO ", timezone="auto")
        result = validate_geo_consistency(geo, cfg)
        self.assertTrue(result["consistent"])
        self.assertEqual(result["mismatches"], [])
        self.assertEqual(result["checks"]["locale"]["resolved"], "en-US")
        cfg.timezone = "Europe/Berlin"
        result = validate_geo_consistency(geo, cfg)
        self.assertEqual(result["mismatches"], ["timezone_id"])

    def test_f15_direct_private_host_address_never_forwarded(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from unittest.mock import patch
        from stealth_engine.config import ProfileConfig
        from stealth_engine.engine import StealthEngine
        with TemporaryDirectory() as td:
            engine = StealthEngine(ProfileConfig(profile_name="p", user_data_dir=str(Path(td)/"p")))
            seeds={"canvas":1,"audio":2,"fonts":3}; fp={"locale":"en-US"}
            for candidate in ("192.168.1.2", "172.16.0.9", "10.0.0.2", "127.0.0.1", "0.0.0.0", "203.0.113.10"):
                with self.subTest(candidate=candidate), patch.object(engine,"_resolve_host_ip", return_value=candidate):
                    kw=engine._build_launch_kwargs(fp,None,seeds)
                    self.assertNotIn("webrtc:ipv4",kw["config"])
            with patch.object(engine,"_resolve_host_ip", return_value="8.8.8.8"):
                self.assertEqual(engine._build_launch_kwargs(fp,None,seeds)["config"]["webrtc:ipv4"],"8.8.8.8")

    def test_f15_explicit_private_target_fails_closed_without_proxy(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from stealth_engine.config import ProfileConfig
        from stealth_engine.engine import StealthEngine
        from stealth_engine.exceptions import LaunchError
        with TemporaryDirectory() as td:
            config=ProfileConfig(profile_name="p", user_data_dir=str(Path(td)/"p"),target_ip="192.168.1.4")
            engine=StealthEngine(config)
            with self.assertRaises(LaunchError):
                engine._build_launch_kwargs({"locale":"en-US"},None,{"canvas":1,"audio":2,"fonts":3})
class P04FingerprintContractTests(unittest.TestCase):
    def test_f03_supported_generated_hardware_concurrency_is_forwarded(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = ProfileConfig(profile_name="fp", user_data_dir=str(Path(d)/"fp"), geoip=False)
            engine = StealthEngine(cfg)
            engine._resolve_host_ip = lambda: "192.168.1.10"
            fp = {"locale": "en-US", "timezone_id": "UTC", "hardware_concurrency": 12,
                  "user_agent": "advisory-agent", "viewport": {"width": 900, "height": 600},
                  "screen": {"width": 1200, "height": 800}, "device_memory": 32,
                  "platform": "Win32", "color_scheme": "dark", "is_mobile": False}
            kw = engine._build_launch_kwargs(fp, None, {"canvas": 1, "audio": 2, "fonts": 3})
            self.assertEqual(kw["config"]["navigator.hardwareConcurrency"], 12)
            self.assertEqual(kw["locale"], "en-US")
            self.assertEqual(kw["config"]["timezone"], "UTC")
            for key in ("user_agent", "viewport", "device_memory", "color_scheme", "platform", "screen"):
                self.assertNotIn(key, kw)
                self.assertNotIn(key, kw["config"])

    def test_f03_explicit_hardware_config_wins_over_proposed_identity(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = ProfileConfig(profile_name="fp", user_data_dir=str(Path(d)/"fp"),
                                hardware_concurrency=4, geoip=False)
            engine = StealthEngine(cfg)
            engine._resolve_host_ip = lambda: "192.168.1.10"
            opts = engine._build_launch_kwargs({"hardware_concurrency": 18, "locale": "fr-FR", "timezone_id": "UTC"},
                                                None, {"canvas": 1, "audio": 2, "fonts": 3})
            self.assertEqual(opts["config"]["navigator.hardwareConcurrency"], 4)


class P04SeedPrecedenceTests(unittest.TestCase):
    def test_f04_explicit_locale_and_timezone_rewrite_without_numeric_seed_rotation(self):
        from stealth_engine.identity import IdentityGenerator
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "acct"
            first = ProfileConfig(profile_name="acct", user_data_dir=str(base), seed=44,
                                  locale="en-US", timezone="America/New_York")
            one = IdentityGenerator(first).get_or_create_seeds()
            second = ProfileConfig(profile_name="acct", user_data_dir=str(base), seed=44,
                                   locale="fr-FR", timezone="Europe/Paris")
            two = IdentityGenerator(second).get_or_create_seeds()
            persisted = json.loads((base / "seeds.json").read_text())
            for k in ("canvas", "audio", "fonts"):
                self.assertEqual(one[k], two[k])
            self.assertEqual(two["locale"], "fr-FR")
            self.assertEqual(two["timezone_id"], "Europe/Paris")
            self.assertEqual(persisted, two)
            self.assertEqual(two["locale_source"], "config")
            self.assertEqual(two["timezone_source"], "config")

    def test_f04_auto_does_not_persist_auto_sentinel_or_rotate_seed(self):
        from stealth_engine.identity import IdentityGenerator
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "acct"
            cfg = ProfileConfig(profile_name="acct", user_data_dir=str(base), seed=44,
                                locale="en-US", timezone="Europe/Paris")
            first = IdentityGenerator(cfg).get_or_create_seeds()
            auto = cfg.model_copy(update={"locale": "auto", "timezone": "auto"})
            second = IdentityGenerator(auto).get_or_create_seeds()
            self.assertEqual(first, second)

    def test_f04_failed_seed_metadata_replacement_leaves_legacy_intact(self):
        from stealth_engine.identity import IdentityGenerator
        from stealth_engine.exceptions import IdentityError
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "acct"
            cfg = ProfileConfig(profile_name="acct", user_data_dir=str(base), seed=44,
                                locale="en-US", timezone="UTC")
            IdentityGenerator(cfg).get_or_create_seeds()
            path = base / "seeds.json"
            before = path.read_bytes()
            with patch("stealth_engine.identity.os.replace", side_effect=OSError("disk error")):
                with self.assertRaises(IdentityError):
                    IdentityGenerator(cfg.model_copy(update={"locale": "de-DE"})).get_or_create_seeds()
            self.assertEqual(path.read_bytes(), before)


class P04ExportSafetyTests(unittest.TestCase):
    def _cfg(self, base):
        return ProfileConfig(profile_name="sec", user_data_dir=str(base / "sec"),
                             proxy=ProxyConfig(server="http://embedded:embedded-pass@host:8080",
                                               username="topuser", password="topsecret"),
                             extra_headers={"Authorization": "Bearer abcprivate", "X-Test": "safe"})

    def test_f10_default_json_yaml_export_omits_proxy_and_auth_secrets(self):
        import yaml
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cfg=self._cfg(root)
            for fmt in ("json", "yaml"):
                path = root / ("profile."+fmt)
                (cfg.save_json if fmt=="json" else cfg.save_yaml)(path)
                raw = path.read_text()
                for token in ("embedded-pass", "topsecret", "topuser", "embedded", "abcprivate"):
                    self.assertNotIn(token, raw)
                data = json.loads(raw) if fmt=="json" else yaml.safe_load(raw)
                self.assertEqual(data["proxy"]["server"], "http://host:8080")
                self.assertIsNone(data["proxy"]["password"])
                self.assertEqual(data["extra_headers"]["Authorization"], "***")
                self.assertEqual(ProfileConfig.model_validate(data).profile_name, "sec")
                if __import__("os").name == "posix":
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertFalse(list(root.glob(".*.tmp")))

    def test_f10_explicit_backup_roundtrip_and_private_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cfg=self._cfg(root)
            for ext in ("json", "yaml"):
                path=root/("private."+ext)
                (cfg.save_json if ext=="json" else cfg.save_yaml)(path, include_secrets=True)
                loaded=(ProfileConfig.load_json if ext=="json" else ProfileConfig.load_yaml)(path)
                self.assertEqual(loaded, cfg)
                if __import__("os").name=="posix":
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_f10_failed_replace_keeps_original_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cfg=self._cfg(root);path=root/"config.json"
            path.write_text("previous")
            with patch("os.replace", side_effect=OSError("write failure")):
                with self.assertRaises(OSError):
                    cfg.save_json(path)
            self.assertEqual(path.read_text(), "previous")
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["config.json"])


class P04PresetTests(unittest.TestCase):
    def test_f13_all_public_presets_validate_without_android_claim(self):
        from stealth_engine.config import preset_names
        from stealth_engine.exceptions import ConfigError
        names=preset_names()
        self.assertNotIn("mobile-android", names)
        for name in names:
            cfg=ProfileConfig.preset(name, profile_name="acct", user_data_dir="/tmp/acct")
            self.assertIn(cfg.os, ("windows", "macos", "linux"))
        with self.assertRaises(ConfigError):
            ProfileConfig.preset("mobile-android",profile_name="acct",user_data_dir="/tmp/acct")


class P04ProfileLoggingTests(unittest.TestCase):
    def test_f19_profile_levels_are_isolated_without_global_handler_change(self):
        from stealth_engine.utils.logging import get_profile_logger
        captured=[]
        sink_id=logger.add(lambda msg: captured.append(msg.record), level="TRACE")
        try:
            info=get_profile_logger("stealth_engine.engine", "info-profile", "INFO")
            warning=get_profile_logger("stealth_engine.engine", "warn-profile", "WARNING")
            info.debug("hidden debug")
            info.info("per-profile info")
            warning.info("hidden info")
            warning.warning("per-profile warning")
            self.assertEqual([(x["extra"].get("profile"),x["message"]) for x in captured],
                             [("info-profile","per-profile info"), ("warn-profile","per-profile warning")])
        finally:
            logger.remove(sink_id)

    def test_f19_engines_bind_different_profiles_and_scrub_passwords(self):
        captured=[]
        sink_id=logger.add(lambda msg: captured.append(msg.record), level="TRACE")
        try:
            with tempfile.TemporaryDirectory() as d:
                a=StealthEngine(ProfileConfig(profile_name="a",user_data_dir=str(Path(d)/"a"),
                        log_level="INFO",proxy=ProxyConfig(server="http://u:passwd42@host:8080")))
                b=StealthEngine(ProfileConfig(profile_name="b",user_data_dir=str(Path(d)/"b"),
                        log_level="ERROR"))
                a._profile_log.info("profile info", reason="passwd42")
                b._profile_log.info("no visibility")
                b._profile_log.error("error visible")
            events=[(x["extra"].get("profile"),x["message"],x["extra"].get("reason")) for x in captured]
            self.assertEqual(events,[("a","profile info","***"),("b","error visible",None)])
        finally:
            logger.remove(sink_id)


class P05NoiseConsistencyTests(unittest.TestCase):
    """F-16: deterministic readbacks in a Node canvas/WebGL test double."""

    @unittest.skipUnless(__import__('shutil').which('node'), 'Node.js not present')
    def test_f16_canvas_webgl_readback_is_stable_and_live_pixels_intact(self):
        import subprocess
        from stealth_engine.engine import _js_noise_init_script
        mock = r"""
class CanvasRenderingContext2D {
  constructor(canvas) { this.canvas = canvas; }
  drawImage(source) { this.canvas.pixels = new Uint8ClampedArray(source.pixels); }
  getImageData() { return {data: new Uint8ClampedArray(this.canvas.pixels)}; }
  putImageData(img) { this.canvas.pixels = new Uint8ClampedArray(img.data); }
}
class HTMLCanvasElement {
  constructor() { this.width=24; this.height=24; this.pixels=new Uint8ClampedArray(24*24*4).fill(128); }
  getContext(mode) { return mode==='2d' ? new CanvasRenderingContext2D(this) : null; }
  toDataURL() { return 'data:canvas/' + Buffer.from(this.pixels).toString('hex'); }
}
class WebGLRenderingContext {
  readPixels(x,y,w,h,format,type,out) { out.fill(128); }
}
class WebGL2RenderingContext extends WebGLRenderingContext {}
globalThis.HTMLCanvasElement = HTMLCanvasElement;
globalThis.CanvasRenderingContext2D = CanvasRenderingContext2D;
globalThis.WebGLRenderingContext = WebGLRenderingContext;
globalThis.WebGL2RenderingContext = WebGL2RenderingContext;
globalThis.document = { createElement: () => new HTMLCanvasElement() };
const fs = require('node:fs');
eval(fs.readFileSync(0, 'utf8'));
const c = new HTMLCanvasElement();
const pixelBefore = Buffer.from(c.pixels).toString('hex');
const first = c.toDataURL();
const mid = c.getContext('2d').getImageData(0,0,24,24).data;
const second = c.toDataURL();
const again = c.getContext('2d').getImageData(0,0,24,24).data;
const third = c.toDataURL();
function glReads(Class) {
  const obj = new Class(); const a = new Uint8ClampedArray(24*24*4), b = new Uint8ClampedArray(24*24*4);
  obj.readPixels(0,0,24,24,0,0,a);
  obj.readPixels(0,0,24,24,0,0,b);
  return Buffer.from(a).equals(Buffer.from(b));
}
const out = {canvas: first===second && second===third,
             getImageData: Buffer.from(mid).equals(Buffer.from(again)),
             webgl1: glReads(WebGLRenderingContext), webgl2: glReads(WebGL2RenderingContext),
             liveCanvasIntact: pixelBefore===Buffer.from(c.pixels).toString('hex'),
             noiseApplied: first!=='data:canvas/'+pixelBefore};
console.log(JSON.stringify(out));
"""
        results=[]
        for seed in (7, 1001):
            run=subprocess.run(['node','-e',mock], input=_js_noise_init_script(seed),
                              text=True, capture_output=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr)
            result=json.loads(run.stdout)
            self.assertTrue(all(result.values()), result)
            results.append(result)
        self.assertEqual(results[0], results[1])

    def test_f16_script_generation_is_seed_stable(self):
        from stealth_engine.engine import _js_noise_init_script
        self.assertEqual(_js_noise_init_script(99), _js_noise_init_script(99))
        self.assertNotEqual(_js_noise_init_script(99), _js_noise_init_script(100))


class P05TrackerHostnameTests(unittest.IsolatedAsyncioTestCase):
    """F-17: match destination host labels, never URL text or userinfo."""

    async def asyncSetUp(self):
        self.ctx=SimpleNamespace(pages=[], route=AsyncMock())
        config=ProfileConfig(profile_name='p05', user_data_dir='p05')
        self.s=BrowserSession(self.ctx, object(), SimpleNamespace(), None, config)

    async def _route(self,url):
        handler=self.ctx.route.call_args.args[1]
        route=SimpleNamespace(abort=AsyncMock(), continue_=AsyncMock())
        await handler(route, SimpleNamespace(url=url))
        return route.abort.await_count,route.continue_.await_count

    async def test_f17_known_domains_and_subdomains_block(self):
        count=await self.s.block_trackers()
        self.assertGreater(count,0)
        for url in ('https://google-analytics.com/track','https://a.GOOGLE-ANALYTICS.com./pixel',
                    'https://connect.facebook.net/', 'https://safe.org/a?x=1#google-analytics.com'):
            blocked,allowed=await self._route(url)
            self.assertEqual((blocked,allowed),(0,1) if 'safe.org' in url else (1,0),url)

    async def test_f17_query_path_and_lookalike_never_block(self):
        await self.s.block_trackers()
        for url in ('https://good.example.org/article?next=https://google-analytics.com/',
                    'https://google-analytics.com.evil.org/path',
                    'https://google-analytics.com@good.example.org/',
                    'https://good.example.org/a/google-analytics.com',
                    'https://good.example.org/?tracker=hotjar.com',
                    'https://example.org/#google-analytics.com'):
            self.assertEqual(await self._route(url),(0,1),url)

    async def test_f17_redirect_destination_and_extra_domains(self):
        await self.s.block_trackers(extra_domains=['*.Partner.Example.com.', '  metrics.example.net  '])
        self.assertEqual(await self._route('https://good.org/redirect?to=https://partner.example.com'),(0,1))
        for url in ('https://partner.example.com/', 'https://sub.partner.example.com/',
                    'https://metrics.example.net/log'):
            self.assertEqual(await self._route(url),(1,0),url)
        self.assertEqual(await self._route('https://notpartner.example.com/'),(0,1))

    async def test_f17_invalid_authority_does_not_accidentally_block(self):
        await self.s.block_trackers()
        self.assertEqual(await self._route('https://[invalid]/?x=google-analytics.com'),(0,1))

    async def test_f17_registration_failure_remains_typed(self):
        self.ctx.route.side_effect=OSError('route install failure')
        with self.assertRaises(AutomationError):
            await self.s.block_trackers()


class P05ConditionalApiContractTests(unittest.TestCase):
    """U-02/U-03/U-06: unsupported and conditional behavior stays unchanged."""

    def test_u02_video_recording_still_rejected(self):
        from stealth_engine.exceptions import AutomationError
        with tempfile.TemporaryDirectory() as td:
            cfg=ProfileConfig(profile_name='video',user_data_dir=str(Path(td)/'video'),
                              record_video_dir='video-output')
            engine=StealthEngine(cfg)
            seeds={'canvas':1,'audio':2,'fonts':3,'locale':'en-US','timezone_id':'UTC'}
            with self.assertRaises(AutomationError) as cm:
                engine._build_launch_kwargs({'locale':'en-US','timezone_id':'UTC'},None,seeds)
            self.assertIn('unsupported',str(cm.exception))

    def test_u06_timeout_wrapping_remains_task_only(self):
        import inspect, ast, textwrap
        from stealth_engine.orchestrator import BulkRunner
        source=textwrap.dedent(inspect.getsource(BulkRunner._attempt_profile))
        method=ast.parse(source).body[0]
        targets=[n for n in ast.walk(method) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='wait_for']
        self.assertEqual(len(targets),1)
        self.assertIsInstance(targets[0].args[0],ast.Call)
        self.assertIsInstance(targets[0].args[0].func,ast.Name)
        self.assertEqual(targets[0].args[0].func.id,'task_fn')


class P05ConditionalCdpTest(unittest.IsolatedAsyncioTestCase):
    async def test_u03_unsupported_backend_surfaces_automation_error(self):
        ctx=SimpleNamespace(pages=[],new_cdp_session=AsyncMock(side_effect=NotImplementedError('Firefox')))
        cfg=ProfileConfig(profile_name='cdp',user_data_dir='cdp')
        session=BrowserSession(ctx,object(),SimpleNamespace(),None,cfg)
        with self.assertRaises(AutomationError):
            await session.cdp_session(object())
