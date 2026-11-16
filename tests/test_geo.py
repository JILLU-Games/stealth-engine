"""Focused tests for PH-09 GeoIP core (GeoResolver, filters, cache, batch, validator)."""

from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from stealth_engine import (
    GeoPolicy,
    GeoResolver,
    ProfileConfig,
    ProxyConfig,
    matches_geo_policy,
    validate_geo_consistency,
)
from stealth_engine.exceptions import ConfigError, ProxyError
from stealth_engine.proxy import GeoInfo, ProxyManager, parse_geo_data


def _geo(country="US", **kw) -> GeoInfo:
    base = dict(
        ip="203.0.113.1",
        country=country,
        timezone_id="America/New_York",
        locale="en-US",
        currency="USD",
    )
    base.update(kw)
    return GeoInfo(**base)


class _FakeResp:
    def __init__(self, payload, status=200):
        self.status = status
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return None

    async def json(self, **kw):
        return self._payload


_GEO_JSON = {"ip": "203.0.113.1", "country": "US", "timezone": "America/New_York"}


def _session_with(payload=_GEO_JSON, status=200, calls=None):
    resp = _FakeResp(payload, status)

    def _get(url, **kw):
        if calls is not None:
            calls.append((url, kw))
        return resp

    return SimpleNamespace(
        get=Mock(side_effect=_get), closed=False, close=AsyncMock()
    )


class ParseGeoDataTests(unittest.TestCase):
    def test_parse_ok(self):
        geo = parse_geo_data(_GEO_JSON)
        self.assertEqual(geo.country, "US")
        self.assertEqual(geo.locale, "en-US")
        self.assertEqual(geo.currency, "USD")

    def test_parse_missing_fields(self):
        with self.assertRaises(ProxyError):
            parse_geo_data({"country": "US"})

    def test_parse_extended_ipinfo_fields(self):
        geo = parse_geo_data({
            "ip": "1.2.3.4", "country": "DE", "timezone": "Europe/Berlin",
            "region": "Bavaria", "city": "Munich", "loc": "48.137,11.575",
        })
        self.assertEqual(geo.region, "Bavaria")
        self.assertEqual(geo.city, "Munich")
        self.assertAlmostEqual(geo.latitude, 48.137)
        self.assertAlmostEqual(geo.longitude, 11.575)

    def test_parse_extended_ipapi_shape(self):
        geo = parse_geo_data({
            "status": "success", "country": "Germany", "countryCode": "DE",
            "timezone": "Europe/Berlin", "query": "5.6.7.8",
            "regionName": "Bavaria", "city": "Munich",
            "lat": 48.1, "lon": 11.5,
        })
        self.assertEqual(geo.ip, "5.6.7.8")
        self.assertEqual(geo.country, "DE")
        self.assertEqual(geo.region, "Bavaria")
        self.assertEqual(geo.city, "Munich")
        self.assertAlmostEqual(geo.latitude, 48.1)
        self.assertAlmostEqual(geo.longitude, 11.5)

    def test_parse_extended_fields_optional(self):
        geo = parse_geo_data(_GEO_JSON)
        self.assertIsNone(geo.region)
        self.assertIsNone(geo.city)
        self.assertIsNone(geo.latitude)
        self.assertIsNone(geo.longitude)


class MatchesGeoPolicyTests(unittest.TestCase):
    def test_allowed(self):
        geo = _geo("DE")
        self.assertTrue(matches_geo_policy(geo, allowed_countries=["DE", "AT"]))
        self.assertFalse(matches_geo_policy(geo, allowed_countries=["US"]))

    def test_blocked(self):
        geo = _geo("RU")
        self.assertFalse(matches_geo_policy(geo, blocked_countries=["ru"]))
        self.assertTrue(matches_geo_policy(geo, blocked_countries=["CN"]))

    def test_case_insensitive(self):
        geo = _geo("de")
        self.assertTrue(matches_geo_policy(geo, allowed_countries=["dE"]))


class ValidateGeoConsistencyTests(unittest.TestCase):
    def test_consistent(self):
        geo = _geo("US", locale="en-US", timezone_id="America/New_York")
        cfg = ProfileConfig(
            profile_name="p", user_data_dir="p",
            locale="en-US", timezone="America/New_York",
        )
        report = validate_geo_consistency(geo, cfg)
        self.assertTrue(report["consistent"])
        self.assertEqual(report["mismatches"], [])

    def test_mismatch(self):
        geo = _geo("DE", locale="de-DE", timezone_id="Europe/Berlin")
        cfg = ProfileConfig(
            profile_name="p", user_data_dir="p",
            locale="en-US", timezone="America/New_York",
        )
        report = validate_geo_consistency(geo, cfg)
        self.assertFalse(report["consistent"])
        self.assertEqual(sorted(report["mismatches"]), ["locale", "timezone_id"])

    def test_unset_fields_skipped(self):
        geo = _geo()
        cfg = ProfileConfig(profile_name="p", user_data_dir="p")
        report = validate_geo_consistency(geo, cfg)
        self.assertTrue(report["consistent"])
        self.assertEqual(report["checks"]["locale"]["status"], "skipped")


class GeoResolverTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolve_direct_host(self):
        calls = []
        resolver = GeoResolver(cache_ttl_s=0)
        resolver._session = _session_with(calls=calls)
        geo = await resolver.resolve(None)
        self.assertEqual(geo.country, "US")
        url, kw = calls[0]
        self.assertIsNone(kw.get("proxy"))
        self.assertIsNone(kw.get("proxy_auth"))

    async def test_resolve_via_proxy_strips_credentials(self):
        calls = []
        resolver = GeoResolver(cache_ttl_s=0)
        resolver._session = _session_with(calls=calls)
        proxy = ProxyConfig(server="http://user:secret@host:8080")
        await resolver.resolve(proxy)
        url, kw = calls[0]
        self.assertEqual(kw["proxy"], "http://host:8080")
        self.assertIsNotNone(kw["proxy_auth"])
        self.assertNotIn("secret", repr(kw["proxy"]))

    async def test_cache_hit_skips_http(self):
        calls = []
        resolver = GeoResolver(cache_ttl_s=300)
        resolver._session = _session_with(calls=calls)
        await resolver.resolve(None)
        await resolver.resolve(None)
        self.assertEqual(len(calls), 1)

    async def test_cache_disabled(self):
        calls = []
        resolver = GeoResolver(cache_ttl_s=0)
        resolver._session = _session_with(calls=calls)
        await resolver.resolve(None)
        await resolver.resolve(None)
        self.assertEqual(len(calls), 2)

    async def test_allowed_country_rejects(self):
        resolver = GeoResolver(cache_ttl_s=0, allowed_countries=["DE"])
        resolver._session = _session_with()
        with self.assertRaises(ProxyError):
            await resolver.resolve(None)

    async def test_blocked_country_rejects(self):
        resolver = GeoResolver(cache_ttl_s=0, blocked_countries=["US"])
        resolver._session = _session_with()
        with self.assertRaises(ProxyError):
            await resolver.resolve(None)

    async def test_resolve_ip_uses_ip_path(self):
        calls = []
        resolver = GeoResolver(cache_ttl_s=0)
        resolver._session = _session_with(calls=calls)
        await resolver.resolve_ip("8.8.8.8")
        url, kw = calls[0]
        self.assertTrue(url.endswith("/8.8.8.8/json"))

    async def test_resolve_many_collects_errors(self):
        resolver = GeoResolver(cache_ttl_s=0)
        good = _session_with()
        resolver._session = good
        proxy = ProxyConfig(server="http://h:1")
        results = await resolver.resolve_many([None, None], concurrency=2)
        self.assertTrue(all(isinstance(r, GeoInfo) for r in results))

    async def test_resolve_many_bad_target_returns_error(self):
        resolver = GeoResolver(cache_ttl_s=0)
        resolver._session = _session_with(status=500)
        results = await resolver.resolve_many([None], concurrency=1)
        self.assertIsInstance(results[0], ProxyError)

    async def test_aclose_clears_cache_and_session(self):
        resolver = GeoResolver(cache_ttl_s=300)
        resolver._session = _session_with()
        await resolver.resolve(None)
        self.assertTrue(resolver._cache)
        await resolver.aclose()
        self.assertFalse(resolver._cache)

    async def test_negative_ttl_rejected(self):
        with self.assertRaises(ProxyError):
            GeoResolver(cache_ttl_s=-1)


class ProxyManagerFilterTests(unittest.IsolatedAsyncioTestCase):
    async def test_pick_healthy_skips_disallowed_country(self):
        de_geo = _geo("DE", locale="de-DE", timezone_id="Europe/Berlin")
        manager = ProxyManager(
            [ProxyConfig(server="http://a:1"), ProxyConfig(server="http://b:2")],
            allowed_countries=["DE"],
        )
        manager.resolve_geo = AsyncMock(return_value=de_geo)
        proxy, geo = await manager.pick_healthy()
        self.assertEqual(geo.country, "DE")

    async def test_pick_healthy_all_filtered_raises(self):
        manager = ProxyManager(
            [ProxyConfig(server="http://a:1")],
            blocked_countries=["US"],
        )
        manager.resolve_geo = AsyncMock(return_value=_geo("US"))
        with self.assertRaises(ProxyError):
            await manager.pick_healthy()

    async def test_manager_cache_ttl(self):
        calls = []
        manager = ProxyManager(
            [ProxyConfig(server="http://h:1")], cache_ttl_s=300
        )
        manager._session = _session_with(calls=calls)
        proxy = manager._proxies[0]
        await manager.resolve_geo(proxy)
        await manager.resolve_geo(proxy)
        self.assertEqual(len(calls), 1)


