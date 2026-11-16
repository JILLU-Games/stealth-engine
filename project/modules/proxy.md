# Module: proxy.py

**File:** `stealth_engine/proxy.py`
**Status:** ✅ Implemented (v0.1.0)
**Public names:** `GeoInfo`, `ProxyManager`, `parse_geo_data`

## Purpose

Proxy rotation, health checking, failover, and GeoIP-based locale/currency/timezone matching.
All network calls share a single `aiohttp.ClientSession` (lazy-created, connection-pooled).

## Public API

### GeoInfo (Pydantic BaseModel)

| Field       | Type               | Description                             |
| ----------- | ------------------ | --------------------------------------- |
| ip          | str                | Public exit IP seen by geo endpoint     |
| country     | ISO 3166-1 alpha-2 | Country code (e.g. "US")                |
| timezone_id | str                | IANA timezone (e.g. "America/New_York") |
| locale      | str                | BCP-47 locale derived from country      |
| currency    | str                | ISO 4217 currency derived from country  |
| region      | str \| None        | Region/state name (PH-10; provider-dependent) |
| city        | str \| None        | City name (PH-10; provider-dependent)    |
| latitude    | float \| None      | Exit-IP latitude (PH-10)                |
| longitude   | float \| None      | Exit-IP longitude (PH-10)               |

### ProxyManager

| Method          | Signature                                     | Description                                                                           |
| --------------- | --------------------------------------------- | ------------------------------------------------------------------------------------- |
| `__init__`      | `(proxies, *, geo_endpoint, timeout_s, seed, allowed_countries, blocked_countries, cache_ttl_s, geo_retries, health_threshold_ms)` | Store pool, seeded RNG, lazy session, country filters, GeoIP cache, retries, health threshold |
| `resolve_geo`   | `async (proxy) -> GeoInfo`                    | GET geo_endpoint through proxy, parse JSON                                            |
| `health_check`  | `async (proxy) -> float`                      | Time a full resolve_geo; return latency_ms                                            |
| `pick_healthy`  | `async () -> tuple[ProxyConfig, GeoInfo]`     | Shuffle + try each; return first under `health_threshold_ms`                                        |
| `to_playwright` | `(proxy) -> dict`                             | Playwright-compatible proxy dict (no None values)                                     |
| `mask`          | `(proxy) -> dict`                             | Log-safe proxy dict; URL credentials are removed and passwords replaced with "\*\*\*" |
| `aclose`        | `async () -> None`                            | Close aiohttp session; idempotent                                                     |

## Behaviour Details

- **Session**: created lazily on first network call; never per-request.
- **Rotation**: `pick_healthy()` shuffles with `self._rng` (seeded or OS-random), tries in order.
- **Concurrency**: `asyncio.Lock` serialises access to the proxy list copy in `pick_healthy`.
- **Geo fallback**: Unknown country → locale `"en-US"`, currency `"USD"`. Never raises.
- **Country filter (PH-09)**: `allowed_countries`/`blocked_countries` (ISO alpha-2, case-insensitive) are enforced inside `pick_healthy()` — non-matching proxies are skipped like failed health checks.
- **GeoIP cache (PH-09)**: `cache_ttl_s > 0` caches `resolve_geo` results per proxy `server` URL; `0` disables. Cleared by `aclose()`.
| `load_proxies(path)` | module function | Parse proxy pool file — `host:port:user:pass`, `user:pass@host:port`, `scheme://` URL, comments/`#` skipped (PH-18, N1) |

- **Retries + threshold (PH-11)**: `geo_retries` adds attempts for transient `resolve_geo` failures (linear 0.3s backoff, `attempt` in error details); `health_threshold_ms` replaces the hardcoded 5000 ms pick cutoff.
- **Pool file import (PH-18)**: `load_proxies(path)` supports common provider formats; bad lines raise `ProxyError` with 1-based line numbers.
- **Shared parser**: `_parse_geo` delegates to module-level `parse_geo_data()` so `geo.GeoResolver` reuses identical parsing/validation. PH-10: `parse_geo_data` auto-detects ipinfo vs ip-api response shapes and populates extended `GeoInfo` fields (`region`, `city`, `latitude`, `longitude`) when present.
- **Credential safety**: URL-embedded credentials are split from the server address; aiohttp receives credentials through `proxy_auth`, and Playwright receives separate `username` / `password` fields. `ProfileConfig.to_public_dict()`, log values, and exception details use redacted server data.
- **TLS**: GeoIP requests use aiohttp's default TLS certificate verification.

## Static Mapping Tables

- `_COUNTRY_LOCALE`: 50+ country → BCP-47 locale entries
- `_COUNTRY_CURRENCY`: 50+ country → ISO 4217 currency entries

## Does NOT

- Cache health check results
- Add retry loops
- Launch or import camoufox/playwright
- Modify ProfileConfig

## Change History

| Version | Change                                                                  |
| ------- | ----------------------------------------------------------------------- |
| 0.1.0   | Initial implementation — Phase 4                                        |
| 0.1.0   | Strip embedded URL credentials from server URLs and redact them in logs |
| 0.1.0   | Keep TLS certificate verification enabled for GeoIP requests            |
| PH-09   | Added `allowed_countries`/`blocked_countries` filters, `cache_ttl_s` GeoIP cache, `parse_geo_data()` shared parser |
| PH-10   | `GeoInfo` extended fields (`region`/`city`/`latitude`/`longitude`); `parse_geo_data` auto-detects ipinfo + ip-api shapes |
| PH-11   | `geo_retries` + `health_threshold_ms` params; retry loop in `resolve_geo`; configurable pick cutoff |

BF-03: `resolve_geo` wraps unexpected exceptions in `ProxyError` (was leaking raw errors); geo cache keyed by masked server (credentials no longer sit in `_geo_cache`); `pick_healthy` docstring updated to `health_threshold_ms`.
