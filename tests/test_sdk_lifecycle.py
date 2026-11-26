"""Offline lifecycle and opt-in configuration regression tests."""
import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from stealth_engine import ProfileConfig, StealthEngine
from tests.test_forensic_regressions import _P01Context, _P01Handle, _p01_engine, _p01_fake_camoufox


class EventContext(_P01Context):
    def __init__(self, *, fail_capture=False):
        super().__init__()
        self.listener = None
        self.fail_capture = fail_capture
        self.set_storage_state = AsyncMock()

    def on(self, name, callback):
        if name == "close":
            self.listener = callback

    async def storage_state(self):
        if self.fail_capture:
            raise RuntimeError("closed context")
        return await super().storage_state()

    async def close(self):
        await super().close()
        if self.listener:
            self.listener(self)


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def launch(self, engine, ctx):
        handle = _P01Handle(ctx)
        with _p01_fake_camoufox(handle), patch.object(StealthEngine, "_resolve_host_ip", return_value=""):
            session = await engine.alaunch()
        return session, handle

    async def test_manual_close_releases_lock_and_calls_sync_hook_once(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            close = Mock()
            engine._on_close = close
            ctx = EventContext()
            session, handle = await self.launch(engine, ctx)
            self.assertTrue(Path(engine._session.lock_path).exists())
            ctx.listener(ctx)
            ctx.listener(ctx)
            await session.aclose()
            self.assertTrue(session._closed)
            self.assertFalse(Path(engine._session.lock_path).exists())
            close.assert_called_once_with("p01")
            self.assertEqual(handle.exit_calls, 1)
            self.assertTrue(engine._session.has_state())

    async def test_manual_close_capture_failure_preserves_previous_state(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            close, error = AsyncMock(), AsyncMock()
            engine._on_close, engine._on_error = close, error
            ctx = EventContext(fail_capture=True)
            session, _ = await self.launch(engine, ctx)
            await asyncio.to_thread(engine._session.export_state, {"cookies": [], "origins": []})
            previous = Path(engine._session.storage_state_path).read_bytes()
            ctx.listener(ctx)
            await session.aclose()
            self.assertEqual(Path(engine._session.storage_state_path).read_bytes(), previous)
            self.assertFalse(Path(engine._session.lock_path).exists())
            close.assert_awaited_once_with("p01")
            error.assert_awaited_once()

    async def test_explicit_close_coalesces_and_callback_failure_isolated(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            close = AsyncMock(side_effect=RuntimeError("callback failed"))
            engine._on_close = close
            ctx = EventContext()
            session, handle = await self.launch(engine, ctx)
            await asyncio.gather(session.aclose(), session.aclose())
            close.assert_awaited_once_with("p01")
            self.assertEqual(ctx.close_calls, 1)
            self.assertEqual(handle.exit_calls, 1)
            self.assertFalse(Path(engine._session.lock_path).exists())

    async def test_restore_opt_in_reads_same_profile(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            engine._config.restore_state = True
            ctx = EventContext()
            state = {"cookies": [], "origins": []}
            with patch.object(engine._session, "has_state", return_value=True), patch.object(
                engine._session, "import_state", return_value=state
            ) as load:
                session, _ = await self.launch(engine, ctx)
                try:
                    load.assert_called_once_with()
                    ctx.set_storage_state.assert_awaited_once_with(state)
                finally:
                    await session.aclose()

    async def test_restore_default_does_not_import(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            ctx = EventContext()
            with patch.object(engine._session, "import_state") as load:
                session, _ = await self.launch(engine, ctx)
                try:
                    load.assert_not_called()
                    ctx.set_storage_state.assert_not_awaited()
                finally:
                    await session.aclose()

    async def test_launch_error_hook_and_owner_lock(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            error = AsyncMock()
            engine._on_error = error
            session, _ = await self.launch(engine, EventContext())
            try:
                with self.assertRaisesRegex(Exception, "already owns"):
                    await engine.alaunch()
                self.assertTrue(Path(engine._session.lock_path).exists())
                error.assert_awaited_once()
            finally:
                await session.aclose()

    def test_config_defaults_and_host_probe_opt_out(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            self.assertTrue(engine._config.auto_resolve_host_ip)
            self.assertFalse(engine._config.restore_state)
            engine._config.auto_resolve_host_ip = False
            with patch.object(engine, "_resolve_host_ip") as probe:
                engine._build_launch_kwargs(
                    {"locale": "en-US", "timezone_id": "UTC"}, None,
                    seeds={"canvas": 11, "audio": 12, "fonts": 13, "locale": "en-US", "timezone_id": "UTC"}
                )
                probe.assert_not_called()

    def test_callback_constructor_keywords(self):
        with tempfile.TemporaryDirectory() as td:
            config = ProfileConfig(profile_name="sdk", user_data_dir=str(Path(td) / "sdk"))
            close, error = Mock(), Mock()
            engine = StealthEngine(config, on_close=close, on_error=error)
            self.assertIs(engine._on_close, close)
            self.assertIs(engine._on_error, error)
