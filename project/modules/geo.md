# Module: geo.py

**File:** `stealth_engine/geo.py`
**Status:** ✅ Implemented (PH-09, extended PH-10)
**Public names:** `GeoResolver`, `GeoPolicy`, `GeoDriftMonitor`, `StickyGeoStore`, `matches_geo_policy`, `validate_geo_consistency`

## Purpose

Standalone, browser-independent GeoIP layer. Reusable from any project —
no camoufox/playwright dependency. Complements `proxy.py` (which is
proxy-pool oriented) with direct-IP/host-IP resolution, policy filters,
caching, batching, and consistency checks.

## Public API

### `GeoResolver`

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(*, endpoint\|endpoints, timeout_s, cache_ttl_s, allowed_countries, blocked_countries)` | Configure endpoint(s) — ordered fallback list (default ipinfo), timeout, TTL cache (default 300s), country filters |
| `resolve` | `async (target: ProxyConfig \| None) -> GeoInfo` | Resolve via proxy exit IP, or host IP when `None`; tries endpoints in order |
| `resolve_ip` | `async (ip: str) -> GeoInfo` | Explicit IP lookup via `{endpoint}/{ip}/json` per endpoint |
| `resolve_many` | `async (targets, *, concurrency=5) -> list[GeoInfo \| ProxyError]` | Semaphore-bounded batch; per-item errors collected, not raised |
| `aclose` | `async () -> None` | Close aiohttp session + clear cache; idempotent |

### `GeoPolicy` (PH-10)

Pydantic model: `name`, `allowed_countries`, `blocked_countries`,
`.matches(geo) -> bool`, `.preset(name)` for built-ins:
`"any"`, `"us-strict"` (US only), `"eu"` (EU-27). Unknown preset →
`ConfigError`.

### `matches_geo_policy(geo, *, allowed_countries, blocked_countries) -> bool`

Pure country allow/block check (case-insensitive ISO alpha-2).

### `validate_geo_consistency(geo, config) -> dict`

Compares `GeoInfo.locale`/`timezone_id` against `ProfileConfig.locale`/
`timezone` (only when config sets them and is not `"auto"`). Returns
`{consistent, country, checks, mismatches}` — never raises.

## Behaviour notes

- Credentials in `ProxyConfig.server` are stripped before the request and
  never appear in URLs, logs, or error details.
- Cache keyed by `proxy:<server>` / `__host__` / `ip:<addr>`; TTL-checked
  on read; cleared by `aclose()`.
- Country-policy rejection raises `ProxyError` with `stage="geo_policy"`.
- Reuses `parse_geo_data()` and `ProxyManager`'s credential helpers from
  `proxy.py` — single parsing/credential code path.
- **Multi-provider fallback (PH-10):** `endpoint`/`endpoints` accept an
  ordered list; each request tries endpoints in order and falls back on
  `ProxyError`. Total failure raises the last error with an `attempts`
  detail. Response parsing auto-detects ipinfo vs ip-api shapes.
- **Extended GeoInfo (PH-10):** `region`, `city`, `latitude`, `longitude`
  are populated when the provider returns them (ipinfo `loc` "lat,lon"
  string or ip-api `lat`/`lon`); otherwise `None`.

## Change History

| Version | Change |
|---|---|
| PH-09 | Initial implementation — resolver, filters, cache, batch, validator |
| PH-10 | Multi-endpoint fallback, `GeoPolicy` presets, extended GeoInfo parsing |
| PH-18 | `StickyGeoStore` (account→proxy+geo JSON bindings) + `GeoDriftMonitor` (per-target geo-change detection) |
| BF-02 | `resolve_ip` endpoint normalization — strips trailing `/json`, tries both `/{ip}/json` and `/json/{ip}` provider shapes (B-17 fix) |
