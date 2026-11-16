"""Opt-in browser egress check through a proxy the repository owner controls.

This is NOT a WebRTC/DNS-leak certification. It never prints credentials or
browser traces. The endpoint must be HTTPS and return JSON with an `ip` key.
"""
from __future__ import annotations

import asyncio
import ipaddress
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

from stealth_engine import ProfileConfig, ProxyConfig, StealthEngine


def required(name: str) -> str:
    result = os.environ.get(name, "").strip()
    if not result:
        raise RuntimeError(f"Required GitHub Actions secret {name} is missing")
    return result


async def verify() -> None:
    server = required("CI_PROXY_SERVER")
    url = required("CI_EGRESS_JSON_URL")
    expected = required("CI_EXPECTED_EXIT_IP")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise RuntimeError("CI_EGRESS_JSON_URL must be a credential-free HTTPS endpoint")
    if not ipaddress.ip_address(expected).is_global:
        raise RuntimeError("CI_EXPECTED_EXIT_IP must be a public routable IP")

    # The server URL is validated by ProxyConfig; keep all sensitive values out of reports.
    proxy = ProxyConfig(
        server=server,
        username=os.getenv("CI_PROXY_USERNAME") or None,
        password=os.getenv("CI_PROXY_PASSWORD") or None,
    )
    with tempfile.TemporaryDirectory(prefix="stealth-proxy-ci-") as directory:
        config = ProfileConfig(
            profile_name="ci_real_proxy",
            user_data_dir=str(Path(directory) / "profile"),
            proxy=proxy,
            geoip=True,
            locale="auto",
            timezone="auto",
            headless=True,
        )
        engine = StealthEngine(config)
        session = await engine.alaunch()
        try:
            page = session.page or await session.new_page_async()
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if response is None or not response.ok:
                raise RuntimeError("Proxy egress probe did not return HTTP 2xx")
            data = json.loads(await page.locator("body").inner_text(timeout=10000))
            actual = data.get("ip")
            if not isinstance(actual, str) or ipaddress.ip_address(actual) != ipaddress.ip_address(expected):
                raise RuntimeError("Observed proxy egress IP differs from the expected IP")
        finally:
            await session.aclose()
    print("EXTERNAL PROXY EGRESS GATE PASS (does not certify DNS or WebRTC leakage)")


if __name__ == "__main__":
    asyncio.run(verify())
