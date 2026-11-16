"""PH-20 ghost-layer tests."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from stealth_engine.config import ProfileConfig
from stealth_engine.engine import (
    BrowserSession,
    StealthEngine,
    _js_noise_init_script,
    _WARMUP_TEMPLATES,
)
from stealth_engine.exceptions import AutomationError
from stealth_engine.session import SessionManager


class JsNoiseTests(unittest.TestCase):
    def test_script_contains_patches(self):
        js = _js_noise_init_script(42)
        self.assertIn("toDataURL", js)
        self.assertIn("getImageData", js)
        self.assertIn("readPixels", js)
        self.assertTrue(
            "0x6D2B79F5" in js or "mulberry" in js.lower()
        )

    def test_deterministic_per_seed(self):
        self.assertEqual(
            _js_noise_init_script(7), _js_noise_init_script(7)
        )
        self.assertNotEqual(
            _js_noise_init_script(7), _js_noise_init_script(8)
        )

    def test_none_seed_safe(self):
        js = _js_noise_init_script(None)
        self.assertIn("readPixels", js)


class _FakePage:
    pass


class _FakeCtx:
    def __init__(self):
        self.pages = []
        self.routes = []

    def new_page(self):
        return _FakePage()

    async def route(self, pattern, handler):
        self.routes.append((pattern, handler))

    async def close(self):
        pass


class _FakeHandle:
    async def __aexit__(self, *a):
        pass


def _session(**cfg_kw) -> BrowserSession:
    tmp = tempfile.mkdtemp()
    cfg = ProfileConfig(
        profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=1, **cfg_kw
    )
    return BrowserSession(
        ctx=_FakeCtx(),
        ctx_handle=_FakeHandle(),
        session=SessionManager(cfg, base_dir=tmp),
        proxy_manager=None,
        config=cfg,
    )


class WarmupTemplateTests(unittest.IsolatedAsyncioTestCase):
    async def test_unknown_template_raises(self):
        s = _session()
        with self.assertRaises(AutomationError) as ctx:
            await s.warmup("https://example.com", template="nope")
        self.assertIn("template", str(ctx.exception))

    def test_presets_exist(self):
        for name in ("default", "social", "commerce", "search"):
            self.assertIn(name, _WARMUP_TEMPLATES)
        self.assertGreater(
            _WARMUP_TEMPLATES["social"]["scrolls"],
            _WARMUP_TEMPLATES["search"]["scrolls"],
        )


class BlockTrackersTests(unittest.IsolatedAsyncioTestCase):
    async def test_registers_catch_all_route(self):
        s = _session()
        n = await s.block_trackers()
        self.assertGreater(n, 15)
        self.assertEqual(s.context.routes[0][0], "**/*")

    async def test_extra_domains_counted(self):
        s = _session()
        base = await s.block_trackers()
        s2 = _session()
        n = await s2.block_trackers(extra_domains=["mytracker.io"])
        self.assertEqual(n, base + 1)
        self.assertEqual(s2.context.routes[0][0], "**/*")


class SessionAgeTests(unittest.TestCase):
    def test_no_history_returns_none(self):
        s = _session()
        self.assertIsNone(s.session_age_days())

    def test_age_from_first_history_entry(self):
        s = _session()
        prof = Path(s._session.profile_dir)
        prof.mkdir(parents=True, exist_ok=True)
        old_ts = time.time() - 2 * 86400
        (prof / "fingerprint_history.json").write_text(
            json.dumps([{"ts": old_ts, "hash": "x", "diversity": False}])
        )
        age = s.session_age_days()
        self.assertIsNotNone(age)
        self.assertAlmostEqual(age, 2.0, delta=0.1)


if __name__ == "__main__":
    unittest.main()
