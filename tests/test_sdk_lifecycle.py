"""Offline lifecycle and opt-in configuration regression tests."""
import asyncio
import tempfile
import threading
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

    async def test_fqa01_closed_flag_waits_for_async_callbacks(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            entered, proceed = asyncio.Event(), asyncio.Event()
            calls = []
            async def callback(profile):
                calls.append(profile)
                entered.set()
                await proceed.wait()
            engine._on_close = callback
            session, _ = await self.launch(engine, EventContext())
            task = asyncio.create_task(session.aclose())
            try:
                await asyncio.wait_for(entered.wait(), 5)
                self.assertFalse(session._closed)
                self.assertFalse(Path(engine._session.lock_path).exists())
                self.assertFalse(task.done())
            finally:
                proceed.set()
                await asyncio.wait_for(task, 5)
            self.assertTrue(session._closed)
            self.assertEqual(calls, ["p01"])

    async def test_fqa01_owned_loop_waits_for_callback_and_concurrent_close(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            entered, proceed = threading.Event(), threading.Event()
            calls = []
            async def callback(profile):
                calls.append(profile)
                entered.set()
                if not await asyncio.to_thread(proceed.wait, 10):
                    raise RuntimeError("test callback timeout")
            engine._on_close = callback
            ctx = EventContext()
            handle = _P01Handle(ctx)
            def launch_sync():
                with _p01_fake_camoufox(handle), patch.object(StealthEngine, "_resolve_host_ip", return_value=""):
                    return engine.launch()
            session = await asyncio.to_thread(launch_sync)
            loop, worker = session._sync_loop, session._sync_thread
            tasks = []
            try:
                loop.call_soon_threadsafe(ctx.listener, ctx)
                self.assertTrue(await asyncio.to_thread(entered.wait, 5))
                tasks = [asyncio.create_task(asyncio.to_thread(session.close)),
                         asyncio.create_task(session.aclose())]
                # Scheduling happens before the callback is allowed to finish.
                async def scheduled():
                    while session._sync_close_future is None:
                        await asyncio.sleep(0.001)
                await asyncio.wait_for(scheduled(), 5)
                self.assertFalse(session._closed)
                self.assertTrue(worker.is_alive())
                self.assertTrue(all(not task.done() for task in tasks))
            finally:
                proceed.set()
                if tasks:
                    await asyncio.wait_for(asyncio.gather(*tasks), 10)
                else:
                    await asyncio.to_thread(session.close)
            self.assertTrue(session._closed)
            self.assertEqual(calls, ["p01"])
            self.assertEqual(handle.exit_calls, 1)
            self.assertFalse(worker.is_alive())
            self.assertTrue(loop.is_closed())

    async def test_fqa02_early_close_during_restore_cleans_once(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            engine._config.restore_state = True
            engine._on_close, engine._on_error = AsyncMock(), AsyncMock()
            ctx = EventContext()
            handle = _P01Handle(ctx)
            async def close_during_restore(state):
                self.assertIsNotNone(ctx.listener)
                ctx.listener(ctx)
                await asyncio.sleep(0)
            ctx.set_storage_state.side_effect = close_during_restore
            with _p01_fake_camoufox(handle), patch.object(StealthEngine, "_resolve_host_ip", return_value=""), patch.object(
                engine._session, "has_state", return_value=True
            ), patch.object(engine._session, "import_state", return_value={"cookies": [], "origins": []}):
                with self.assertRaisesRegex(Exception, "context closed during launch"):
                    await engine.alaunch()
            self.assertFalse(Path(engine._session.lock_path).exists())
            self.assertEqual(handle.exit_calls, 1)
            engine._on_close.assert_awaited_once_with("p01")
            engine._on_error.assert_awaited_once()
            self.assertIsNone(engine._active_session)

    async def test_fqa02_early_close_during_initial_page_cleans_once(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            ctx = EventContext()
            ctx.pages = []
            handle = _P01Handle(ctx)
            async def close_during_page():
                self.assertIsNotNone(ctx.listener)
                ctx.listener(ctx)
                await asyncio.sleep(0)
                return object()
            ctx.new_page = close_during_page
            with _p01_fake_camoufox(handle), patch.object(StealthEngine, "_resolve_host_ip", return_value=""):
                with self.assertRaisesRegex(Exception, "context closed during launch"):
                    await engine.alaunch()
            self.assertFalse(Path(engine._session.lock_path).exists())
            self.assertEqual(handle.exit_calls, 1)
            self.assertIsNone(engine._active_session)

    async def test_fqa04_existing_disk_calls_run_in_worker(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            from stealth_engine import engine as module
            loop_thread = threading.get_ident()
            observed = {}
            seeds = engine._identity.get_or_create_seeds
            history = engine._record_fingerprint
            def read():
                observed["seeds"] = threading.get_ident()
                return seeds()
            def write():
                observed["history"] = threading.get_ident()
                return history()
            with patch.object(engine._identity, "get_or_create_seeds", side_effect=read) as seed_call, patch.object(
                engine, "_record_fingerprint", side_effect=write
            ) as history_call, patch.object(module, "_disk_call", wraps=module._disk_call) as disk:
                session, _ = await self.launch(engine, EventContext())
                try:
                    disk.assert_any_await(seed_call)
                    disk.assert_any_await(history_call)
                    self.assertNotEqual(observed["seeds"], loop_thread)
                    self.assertNotEqual(observed["history"], loop_thread)
                finally:
                    await session.aclose()

    async def test_fqa05_export_drains_before_release_and_rejects_late_save(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            session, _ = await self.launch(engine, EventContext())
            entered, proceed = threading.Event(), threading.Event()
            writes = []
            export = engine._session.export_state
            release = engine._session.release_lock
            def slow_export(state):
                writes.append("start")
                if len(writes) == 1:
                    entered.set()
                    if not proceed.wait(10):
                        raise RuntimeError("test export timeout")
                export(state)
                writes.append("end")
            def release_after_exports():
                writes.append("release")
                release()
            with patch.object(engine._session, "export_state", side_effect=slow_export), patch.object(
                engine._session, "release_lock", side_effect=release_after_exports
            ):
                save = asyncio.create_task(session.save_state_async())
                closing = None
                try:
                    self.assertTrue(await asyncio.to_thread(entered.wait, 5))
                    closing = asyncio.create_task(session.aclose())
                    async def close_started():
                        while session._close_task is None:
                            await asyncio.sleep(0.001)
                    await asyncio.wait_for(close_started(), 5)
                    self.assertEqual(writes, ["start"])
                    self.assertTrue(Path(engine._session.lock_path).exists())
                finally:
                    proceed.set()
                    await asyncio.wait_for(save, 10)
                    if closing is not None:
                        await asyncio.wait_for(closing, 10)
                    else:
                        await session.aclose()
                self.assertEqual(writes, ["start", "end", "start", "end", "release"])
                with self.assertRaisesRegex(Exception, "closing or closed"):
                    await session.save_state_async()
                self.assertFalse(Path(engine._session.lock_path).exists())
                self.assertFalse(Path(engine._session.storage_state_path).with_suffix(".json.tmp").exists())

    async def test_fqa01_stop_requested_once_during_executor_shutdown(self):
        with tempfile.TemporaryDirectory() as td:
            engine = _p01_engine(td)
            ctx = EventContext()
            handle = _P01Handle(ctx)
            def launch_sync():
                with _p01_fake_camoufox(handle), patch.object(StealthEngine, "_resolve_host_ip", return_value=""):
                    return engine.launch()
            session = await asyncio.to_thread(launch_sync)
            loop, worker = session._sync_loop, session._sync_thread
            shutdown_entered, shutdown_release, join_entered = (
                threading.Event(), threading.Event(), threading.Event()
            )
            original_shutdown = loop.shutdown_default_executor
            original_join = worker.join
            async def held_shutdown():
                shutdown_entered.set()
                if not await asyncio.to_thread(shutdown_release.wait, 10):
                    raise RuntimeError("test shutdown timeout")
                await original_shutdown()
            def observed_join(*args, **kwargs):
                join_entered.set()
                return original_join(*args, **kwargs)
            explicit_close = None
            with patch.object(loop, "shutdown_default_executor", side_effect=held_shutdown), patch.object(
                loop, "call_soon_threadsafe", wraps=loop.call_soon_threadsafe
            ) as schedule, patch.object(worker, "join", side_effect=observed_join):
                try:
                    loop.call_soon_threadsafe(ctx.listener, ctx)
                    self.assertTrue(await asyncio.to_thread(shutdown_entered.wait, 5))
                    explicit_close = asyncio.create_task(asyncio.to_thread(session.close))
                    self.assertTrue(await asyncio.to_thread(join_entered.wait, 5))
                    stop_requests = [c for c in schedule.call_args_list if c.args and c.args[0] == loop.stop]
                    self.assertEqual(len(stop_requests), 1)
                    self.assertFalse(explicit_close.done())
                finally:
                    shutdown_release.set()
                    if explicit_close is not None:
                        await asyncio.wait_for(explicit_close, 10)
                    else:
                        await asyncio.to_thread(session.close)
            self.assertTrue(session._closed)
            self.assertFalse(worker.is_alive())
            self.assertTrue(loop.is_closed())
            self.assertEqual(handle.exit_calls, 1)
