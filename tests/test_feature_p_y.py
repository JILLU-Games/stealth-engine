"""Focused tests for Feature P (pluggable identity) and Feature Y (YAML/JSON)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stealth_engine import (
    BrowserForgeIdentityProvider,
    ProfileConfig,
    ProxyConfig,
)
from stealth_engine.identity import IdentityGenerator


def _valid_fp(**overrides) -> dict:
    fp = {
        "user_agent": "CustomAgent/1.0",
        "viewport": {"width": 1280, "height": 720},
        "screen": {"width": 1920, "height": 1080},
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "platform": "Win32",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "color_scheme": "light",
        "reduced_motion": "no-preference",
        "is_mobile": False,
        "has_touch": False,
    }
    fp.update(overrides)
    return fp


class _FixedProvider:
    """Minimal IdentityProvider returning a fixed fingerprint."""

    def __init__(self, fp: dict) -> None:
        self._fp = fp
        self.calls = 0

    def build(self, config, rng):
        self.calls += 1
        return dict(self._fp)


class FeatureP_Tests(unittest.TestCase):
    def test_custom_provider_supplies_fingerprint(self) -> None:
        provider = _FixedProvider(_valid_fp())
        config = ProfileConfig(
            profile_name="p", user_data_dir="p", seed=1
        )
        gen = IdentityGenerator(config, provider=provider)
        fp = gen.generate()
        self.assertEqual(fp["user_agent"], "CustomAgent/1.0")
        self.assertEqual(provider.calls, 1)
        # Cached: second call does not re-invoke provider.
        gen.generate()
        self.assertEqual(provider.calls, 1)

    def test_config_overrides_apply_to_custom_provider(self) -> None:
        provider = _FixedProvider(_valid_fp(locale="en-US", timezone_id="UTC"))
        config = ProfileConfig(
            profile_name="p",
            user_data_dir="p",
            locale="fr-FR",
            timezone="Europe/Paris",
        )
        fp = IdentityGenerator(config, provider=provider).generate()
        self.assertEqual(fp["locale"], "fr-FR")
        self.assertEqual(fp["timezone_id"], "Europe/Paris")

    def test_invalid_provider_output_rejected(self) -> None:
        provider = _FixedProvider({"user_agent": "x"})
        config = ProfileConfig(profile_name="p", user_data_dir="p")
        from stealth_engine.exceptions import IdentityError

        with self.assertRaises(IdentityError):
            IdentityGenerator(config, provider=provider).generate()

    def test_default_provider_is_browserforge(self) -> None:
        config = ProfileConfig(profile_name="p", user_data_dir="p", seed=7)
        gen = IdentityGenerator(config)
        self.assertIsInstance(gen._provider, BrowserForgeIdentityProvider)

    def test_engine_accepts_identity_provider(self) -> None:
        from stealth_engine.engine import StealthEngine

        provider = _FixedProvider(_valid_fp())
        config = ProfileConfig(profile_name="p", user_data_dir="p")
        engine = StealthEngine(config, identity_provider=provider)
        self.assertIs(engine._identity._provider, provider)


class FeatureY_Tests(unittest.TestCase):
    def _sample_config(self) -> ProfileConfig:
        return ProfileConfig(
            profile_name="acct_1",
            user_data_dir="/tmp/profiles/acct_1",
            os="linux",
            proxy=ProxyConfig(server="http://user:secret@1.2.3.4:8080"),
            geoip=False,
            seed=42,
            headless=False,
            locale="de-DE",
            timezone="Europe/Berlin",
            extra_headers={"X-Test": "yes"},
            log_level="DEBUG",
            schema_version="1",
            target_ip="203.0.113.9",
        )

    def test_json_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            cfg = self._sample_config()
            path = Path(d) / "profile.json"
            cfg.save_json(path)
            loaded = ProfileConfig.load_json(path)
            self.assertEqual(loaded, cfg)
            # Embedded proxy credentials survive the round trip in server.
            self.assertEqual(
                loaded.proxy.server, "http://user:secret@1.2.3.4:8080"
            )

    def test_yaml_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            cfg = self._sample_config()
            path = Path(d) / "profile.yaml"
            cfg.save_yaml(path)
            loaded = ProfileConfig.load_yaml(path)
            self.assertEqual(loaded, cfg)
            self.assertEqual(loaded.proxy.server, "http://user:secret@1.2.3.4:8080")

    def test_yaml_file_is_plain_yaml(self) -> None:
        import yaml

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.yml"
            self._sample_config().save_yaml(path)
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertIsInstance(data, dict)
            self.assertEqual(data["profile_name"], "acct_1")

    def test_json_file_is_pretty_printed(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            self._sample_config().save_json(path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("\n", text)
            json.loads(text)  # must parse

    def test_load_rejects_invalid_file(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.json"
            path.write_text('{"profile_name": ""}', encoding="utf-8")
            from pydantic import ValidationError

            with self.assertRaises(ValidationError):
                ProfileConfig.load_json(path)

    def test_minimal_config_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            cfg = ProfileConfig(profile_name="min", user_data_dir="min")
            for suffix, save, load in (
                (".json", cfg.save_json, ProfileConfig.load_json),
                (".yaml", cfg.save_yaml, ProfileConfig.load_yaml),
            ):
                path = Path(d) / f"min{suffix}"
                save(path)
                self.assertEqual(load(path), cfg)


if __name__ == "__main__":
    unittest.main()
