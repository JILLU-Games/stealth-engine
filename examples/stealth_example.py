"""Full-stack stealth demo (PH-21, V3).

Demonstrates the complete stealth stack in one runnable script:
config → launch → warmup → human hooks → probes → verify_stealth →
recording options → clean close.

Run:  python examples/stealth_example.py
Requires: camoufox installed (pip install 'camoufox[geoip]' + camoufox fetch).
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from stealth_engine import (
    ProfileConfig,
    ProxyConfig,
    StealthEngine,
    ban_risk_score,
)


async def main() -> None:
    with tempfile.TemporaryDirectory() as d:
        cfg = ProfileConfig(
            profile_name="stealth_demo",
            user_data_dir=str(Path(d) / "stealth_demo"),
            seed=1337,
            headless=True,
            geoip=False,
            # --- advanced layer ---
            js_noise=True,               # canvas/WebGL readback noise
            seed_localstorage=True,      # plausible storage fingerprint
            disable_ipv6=True,
            proxy_remote_dns=True,
            webgl_config=(
                "Google Inc.",
                "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11)",
            ),
            hardware_concurrency=8,
            screen_bounds=(1920, 2560, 1080, 1440),
            # --- recording/debug ---
            record_har_path="demo.har",
            record_har_content="omit",
            # record_video_dir="demo_videos",
        )

        # Optional: uncomment with a real proxy to enable geoip mode.
        # cfg.proxy = ProxyConfig(server="socks5://user:pass@host:1080")
        # cfg.geoip = True
        # cfg.locale = "auto"
        # cfg.timezone = "auto"

        engine = StealthEngine(cfg)
        session = await engine.alaunch()
        try:
            page = await session.new_page_async()
            await page.goto("about:blank")

            # Warmup flow (social preset = longer dwell).
            # await session.warmup("https://example.com", template="social")

            # Human-like interaction demo.
            await session.ahuman_move(page, 300, 200)
            await session.ahuman_type(page, "hello stealth")
            await session.ahuman_scroll(page, 300)
            await session.adwell(page, 0.5, 1.0)

            # Block trackers on real navigations.
            # await session.block_trackers()

            # Stealth audit.
            report = await session.verify_stealth(page)
            print("=== verify_stealth ===")
            print(report["summary"])
            print("consistent:", report["consistent"])
            for sig in report["risk"]["signals"]:
                print("  -", sig)

            # Standalone risk score demo.
            risk = ban_risk_score(report["probe"], config=cfg)
            print("risk:", risk["score"], risk["level"])

            # Session age (days since first launch).
            print("session_age_days:", session.session_age_days())
        finally:
            await session.aclose()

    print("done — demo.har written under profile dir (if recording supported)")


if __name__ == "__main__":
    asyncio.run(main())
