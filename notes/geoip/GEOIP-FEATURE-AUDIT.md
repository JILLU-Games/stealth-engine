# GeoIP Feature — Forensic Audit Report

Date: 2026-11-15
Auditor: Devin (post PH-08 baseline)
Scope: every GeoIP-related capability — what exists in `stealth_engine/`,
what is actually consumed by the engine, and what is missing vs the
full reusable-API vision.

---

## 1. What exists in code today (verified)

### `stealth_engine/proxy.py` — the GeoIP engine

| Component | Location | Behavior |
|---|---|---|
| `GeoInfo` (Pydantic) | proxy.py:94–109 | Fields: `ip`, `country` (ISO alpha-2), `timezone_id` (IANA), `locale` (BCP-47), `currency` (ISO 4217) — **5 fields only** |
| `ProxyManager.resolve_geo()` | proxy.py:173–239 | GET `geo_endpoint` through the given `ProxyConfig`; aiohttp; TLS verification ON; credentials split from URL (`_build_proxy_url`/`_build_proxy_auth`); typed `ProxyError` on timeout/HTTP/JSON failure |
| `ProxyManager.health_check()` | proxy.py:241–261 | Latency ms of a full `resolve_geo` call |
| `ProxyManager.pick_healthy()` | proxy.py:263–303 | Seeded `random.Random` shuffle under `asyncio.Lock`; returns first proxy with geo + latency < 5000 ms; raises `ProxyError` listing masked attempts |
| `ProxyManager.to_playwright()` | proxy.py:305–327 | ProxyConfig → Playwright proxy dict (creds optional keys) |
| `ProxyManager.mask()` | proxy.py:329+ | Credential-redacted dict for logs |
| `_COUNTRY_LOCALE` | proxy.py:24+ | **54 country→locale entries** |
| `_COUNTRY_CURRENCY` | proxy.py:66+ | **56 country→currency entries** |
| `_FALLBACK_LOCALE` / `_FALLBACK_CURRENCY` | proxy.py:90–91 | Fallback constants |
| `_parse_geo()` | proxy.py:415–457 | Maps endpoint JSON → GeoInfo; derives locale/currency from country code |
| Constructor options | proxy.py:131–154 | `geo_endpoint` (default `https://ipinfo.io/json`), `timeout_s=8.0`, `seed` |

### Consumers of GeoIP data

| Consumer | What it uses | Where |
|---|---|---|
| `StealthEngine.alaunch()` | `geo.locale` → `fp["locale"]` → launch `locale` kwarg; `geo.timezone_id` → `fp["timezone_id"]` (fp dict itself NOT passed to Camoufox) | engine.py:155–157, 329 |
| `StealthEngine._build_launch_kwargs()` | `kwargs["geoip"] = cfg.geoip` → Camoufox derives tz/locale/WebRTC from exit IP | engine.py:337–339 |
| Mode A (no proxy) | `geoip=False`, `webrtc:ipv4` = `target_ip` or `_resolve_host_ip()` (UDP 8.8.8.8 route lookup) | engine.py:341–347, 226–257 |
| `BulkRunner` | none directly — per-profile `StealthEngine` inherits behavior | orchestrator.py |
| `ProfileConfig.geoip` | per-app ON/OFF gate (PH-08 owner decision) | config.py:83 |

### What GeoIP data is NOT consumed by

- `GeoInfo.currency` — **resolved but never used anywhere** (metadata only)
- `GeoInfo.ip` — logged/returned but not applied to any browser setting
- `GeoInfo.country` — used only for logging in `pick_healthy`
- `timezone_id` from GeoInfo → only mutates `fp` dict; Camoufox gets tz via its own `geoip=True` mechanism, not from our value

---

## 2. Feature inventory — USED vs MISSING

### ✅ Already implemented & wired (8)

| # | Feature | Evidence |
|---|---|---|
| U1 | Exit-IP GeoIP resolution via configurable endpoint | `resolve_geo`, `geo_endpoint` param |
| U2 | Async proxy health check (latency ms) | `health_check` |
| U3 | Seeded proxy rotation + health-gated pick | `pick_healthy` |
| U4 | GeoIP→locale/timezone alignment at launch (Mode B) | engine.py:155–157 |
| U5 | WebRTC IP via Camoufox `geoip=True` (Mode B) / host IP (Mode A) | engine.py:337–347 |
| U6 | Per-app geoip ON/OFF gate | `ProfileConfig.geoip` (PH-08 decision) |
| U7 | Credential-safe proxy handling in geo requests | `_build_proxy_url`/`_build_proxy_auth`/`mask` |
| U8 | Country→locale/currency static derivation | `_COUNTRY_*` maps in `_parse_geo` |

