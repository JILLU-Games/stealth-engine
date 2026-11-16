"""Real socket-bound HTTP proxy integration: localhost only, no external proxy.

A controlled proxy answers geolocation/HTTP probes without contacting the
requested domain. Browser routing is separately exercised through a fake
.invalid destination so there is no unauthorized target traffic.
"""
from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
import tempfile
import unittest

from stealth_engine import ProfileConfig, ProxyConfig, StealthEngine
from stealth_engine.exceptions import ProxyError
from stealth_engine.proxy import GeoInfo, ProxyManager

_GEO = {"ip": "8.8.4.4", "country": "US", "timezone": "America/New_York"}
_FAKE_HOST = "ci-proxy-target.invalid"


class LocalHTTPProxy:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.server = None
        self.requests = []
        self.errors = []

    async def __aenter__(self):
        self.server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *_):
        self.server.close()
        await self.server.wait_closed()

    async def _handle(self, reader, writer):
        try:
            raw = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 10)
            lines = raw.decode("latin-1").split("\r\n")
            request = lines[0]
            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    name, value = line.split(":", 1)
                    headers[name.strip().lower()] = value.strip()
            auth = headers.get("proxy-authorization")
            authenticated = self.username is None
            if self.username is not None:
                expected = "Basic " + base64.b64encode(
                    f"{self.username}:{self.password}".encode()
                ).decode()
                authenticated = auth == expected
            self.requests.append({"line": request, "authenticated": authenticated})
            if not authenticated:
                code, text, payload = 407, "Proxy Authentication Required", b""
            elif "/geo" in request:
                code, text, payload = 200, "OK", json.dumps(_GEO).encode()
            elif _FAKE_HOST in request:
                code, text, payload = 200, "OK", b"LOCAL_PROXY_CONFIRMED"
            else:
                code, text, payload = 502, "Bad Gateway", b""
            out = (
                f"HTTP/1.1 {code} {text}\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(payload)}\r\n"
                f"Connection: close\r\n\r\n"
            ).encode() + payload
            writer.write(out)
            await writer.drain()
        except (EOFError, ConnectionError, asyncio.TimeoutError, asyncio.IncompleteReadError) as exc:
            self.errors.append(type(exc).__name__)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionError:
                pass


class LocalProxyProtocolAcceptance(unittest.IsolatedAsyncioTestCase):
    async def test_authenticated_http_geo_and_wrong_password_rejected(self):
        async with LocalHTTPProxy("alice", "CI_ONLY_SENTINEL") as peer:
            cfg = ProxyConfig(
                server=f"http://127.0.0.1:{peer.port}",
                username="alice", password="CI_ONLY_SENTINEL",
            )
            manager = ProxyManager([cfg], geo_endpoint="http://geo.invalid/geo", timeout_s=3)
            try:
                selected, geo = await manager.pick_healthy()
                self.assertEqual(selected, cfg)
                self.assertEqual(geo.ip, _GEO["ip"])
                self.assertTrue(peer.requests[-1]["authenticated"])
                self.assertNotIn("CI_ONLY_SENTINEL", str(manager.mask(cfg)))
            finally:
                await manager.aclose()
            wrong = ProxyConfig(
                server=f"http://127.0.0.1:{peer.port}",
                username="alice", password="WRONG_CI_SENTINEL",
            )
            denied = ProxyManager([wrong], geo_endpoint="http://geo.invalid/geo", timeout_s=3)
            try:
                with self.assertRaises(ProxyError) as captured:
                    await denied.resolve_geo(wrong)
                self.assertNotIn("WRONG_CI_SENTINEL", str(captured.exception))
                self.assertFalse(peer.requests[-1]["authenticated"])
            finally:
                await denied.aclose()

    async def test_real_camoufox_through_loopback_http_proxy(self):
        async with LocalHTTPProxy() as peer:
            with tempfile.TemporaryDirectory() as base:
                cfg = ProfileConfig(
                    profile_name="loopback_proxy",
                    user_data_dir=str(Path(base) / "loopback_proxy"),
                    os="linux",
                    proxy=ProxyConfig(server=f"http://127.0.0.1:{peer.port}"),
                    geoip=False,
                    headless=True,
                    locale="en-US",
                    timezone="Etc/UTC",
                    seed=3861,
                )
                engine = StealthEngine(cfg)
                # Health metadata is synthesized, not a claim of real proxy
                # geolocation. The actual browser still uses the real socket
                # proxy configured in ProxyConfig.
                async def local_geo(_proxy):
                    return GeoInfo(
                        ip="8.8.4.4", country="US",
                        timezone_id="America/New_York",
                        locale="en-US", currency="USD",
                    )
                engine._proxy_manager.resolve_geo = local_geo
                session = await engine.alaunch()
                try:
                    page = session.page
                    url = f"http://{_FAKE_HOST}/check"
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    self.assertIsNotNone(response)
                    self.assertEqual(response.status, 200)
                    self.assertIn("LOCAL_PROXY_CONFIRMED", await page.locator("body").inner_text())
                    self.assertTrue(
                        any(_FAKE_HOST in r["line"] for r in peer.requests),
                        "browser request never reached the loopback proxy",
                    )
                finally:
                    await session.aclose()