class GeoPolicyTests(unittest.TestCase):
    def test_preset_any(self):
        policy = GeoPolicy.preset("any")
        self.assertTrue(policy.matches(_geo("US")))
        self.assertTrue(policy.matches(_geo("KP")))

    def test_preset_us_strict(self):
        policy = GeoPolicy.preset("us-strict")
        self.assertTrue(policy.matches(_geo("US")))
        self.assertFalse(policy.matches(_geo("DE")))

    def test_preset_eu(self):
        policy = GeoPolicy.preset("eu")
        self.assertTrue(policy.matches(_geo("DE")))
        self.assertTrue(policy.matches(_geo("FR")))
        self.assertFalse(policy.matches(_geo("US")))

    def test_preset_unknown_raises(self):
        with self.assertRaises(ConfigError):
            GeoPolicy.preset("atlantis")

    def test_custom_policy(self):
        policy = GeoPolicy(name="custom", allowed_countries=["JP"], blocked_countries=["KP"])
        self.assertTrue(policy.matches(_geo("JP")))
        self.assertFalse(policy.matches(_geo("US")))


class GeoResolverFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_multi_endpoint_fallback(self):
        """First endpoint fails → second endpoint's data is used."""
        calls = []

        def _get(url, **kw):
            calls.append(url)
            if "ipinfo" in url:
                return _FakeResp({}, status=500)
            return _FakeResp(_GEO_JSON)

        resolver = GeoResolver(
            endpoints=["https://ipinfo.io/json", "https://backup.example/json"],
            cache_ttl_s=0,
        )
        resolver._session = SimpleNamespace(
            get=Mock(side_effect=_get), closed=False, close=AsyncMock()
        )
        geo = await resolver.resolve(None)
        self.assertEqual(geo.country, "US")
        self.assertEqual(len(calls), 2)

    async def test_all_endpoints_fail_raises_with_attempts(self):
        resolver = GeoResolver(
            endpoints=["https://a.example", "https://b.example"],
            cache_ttl_s=0,
        )
        resolver._session = _session_with(status=500)
        with self.assertRaises(ProxyError) as ctx:
            await resolver.resolve(None)
        self.assertIn("attempts", ctx.exception.details)
        self.assertEqual(len(ctx.exception.details["attempts"]), 2)


class AutoSentinelTests(unittest.TestCase):
    def test_seeds_treat_auto_as_unset(self):
        """locale/timezone="auto" must not persist literally in seeds.json."""
        import tempfile, pathlib
        from stealth_engine.identity import IdentityGenerator

        with tempfile.TemporaryDirectory() as d:
            cfg = ProfileConfig(
                profile_name="x", user_data_dir=d,
                locale="auto", timezone="AUTO",
            )
            seeds = IdentityGenerator(cfg).get_or_create_seeds()
            self.assertNotEqual(seeds["locale"], "auto")
            self.assertNotEqual(seeds["timezone_id"], "auto")
            self.assertIn(seeds["locale_source"], ("host", "fallback"))


class AutoSentinelEngineTests(unittest.IsolatedAsyncioTestCase):
    async def test_auto_locale_uses_proxy_geo_even_when_geoip_false(self):
        """Mode B: locale="auto" derives from proxy GeoIP regardless of
        the cfg.geoip gate (explicit opt-in)."""
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from stealth_engine import StealthEngine

        with tempfile.TemporaryDirectory() as d:
            cfg = ProfileConfig(
                profile_name="profile",
                user_data_dir=str(Path(d) / "profile"),
                proxy=ProxyConfig(server="http://h:1"),
                geoip=False,
                locale="auto",
                seed=1,
            )
            engine = StealthEngine(cfg)
            de_geo = _geo("DE", locale="de-DE", timezone_id="Europe/Berlin")
            proxy_cfg = ProxyConfig(server="http://h:1")

            class FakeContext:
                pages = [object()]
                def storage_state(self):
                    return {"cookies": [], "origins": []}
                async def close(self):
                    return None

            class FakeHandle:
                async def __aenter__(self):
                    return FakeContext()
                async def __aexit__(self, *a):
                    return None

            captured = {}
            def fake_camoufox(**kw):
                captured.update(kw)
                return FakeHandle()

            engine._proxy_manager.pick_healthy = AsyncMock(
                return_value=(proxy_cfg, de_geo)
            )
            with patch("camoufox.async_api.AsyncCamoufox", side_effect=fake_camoufox):
                session = await engine.alaunch()
            try:
                self.assertEqual(captured["locale"], "de-DE")
            finally:
                await session.aclose()


if __name__ == "__main__":
    unittest.main()
