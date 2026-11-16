"""Real Direct-Host network acceptance; no proxy credentials or test targets owned by third parties.

Uses ipify's documented HTTPS echo endpoint only. This is explicitly NOT
proxy egress or DNS/WebRTC leak certification.
"""
from __future__ import annotations

import ipaddress
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest

import aiohttp
from stealth_engine import ProfileConfig, StealthEngine

_IP_URL = "https://api.ipify.org?format=json"


class DirectHostAcceptance(unittest.IsolatedAsyncioTestCase):
    async def test_direct_https_egress_matches_runner_host(self):
        # DNS resolution occurs on the actual runner. Do not silently replace
        # DNS failures with canned data or a fake local proxy.
        resolved = socket.getaddrinfo("api.ipify.org", 443, type=socket.SOCK_STREAM)
        self.assertTrue(resolved, "runner DNS resolution failed")
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20), trust_env=False
        ) as client:
            async with client.get(_IP_URL) as response:
                self.assertEqual(response.status, 200)
                expected = (await response.json())["ip"]
        host_ip = ipaddress.ip_address(expected)
        self.assertEqual(host_ip.version, 4)
        self.assertTrue(host_ip.is_global)
        with tempfile.TemporaryDirectory(prefix="direct-host-ci-") as directory:
            cfg = ProfileConfig(
                profile_name="ci_direct_host",
                user_data_dir=str(Path(directory) / "ci_direct_host"),
                os="windows" if os.name == "nt" else "linux",
                proxy=None,
                target_ip=expected,  # config hint, never an outgoing-IP override
                geoip=False,
                headless=True,
                seed=2945,
            )
            engine = StealthEngine(cfg)
            session = await engine.alaunch()
            try:
                self.assertIsNone(engine._proxy_manager)
                self.assertEqual(session._ctx_handle is not None, True)
                page = session.page
                response = await page.goto(_IP_URL, wait_until="domcontentloaded", timeout=25000)
                self.assertIsNotNone(response)
                self.assertEqual(response.status, 200)
                observed = json.loads(await page.locator("body").inner_text(timeout=10000))
                browser_ip = ipaddress.ip_address(observed["ip"])
                self.assertEqual(browser_ip.version, 4)
                self.assertTrue(browser_ip.is_global)
                self.assertEqual(
                    browser_ip, host_ip,
                    "direct browser IP differs from runner host IP; no NAT parity claim",
                )
                # A second browser request proves the browser stays externally
                # connected without quietly switching to a different proxy.
                repeated = await page.reload(wait_until="domcontentloaded", timeout=25000)
                self.assertEqual(repeated.status, 200)
                repeated_ip = ipaddress.ip_address(
                    json.loads(await page.locator("body").inner_text())["ip"]
                )
                self.assertEqual(repeated_ip, browser_ip)
            finally:
                await session.aclose()
