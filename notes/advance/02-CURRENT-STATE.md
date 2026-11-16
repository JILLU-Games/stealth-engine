# 02 — CURRENT STATE (compact forensic snapshot)

Baseline: `stealth_engine` **v0.2.0**, commit `3bb1ca0`, 2026-11-15.

## What exists (verified)

### Core engine
- `StealthEngine` — async `alaunch()` + sync `launch()`, camoufox C++ spoofing
- `BrowserSession` — human hooks (sync + async `ahuman_*`), state export
- `BulkRunner` — semaphore concurrency, retry+backoff+jitter, `task_timeout_s`
- `SessionManager` — isolated profile dirs, locks, storage_state
- `ProfileConfig`/`ProxyConfig` — Pydantic, JSON+YAML file IO, `"auto"` sentinel

### Identity
- `IdentityGenerator` + `IdentityProvider` protocol + `BrowserForgeIdentityProvider`
- Persistent `seeds.json` (validated, profile-root resolved, self-healing)

### GeoIP (geo.py + proxy.py)
- `GeoResolver` — proxy/direct-IP/host-IP, multi-endpoint fallback, TTL cache,
  country filters, `resolve_many` batch, `aclose`
- `GeoPolicy` presets (`any`/`us-strict`/`eu`), `matches_geo_policy`,
  `validate_geo_consistency`
- `GeoInfo` — ip, country, timezone_id, locale, currency, region, city, lat, lon
- `ProxyManager` — rotation, health check, `geo_retries`, `health_threshold_ms`,
  country filters, geo cache, credential masking

### Quality
- 67 tests (66 pass + 1 env-gated smoke), uniform exception hierarchy,
  docs 100% synced, wheel build verified, git initialized

## Known limitations (frozen — won't fix without owner approval)

| # | Limitation | Impact |
|---|---|---|
| L1 | browserforge uses global `random` | no full fingerprint reproducibility |
| L2 | BrowserForge dict not passed to Camoufox | partial fingerprint application |
| L3 | `GeoInfo.currency` metadata-only | no browser currency signal |
| L4 | Per-page geo override | infeasible in Camoufox |
| L5 | No `.github` CI | tests run locally only |
| L6 | "22-check baseline" never existed | historical gap, documented |

## Public API: 22 names

`ProfileConfig`, `ProxyConfig`, `StealthEngine`, `BrowserSession`,
`BulkRunner`, `ProfileResult`, `ProfileStatus`, `IdentityProvider`,
`BrowserForgeIdentityProvider`, `GeoResolver`, `GeoPolicy`, `GeoInfo`,
`matches_geo_policy`, `validate_geo_consistency`, 7 exception types,
`__version__`.
