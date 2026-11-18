# 05 — IMPLEMENTED STATUS TRACKER

Historical GeoIP/PH-12 work-package tracker with a current 2026-11-18 overlay. Phase-era counts and statements below are retained as history; current release and test scope are stated explicitly here.

- Current package: v0.3.0 Core Preview prerelease.
- PR-01 local Windows/Python 3.12 run: 245 passed, 5 expected skips, 32 subtests passed; browser/canary flags were not enabled.
- Scoped GitHub Core CI evidence and exclusions: `notes/productions/16-CORE-PRODUCTION-ACCEPTANCE.md` and `18-CORE-RELEASE-PUBLICATION-EVIDENCE.md`.
- External proxy/DNS/WebRTC behavior remains unverified; full identity parity and general leak prevention are not claimed.

## Legend

- ✅ Working & tested
- ⚠️ Working with documented limitation
- ⬜ Not implemented
- 🔒 Frozen non-goal (will never implement)

## A. Core engine features (26 A–Z)

| Feature                | Status | Notes                                                                                                         |
| ---------------------- | ------ | ------------------------------------------------------------------------------------------------------------- |
| A Async/sync API       | ✅     | launch/alaunch, loop guard                                                                                    |
| B Bulk runner          | ✅     | semaphore + ordered results                                                                                   |
| C Camoufox spoofing    | ⚠️     | device seeds only; no full fp dict (🔒 non-goal)                                                              |
| D Coherent identity    | ⚠️     | generated+validated; partial browser application                                                              |
| E Deterministic seed   | ⚠️     | device seeds deterministic; browserforge global-random limit                                                  |
| F GeoIP proxy          | ✅     | gated by `cfg.geoip` (owner decision PH-08)                                                                   |
| G Persistent session   | ✅     | user_data_dir + storage_state + locks                                                                         |
| H Human hooks          | ✅     | async hooks are canonical; sync `human_*`/`human_dwell` variants raise `AutomationError` (PF-02)              |
| I Installable          | ✅     | setuptools build_meta                                                                                         |
| J JSON config          | ✅     | Pydantic native                                                                                               |
| K Logging              | ✅     | loguru, masked creds                                                                                          |
| L Multi-profile        | ✅     | isolated roots + locks                                                                                        |
| M Proxy rotation       | ⚠️     | standalone `ProxyManager` can select from a pool; `StealthEngine` uses the single configured profile proxy    |
| N No JS spoofing       | ✅     | architectural constraint held                                                                                 |
| O Retry backoff        | ✅     | jittered exponential                                                                                          |
| P Pluggable identity   | ✅     | PH-06                                                                                                         |
| Q Proxy health         | ✅     | health_check + failover                                                                                       |
| R Reusable             | ✅     | no framework coupling                                                                                         |
| S Seed reproducibility | ⚠️     | seeds persist; full fp not reproducible                                                                       |
| T Locale consistency   | ⚠️     | locale/timezone resolve by mode; currency is metadata-only; Mode A timezone is passed through Camoufox config |
| U Error model          | ✅     | 7-type hierarchy                                                                                              |
| V Versioned config     | ✅     | schema_version field                                                                                          |
| W WebRTC configuration | ⚠️     | guarded hint/GeoIP path; not a DNS/STUN/WebRTC leak-free guarantee                                            |
| X Session export       | ✅     | export/import/has_state/metadata                                                                              |
| Y YAML/JSON IO         | ✅     | PH-06                                                                                                         |
| Z Zero global state    | ⚠️     | engine clean; browserforge violates internally (documented)                                                   |

## B. GeoIP features — current vs planned

### Working now ✅

- Exit-IP geo resolve (proxy only), health check, seeded pick
- Mode B locale/timezone alignment + Camoufox geoip
- Country→locale/currency maps (54/56 entries)
- Credential-safe geo requests, TLS on
- **PH-09:** `GeoResolver` (proxy/direct-IP/host-IP), TTL cache,
  country filters, `resolve_many` batch, `matches_geo_policy`,
  `validate_geo_consistency`; `ProxyManager` country filters + geo cache

