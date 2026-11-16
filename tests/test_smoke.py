"""Real-browser smoke test — env-gated, never runs in normal CI.

Set ``STEALTH_SMOKE=1`` to enable.  Requires the camoufox binary to be
installed (``pip install 'camoufox[geoip]'`` + ``camoufox fetch``).
Skipped automatically when the env var is unset or camoufox is missing.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from stealth_engine import ProfileConfig, StealthEngine

_SMOKE = os.environ.get("STEALTH_SMOKE") == "1"


@unittest.skipUnless(_SMOKE, "set STEALTH_SMOKE=1 to run the real-browser smoke test")
class RealBrowserSmokeTests(unittest.IsolatedAsyncioTestCase):
    """First real camoufox launch verification (PH-11)."""

    async def test_launch_about_blank_and_close(self):
        try:
            import camoufox  # noqa: F401
        except ImportError:
            self.skipTest("camoufox package not installed")

        with tempfile.TemporaryDirectory() as d:
            cfg = ProfileConfig(
                profile_name="smoke",
                user_data_dir=str(Path(d) / "smoke"),
                headless=True,
                seed=7,
            )
            engine = StealthEngine(cfg)
            try:
                session = await engine.alaunch()
            except Exception as exc:
                # PF-01/B-28: skip ONLY when the browser binary is genuinely
                # missing — launch TypeErrors/config bugs must FAIL, not
                # hide behind a skip (this masked B-27 for several phases).
                msg = str(exc).lower()
                if (
                    "executable" in msg
                    or "no such file" in msg
                    or "not installed" in msg
                    or "camoufox fetch" in msg
                ):
                    self.skipTest(f"camoufox binary unavailable: {exc}")
                raise
            try:
                page = await session.new_page_async()
                await page.goto("about:blank")
                title = await page.title()
                self.assertIsInstance(title, str)
            finally:
                await session.aclose()

    async def test_verify_stealth_real_browser(self):
        """PH-21 V1: full stealth audit on a real camoufox session."""
        try:
            import camoufox  # noqa: F401
        except ImportError:
            self.skipTest("camoufox package not installed")

        with tempfile.TemporaryDirectory() as d:
            cfg = ProfileConfig(
                profile_name="smoke2",
                user_data_dir=str(Path(d) / "smoke2"),
                headless=True,
                seed=11,
                js_noise=True,
                seed_localstorage=True,
            )
            engine = StealthEngine(cfg)
            try:
                session = await engine.alaunch()
            except Exception as exc:
                msg = str(exc).lower()
                if (
                    "executable" in msg
                    or "no such file" in msg
                    or "not installed" in msg
                    or "camoufox fetch" in msg
                ):
                    self.skipTest(f"camoufox binary unavailable: {exc}")
                raise
            try:
                page = await session.new_page_async()
                await page.goto("about:blank")
                report = await session.verify_stealth(page)
                # Report structure must be complete even if risk is high.
                for key in ("probe", "risk", "consistent", "summary"):
                    self.assertIn(key, report)
                self.assertIn("score", report["risk"])
                self.assertIn("level", report["risk"])
                # Live probe must return real values, not all-None.
                probe = report["probe"]
                self.assertTrue(probe.get("user_agent"))
                self.assertTrue(probe.get("canvas_hash"))
            finally:
                await session.aclose()


@unittest.skipUnless(
    os.environ.get("STEALTH_CANARY") == "1",
    "set STEALTH_CANARY=1 to run fingerprint canary checks",
)
class FingerprintCanaryTests(unittest.TestCase):
    """PH-21 V2: generated fingerprints must pass the consistency validator.

    Runs without a browser — validates that IdentityGenerator output is
        internally coherent (catches provider/regression drift early).
    """

    def test_generated_fingerprints_pass_validator(self):
        from stealth_engine import validate_fingerprint
        from stealth_engine.identity import IdentityGenerator

        for seed in (1, 42, 1337, 99999):
            cfg = ProfileConfig(
                profile_name=f"canary{seed}",
                user_data_dir=tempfile.mkdtemp(),
                seed=seed,
            )
            gen = IdentityGenerator(cfg)
            fp = gen.generate()
            result = validate_fingerprint(fp)
            self.assertTrue(
                result["consistent"],
                f"seed={seed} issues: {result['issues']}",
            )

    def test_generated_fingerprint_has_required_keys(self):
        """Fingerprint dict carries all keys the engine consumes."""
        from stealth_engine.identity import IdentityGenerator

        cfg = ProfileConfig(
            profile_name="c", user_data_dir=tempfile.mkdtemp(), seed=5
        )
        fp = IdentityGenerator(cfg).generate()
        for key in (
            "user_agent", "viewport", "screen", "locale", "timezone_id",
            "platform", "hardware_concurrency", "device_memory",
        ):
            self.assertIn(key, fp)
            self.assertIsNotNone(fp[key])


if __name__ == "__main__":
    unittest.main()