### ⚠️ Implemented but PARTIALLY consumed (3)

| # | Feature | Gap |
|---|---|---|
| P1 | `GeoInfo.currency` | Resolved, never applied to browser or anywhere |
| P2 | `GeoInfo.ip` / `country` | Available but only for logging — no consumer feature |
| P3 | GeoIP `timezone_id`/`locale` values | Applied to `fp` dict which is NOT passed to Camoufox (frozen non-goal) — real effect comes from Camoufox `geoip=True` itself |

### ❌ Missing — genuinely useful, engine-appropriate (8)

| # | Feature | What it needs | Effort |
|---|---|---|---|
| M1 | **`GeoResolver`** — proxy-optional direct IP/proxy resolution | `resolve_geo` currently requires `ProxyConfig`; add `None`/direct-IP path + standalone class | Small |
| M2 | **Country/region filter** — `allowed_countries`, `blocked_countries` | Filter in `pick_healthy`/`resolve` pipeline | Small |
| M3 | **GeoIP cache (TTL)** | Same proxy/IP resolved repeatedly today; no cache | Small |
| M4 | **Batch resolver** — `resolve_many()` concurrent | Pool-scale (100+ proxies) needs it | Small |
| M5 | **Geo consistency validator** — "proxy geo vs config locale/tz match?" | QA/anti-detect audit tool | Medium |
| M6 | **Extended GeoInfo** — `region`, `city`, `lat`, `lon` | Provider-dependent fields (ipinfo paid tier / ip-api) | Medium |
| M7 | **Multi-provider fallback chain** | ipinfo rate-limit er dukh hole ip-api/ipwhois auto-fallback | Medium |
| M8 | **Geo policy presets** — named `us-strict`/`eu`/`any` configs | Thin config layer over M2 | Small |

### ❌ Missing — app-level, should NOT be in engine (6)

These belong to consuming applications, not `stealth_engine`:

| # | Feature | Why not engine |
|---|---|---|
| A1 | Region-targeted scraper router | App routing logic |
| A2 | Multi-geo rank/price tracker | App reporting logic |
| A3 | Ad verification across regions | App campaign logic |
| A4 | Account geo-discipline manager | App business logic (though sticky-binding data could live in engine — see M-note below) |
| A5 | Geo drift detector | Marginal value; fold into health_check if ever needed |
| A6 | Per-page geo override | Not feasible/fragile in Camoufox — rejected |

### ❓ Verify-before-build (3)

| # | Feature | Blocker |
|---|---|---|
| V1 | `navigator.geolocation` lock to proxy lat/long | Needs extended GeoInfo (M6) + Camoufox support verification |
| V2 | Currency injection into browser signals | Camoufox has no direct currency option; would need locale-level tricks — low ROI |
| V3 | `locale="auto"` sentinel auto-fill | Trivial once M1 exists; config-layer sugar |

---

## 3. Summary scorecard

| Category | Count |
|---|---|
| Fully implemented & consumed | 8 |
| Implemented, partially consumed | 3 |
| Missing, engine-appropriate | 8 |
| Missing, app-level (out of scope) | 6 |
| Verify-first | 3 |
| **Total inventoried** | **28** |

## 4. Recommended next phase (PH-09 candidate)

**Scope: M1 + M2 + M3 + M4 + M5** — the cohesive core:

1. `GeoResolver` — standalone, proxy-optional, reusable in any project
2. Country filter on pick/resolve
3. TTL cache
4. `resolve_many()` batch
5. Consistency validator helper

Deferred: M6/M7 (provider-dependent), M8 (config sugar), V1–V3 (verify first),
A1–A6 (app responsibility).

## 5. Design constraints (must preserve)

- Engine stays **generic reusable** — no app-specific geo logic (PH-08 decision)
- `ProfileConfig.geoip` remains the per-app ON/OFF gate
- No browser/camoufox dependency inside resolver layer
- Credentials never logged; TLS verification stays ON
- Frozen non-goals unchanged (no BrowserForge→Camoufox wiring etc.)
