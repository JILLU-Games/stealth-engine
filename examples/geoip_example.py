"""GeoIP usage example — standalone resolver + engine integration.

Run:  python examples/geoip_example.py

Demonstrates:
- GeoResolver: host-IP geo lookup with multi-endpoint fallback + cache
- GeoPolicy presets for country filtering
- validate_geo_consistency for config-vs-geo checks
- ProfileConfig "auto" locale/timezone sentinel (engine integration)
"""

import asyncio

from stealth_engine import (
    GeoInfo,
    GeoPolicy,
    GeoResolver,
    ProfileConfig,
    ProxyConfig,
    validate_geo_consistency,
)


async def demo_resolver() -> None:
    """Standalone GeoIP resolution — no browser involved."""
    async with GeoResolver(
        endpoints=[
            "https://ipinfo.io/json",
            "https://ip-api.com/json",
        ],
        cache_ttl_s=300,
        allowed_countries=["US", "CA", "GB", "DE", "FR"],
    ) as resolver:
        geo = await resolver.resolve()  # host IP
        print(f"host geo: {geo.ip} {geo.country} {geo.locale} "
              f"{geo.timezone_id} {geo.city or ''}")

        policy = GeoPolicy.preset("us-strict")
        print(f"us-strict match: {policy.matches(geo)}")

        # Batch resolve example (empty list = no-op here)
        results = await resolver.resolve_many([])
        print(f"batch results: {len(results)}")


def demo_config() -> None:
    """ProfileConfig with "auto" geo-derived locale/timezone."""
    cfg = ProfileConfig(
        profile_name="demo",
        user_data_dir="./profiles/demo",
        proxy=ProxyConfig(server="http://user:pass@proxy.example:8080"),
        geoip=True,
        locale="auto",
        timezone="auto",
        seed=42,
    )
    # Round-trip through YAML to show Feature Y together.
    import pathlib, tempfile
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "demo.yaml"
        cfg.save_yaml(p)
        loaded = ProfileConfig.load_yaml(p)
        print(f"yaml round-trip ok: {loaded.locale == 'auto'}")

    report = validate_geo_consistency(
        # synthetic geo for demonstration
        GeoInfo(
            ip="1.2.3.4", country="US",
            timezone_id="America/New_York", locale="en-US", currency="USD",
        ),
        cfg,
    )
    print(f"consistency: {report['consistent']} mismatches={report['mismatches']}")


async def main() -> None:
    await demo_resolver()
    demo_config()


if __name__ == "__main__":
    asyncio.run(main())
