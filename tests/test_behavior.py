"""PH-15 behavioral biometrics tests."""

from __future__ import annotations

import json
import math
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from stealth_engine.behavior import (
    BehaviorProfile,
    bezier_path,
    dwell_plan,
    physics_scroll_chunks,
)
from stealth_engine.engine import BrowserSession


def _profile(seed=1) -> BehaviorProfile:
    return BehaviorProfile(BehaviorProfile._generate(random.Random(seed)))


class _FakeSessionMgr:
    def __init__(self, root: Path):
        self._dir = root

    @property
    def profile_dir(self) -> str:
        return str(self._dir)


def _bs() -> BrowserSession:
    bs = BrowserSession.__new__(BrowserSession)
    bs._rng = random.Random(7)
    bs._behavior = _profile(7)
    return bs


class _Mouse:
    def __init__(self):
        self.position = {"x": 10.0, "y": 10.0}
        self.moves = []
        self.wheels = []

    def move(self, x, y):
        self.moves.append((x, y))
        self.position = {"x": x, "y": y}

    def wheel(self, dx, dy):
        self.wheels.append((dx, dy))

    async def amove(self, x, y):
        self.move(x, y)

    async def awheel(self, dx, dy):
        self.wheel(dx, dy)


class _SyncPage:
    def __init__(self):
        self.mouse = _Mouse()
        self.keyboard = Mock()
        self.keyboard.type = Mock()

    def click(self, sel):
        pass


class _AsyncMouse:
    def __init__(self):
        self.position = {"x": 0.0, "y": 0.0}
        self.moves = []
        self.wheels = []

    async def move(self, x, y):
        self.moves.append((x, y))
        self.position = {"x": x, "y": y}

    async def wheel(self, dx, dy):
        self.wheels.append((dx, dy))


class _AsyncPage:
    def __init__(self):
        self.mouse = _AsyncMouse()
        self.clicks = []

    async def click(self, sel):
        self.clicks.append(sel)


class BezierPathTests(unittest.TestCase):
    def test_path_endpoints_exact(self):
        path = bezier_path(0, 0, 100, 50, random.Random(1))
        self.assertAlmostEqual(path[0][0], 0)
        self.assertAlmostEqual(path[0][1], 0)
        self.assertEqual(path[-1], (100, 50))

    def test_path_is_curved_not_linear(self):
        # Straight line would have midpoint exactly on the diagonal.
        path = bezier_path(0, 0, 200, 0, random.Random(3), steps=20)
        mid = path[10][1]
        self.assertNotAlmostEqual(mid, 0.0, places=1)  # bowed off-axis

    def test_short_distance_min_steps(self):
        path = bezier_path(5, 5, 8, 9, random.Random(1))
        self.assertGreaterEqual(len(path), 2)


class BehaviorProfilePersistenceTests(unittest.TestCase):
    def test_load_or_create_persists(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            mgr = _FakeSessionMgr(root)
            bp = BehaviorProfile.load_or_create(mgr, seed=42)
            self.assertTrue((root / "behavior.json").exists())
            # Second load returns same values
            bp2 = BehaviorProfile.load_or_create(mgr, seed=99)
            self.assertEqual(bp.data, bp2.data)

    def test_corrupt_file_regenerates(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "behavior.json").write_text("{bad json", encoding="utf-8")
            mgr = _FakeSessionMgr(root)
            bp = BehaviorProfile.load_or_create(mgr, seed=1)
            self.assertIn("typing", bp.data)

    def test_invalid_shape_regenerates(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "behavior.json").write_text(json.dumps({"foo": 1}))
            mgr = _FakeSessionMgr(root)
            bp = BehaviorProfile.load_or_create(mgr, seed=1)
            self.assertIn("mouse", bp.data)

    def test_typing_delay_in_range(self):
        bp = _profile(5)
        rng = random.Random(5)
        delays = [bp.typing_delay(rng, "a") for _ in range(50)]
        self.assertTrue(all(0.02 < d < 0.25 for d in delays))
        # space can trigger word pause → occasionally larger
        space_delays = [bp.typing_delay(rng, " ") for _ in range(50)]
        self.assertTrue(max(space_delays) > max(delays))

    def test_scroll_plan_sums_to_dy(self):
        bp = _profile(3)
        plan = bp.scroll_plan(300, random.Random(3))
        total = sum(d for d, _ in plan)
        self.assertAlmostEqual(total, 300, delta=30)

    def test_physics_chunks_decay(self):
        chunks = physics_scroll_chunks(
            300, random.Random(1),
            {"chunks": [4, 4], "pause_s": [0.05, 0.1], "decay": 0.85},
        )
        self.assertTrue(3 <= len(chunks) <= 4)
        first = abs(chunks[0][0]); last = abs(chunks[-1][0])
        self.assertGreater(first, last * 0.5)  # deceleration present


class DwellPlanTests(unittest.TestCase):
    def test_dwell_plan_segments(self):
        plan = dwell_plan(random.Random(1), 2.0, 5.0)
        self.assertGreaterEqual(len(plan), 2)
        total = sum(d for _, d in plan)
        self.assertGreaterEqual(total, 2.0)
        self.assertLessEqual(total, 5.5)
        kinds = {k for k, _ in plan}
        self.assertTrue(kinds <= {"sleep", "jiggle"})


class HookIntegrationTests(unittest.TestCase):
    """PF-02/B-25: sync hooks raise AutomationError — the session
    context is always async, so sync playwright calls can never run.
    The async ahuman_*/adwell variants are the working API."""

    def test_sync_hooks_raise_automation_error(self):
        from stealth_engine.exceptions import AutomationError

        bs = _bs()
        page = _SyncPage()
        for call in (
            lambda: bs.human_move(page, 100, 100),
            lambda: bs.human_type(page, "#i", "ab"),
            lambda: bs.human_scroll(page, 240),
            lambda: bs.human_dwell(page),
        ):
            with self.assertRaises(AutomationError):
                call()


class AsyncHookTests(unittest.IsolatedAsyncioTestCase):
    async def test_adwell_runs(self):
        bs = _bs()
        page = _AsyncPage()
        # Short dwell for test speed
        await bs.adwell(page, 0.05, 0.1)

    async def test_ahuman_move_bezier(self):
        bs = _bs()
        page = _AsyncPage()
        await bs.ahuman_move(page, 50, 50)
        # async mouse has no .position dict attr — hook falls back to 0,0
        self.assertTrue(page.mouse.moves)


if __name__ == "__main__":
    unittest.main()