### Partial ⚠️

- `GeoInfo.currency` — resolved, unused
- `GeoInfo.ip`/`country` — log-only consumers
- Locale/timezone are applied through launch kwargs/config according to GeoIP mode; full BrowserForge identity parity remains partial

### PH-09 added ✅ (2026-11-15)

- `GeoResolver` (proxy-optional, direct IP, host IP)
- Country filter (allowed/blocked) — both resolver and ProxyManager
- TTL cache — both resolver (default 300s) and ProxyManager (opt-in)
- `resolve_many()` batch
- `validate_geo_consistency()`

### PH-10 added ✅ (2026-11-15)

- Extended GeoInfo (region/city/lat/lon) — provider-dependent, graceful None
- Multi-provider fallback — ordered endpoints, auto shape detect
- Geo policy presets — `GeoPolicy.preset("any"|"us-strict"|"eu")`
- `locale="auto"`/`timezone="auto"` sentinel — GeoIP-derived at launch

### PH-11 added ✅ (2026-11-15)

- Real browser smoke test — `tests/test_smoke.py`, `STEALTH_SMOKE=1` gated
- Geo retries + configurable health threshold — `geo_retries`, `health_threshold_ms`
- Async human hooks — `ahuman_move`/`ahuman_type`/`ahuman_scroll`
- BulkRunner task timeout — `task_timeout_s`
- Mode A timezone — camoufox `config={"timezone": ...}` when `geoip=False` (B4 fixed)

### PH-12 added ✅ (2026-11-15)

- v0.2.0 release — version bump, `GeoInfo` public export (22 names),
  README quickstart + geoip example, wheel build + install verified

### Never (🔒)

- Per-page geo, currency injection (unless owner overrides),
  BrowserForge→Camoufox wiring, app-level features

## C. Historical Test Coverage (PH-12 Snapshot)

The following per-suite counts are the 2026-11-15 GeoIP work-package snapshot, not current totals. PR-01's current full-suite result is recorded above; CI runner results and their exact scope are in production document 16.

| Suite                        | Count                           | Covers                                                                                             |
| ---------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------- |
| test_forensic_regressions.py | 9                               | proxy creds, TLS, geoip flag, close guard, checks #23-26 (real #25)                                |
| test_feature_p_y.py          | 11                              | providers, config file IO                                                                          |
| test_geo.py                  | 34                              | geo parser, policy, presets, resolver, filters, cache, batch, fallback, auto sentinel, engine auto |
| test_hardening.py            | 13                              | geo retries, health threshold, async hooks, task timeout, Mode A timezone kwargs                   |
| test_smoke.py                | 1 (env-gated)                   | real camoufox launch — `STEALTH_SMOKE=1` only                                                      |
| **Total**                    | **67** (66 pass + 1 gated skip) | all PASS                                                                                           |
| Real-browser tests           | 0                               | PH-11 smoke test                                                                                   |

## D. Historical Production-Readiness Checklist

This checklist is retained as a phase-era record; use the current release evidence above for present acceptance.

| Item                                      | Status                                                                                                     |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| All documented features fully implemented | ⚠️ partial and unsupported boundaries exist; see current A–Z ledger                                        |
| Docs synced                               | Historical PH-12 result; later docs reconciliation tracked as PR-02                                        |
| Tests green                               | Historical 67-test PH-12 snapshot; superseded by PR-01 result above                                        |
| Real browser verified                     | Scoped Core CI passed on specified runners; arbitrary environments and external proxies remain unverified  |
| Version control                           | ✅ Git repository and GitHub `main`/`origin/main` baseline exist; notes tracking policy mismatch remains   |
| Release version                           | ✅ v0.3.0 Core Preview prerelease                                                                          |
| Clean-install verified                    | ✅ wheel/sdist install recorded in release evidence; dependency snapshot is not a full cross-platform lock |
