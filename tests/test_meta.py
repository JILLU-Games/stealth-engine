"""PH-17 orchestration/meta tests."""

from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from stealth_engine import ProfileConfig, ban_risk_score
from stealth_engine.engine import StealthEngine
from stealth_engine.identity import IdentityGenerator
from stealth_engine.risk import _SOFTWARE_RENDERERS  # noqa: F401 (re-export check)


def _cfg(**kw) -> ProfileConfig:
    tmp = tempfile.mkdtemp()
    return ProfileConfig(
        profile_name="p", user_data_dir=str(Path(tmp) / "p"), seed=11, **kw
    )


class DiversityTests(unittest.TestCase):
    def test_launch_salt_changes_effective_seed(self):
        cfg = _cfg()
        g1 = IdentityGenerator(cfg, launch_salt="aaa")
        g2 = IdentityGenerator(cfg, launch_salt="bbb")
        g3 = IdentityGenerator(cfg)  # no salt
        self.assertIsNotNone(g1._effective_seed)
        self.assertNotEqual(g1._effective_seed, g2._effective_seed)
        self.assertEqual(g3._effective_seed, 11)
        # RNG streams diverge
        self.assertNotEqual(g1._rng.random(), g2._rng.random())

    def test_no_salt_keeps_seed_reproducibility(self):
        cfg = _cfg()
        a = IdentityGenerator(cfg)
        b = IdentityGenerator(cfg)
        self.assertEqual(a._effective_seed, b._effective_seed)
        self.assertEqual(a._rng.random(), b._rng.random())


class DriftDetectionTests(unittest.TestCase):
    def _engine(self, **kw):
        return StealthEngine(_cfg(**kw))

    def test_first_record_no_drift(self):
        engine = self._engine()
        drifted = engine._record_fingerprint()
        self.assertFalse(drifted)
        hist_path = Path(engine._session.profile_dir) / "fingerprint_history.json"
        self.assertTrue(hist_path.exists())
        data = json.loads(hist_path.read_text())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["hash"], engine._identity.fingerprint_hash())

    def test_same_hash_no_drift_second_time(self):
        engine = self._engine()
        engine._record_fingerprint()
        drifted = engine._record_fingerprint()
        self.assertFalse(drifted)

    def test_tampered_history_reports_drift(self):
        engine = self._engine()
        engine._record_fingerprint()
        hist_path = Path(engine._session.profile_dir) / "fingerprint_history.json"
        data = json.loads(hist_path.read_text())
        data[-1]["hash"] = "0" * 64  # pretend previous launch differed
        hist_path.write_text(json.dumps(data))
        drifted = engine._record_fingerprint()
        self.assertTrue(drifted)

    def test_history_capped_at_50(self):
        engine = self._engine()
        hist_path = Path(engine._session.profile_dir) / "fingerprint_history.json"
        hist_path.parent.mkdir(parents=True, exist_ok=True)
        hist_path.write_text(json.dumps([{"hash": "x"}] * 60))
        engine._record_fingerprint()
        data = json.loads(hist_path.read_text())
        self.assertEqual(len(data), 50)


_GOOD_PROBE = {
    "canvas_hash": "100:abc",
    "webgl_renderer": "ANGLE (NVIDIA GeForce RTX 3060)",
    "user_agent": "Mozilla/5.0",
    "language": "en-US",
    "languages": ["en-US", "en"],
    "hardware_concurrency": 8,
    "device_memory": 8,
    "max_touch_points": 0,
    "gamepad_count": 0,
    "has_usb": False,
    "has_serial": False,
    "notification_permission": "default",
    "timezone": "America/New_York",
}


class RiskScoreTests(unittest.TestCase):
    def test_good_probe_low_risk(self):
        result = ban_risk_score(_GOOD_PROBE)
        self.assertEqual(result["level"], "low")
        self.assertLessEqual(result["score"], 30)

    def test_software_renderer_high_risk(self):
        probe = dict(_GOOD_PROBE, webgl_renderer="WebKit WebGL SwiftShader")
        result = ban_risk_score(probe)
        self.assertEqual(result["level"], "high")
        self.assertGreaterEqual(result["score"], 61)

    def test_missing_fields_raise_score(self):
        result = ban_risk_score({})
        self.assertGreater(result["score"], ban_risk_score(_GOOD_PROBE)["score"])
        self.assertTrue(result["signals"])

    def test_timezone_mismatch_with_geo(self):
        from stealth_engine.proxy import GeoInfo
        geo = GeoInfo(
            ip="1.2.3.4", country="DE", timezone_id="Europe/Berlin",
            locale="de-DE", currency="EUR",
        )
        result = ban_risk_score(_GOOD_PROBE, geo=geo)
        self.assertTrue(any("timezone mismatch" in s for s in result["signals"]))

    def test_score_capped_at_100(self):
        bad = {k: None for k in _GOOD_PROBE}
        result = ban_risk_score(bad)
        self.assertLessEqual(result["score"], 100)


if __name__ == "__main__":
    unittest.main()
