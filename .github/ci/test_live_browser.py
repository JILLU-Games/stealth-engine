"""Real Camoufox acceptance: actual sync loop, JS readbacks and browser routing.

Tested on GitHub-hosted Windows and Linux, never on a fake browser. The local
HTTP server makes routing deterministic without relying on an external site.
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
import unittest

from stealth_engine import ProfileConfig, StealthEngine


class SyncLifecycleAcceptance(unittest.TestCase):
    def test_sync_launch_page_and_close(self):
        with tempfile.TemporaryDirectory() as base:
            cfg = ProfileConfig(
                profile_name="sync_acceptance", user_data_dir=str(Path(base) / "sync"),
                seed=120, geoip=False, headless=True,
            )
            engine = StealthEngine(cfg)
            session = engine.launch()
            try:
                self.assertIsNotNone(session.page)
                self.assertIsNotNone(session._sync_loop)
            finally:
                session.close()
            self.assertTrue(session._closed)
            self.assertIsNone(session._sync_loop)
            session.close()


class BrowserBehaviorAcceptance(unittest.IsolatedAsyncioTestCase):
    async def test_browser_visible_hardware_and_timezone(self):
        with tempfile.TemporaryDirectory() as base:
            cfg = ProfileConfig(
                profile_name="readback", user_data_dir=str(Path(base) / "readback"),
                headless=True, geoip=False, seed=12345,
                hardware_concurrency=4, timezone="Europe/Berlin", locale="de-DE",
            )
            session = await StealthEngine(cfg).alaunch()
            try:
                page = session.page
                self.assertIsNotNone(page)
                await page.goto("about:blank")
                seen = await page.evaluate("""() => ({
                    cpu: navigator.hardwareConcurrency,
                    tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    language: navigator.language
                })""")
                self.assertEqual(seen["cpu"], 4)
                self.assertEqual(seen["tz"], "Europe/Berlin")
                self.assertEqual(seen["language"], "de-DE")
            finally:
                await session.aclose()

    async def test_live_canvas_repeated_reads_are_identical(self):
        with tempfile.TemporaryDirectory() as base:
            cfg = ProfileConfig(
                profile_name="canvas", user_data_dir=str(Path(base) / "canvas"),
                headless=True, geoip=False, seed=4321, js_noise=True,
            )
            session = await StealthEngine(cfg).alaunch()
            try:
                page = session.page
                await page.goto("about:blank")
                results = await page.evaluate("""() => {
                    const canvas = document.createElement("canvas");
                    canvas.width = 16;
                    canvas.height = 16;
                    const ctx = canvas.getContext("2d");
                    ctx.fillStyle = "#4268aa";
                    ctx.fillRect(0, 0, 16, 16);
                    const image1 = Array.from(ctx.getImageData(0, 0, 16, 16).data);
                    const image2 = Array.from(ctx.getImageData(0, 0, 16, 16).data);
                    return {
                        urls: [canvas.toDataURL(), canvas.toDataURL()],
                        samePixels: JSON.stringify(image1) === JSON.stringify(image2)
                    };
                }""")
                # Both native export and 2D getImageData must be stable without writes.
                self.assertEqual(results["urls"][0], results["urls"][1])
                self.assertTrue(results["samePixels"])
            finally:
                await session.aclose()

    async def test_real_tracker_route_blocks_only_destination_host(self):
        async def serve(reader, writer):
            try:
                await reader.readuntil(b"\r\n\r\n")
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n"
                             b"Content-Type: text/plain\r\nConnection: close\r\n\r\nOK")
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()

        server = await asyncio.start_server(serve, "127.0.0.1", 0)
        try:
            port = server.sockets[0].getsockname()[1]
            with tempfile.TemporaryDirectory() as base:
                cfg = ProfileConfig(
                    profile_name="routing", user_data_dir=str(Path(base) / "routing"),
                    headless=True, geoip=False, seed=4567,
                )
                session = await StealthEngine(cfg).alaunch()
                try:
                    page = session.page
                    # Tracker strings in query/path must NOT cause a block.
                    response = await page.goto(
                        f"http://127.0.0.1:{port}/ok?next=tracker.example.com",
                        wait_until="domcontentloaded",
                    )
                    self.assertEqual(response.status, 200)
                    await session.block_trackers(extra_domains=["127.0.0.1"])
                    # The exact destination host must be blocked even though
                    # the test server remains alive and reachable.
                    with self.assertRaises(Exception):
                        await page.goto(f"http://127.0.0.1:{port}/blocked")
                finally:
                    await session.aclose()
        finally:
            server.close()
            await server.wait_closed()
