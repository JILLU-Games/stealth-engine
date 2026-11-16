# 01 — PRODUCTION GAPS & BUGS (forensic findings)

Every gap/bug found across all audits, grouped by severity. Each item has an
exact location and proposed fix phase (see 02-ROADMAP-PHASES.md).

## A. Bugs / correctness issues

| ID | Severity | Location | Issue | Fix phase |
|---|---|---|---|---|
| B1 | Medium | `proxy.py` `resolve_geo` | No retry on transient network failure — single attempt only | PH-11 |
| B2 | Medium | `proxy.py` `pick_healthy` | Health threshold `5000.0` ms hardcoded — not configurable | PH-11 |
| B3 | Low | `proxy.py:407` | `aiohttp.BasicAuth` deprecated (aiohttp 4.0 removal warning in tests) | PH-11 |
| B4 | Medium | `engine.py` `_build_launch_kwargs` | Mode A `timezone_id` never reaches Camoufox (fp dict not forwarded; geoip=False) — `config.timezone` inert at browser level | PH-11 (document or fix) |
| B5 | Low | `identity.py` `get_or_create_seeds` | No cross-process lock on seeds.json — two direct `IdentityGenerator` users (bypassing engine lock) could race the tmp→replace write | PH-11 (document or lock) |
| B6 | Low | `orchestrator.py` | No per-task timeout — a hung `task_fn` blocks a semaphore slot forever | PH-11 |
| B7 | Info | `session.py` | `import_state()` exists but engine never auto-imports on launch (by design — persistent_context reads user_data_dir; storage_state.json is export artifact) | Document only |

## B. Missing features — GeoIP core (from GEOIP-FEATURE-AUDIT.md)

| ID | Feature | Phase |
|---|---|---|
| M1 | `GeoResolver` — proxy-optional direct-IP resolution, standalone reusable | PH-09 |
| M2 | Country/region filter (`allowed_countries`, `blocked_countries`) | PH-09 |
| M3 | GeoIP TTL cache | PH-09 |
| M4 | `resolve_many()` batch resolver | PH-09 |
| M5 | Geo consistency validator | PH-09 |
| M6 | Extended GeoInfo (`region`, `city`, `lat`, `lon`) | PH-10 |
| M7 | Multi-provider fallback chain | PH-10 |
| M8 | Geo policy presets | PH-10 |
| V3 | `locale="auto"` sentinel | PH-10 |

## C. Missing features — engine hardening / production

| ID | Feature | Phase |
|---|---|---|
| H1 | Real camoufox launch smoke test (first actual browser verification) | PH-11 |
| H2 | Configurable geo health threshold + resolve retries | PH-11 |
| H3 | Async human-interaction hooks (`ahuman_move` etc.) | PH-11 |
| H4 | `BulkRunner` per-task timeout | PH-11 |
| H5 | `.git` init / version control setup | PH-11 (owner decision) |
| H6 | Version bump 0.1.0 → 0.2.0 + release prep | PH-12 |

## D. Explicitly OUT of scope (do not implement)

- BrowserForge→Camoufox fingerprint wiring (frozen non-goal)
- Per-page geo override (infeasible)
- App-level features: scraper router, rank tracker, ad verification,
  account geo-discipline manager, geo analytics (consuming-app responsibility)
- `navigator.geolocation` lock, currency injection (verify-first, low ROI —
  deferred unless owner requests)
- Changing `docs/ROADMAP-v2-FREEZE.md`

## E. Documentation debt (remaining)

| ID | Item | Phase |
|---|---|---|
| D1 | `docs/MANIFEST.md` doesn't list `ROADMAP-v2-FREEZE.md` | PH-11 |
| D2 | README feature table vs actual partial statuses — add notes column | PH-12 |
| D3 | `examples/` has only placeholder — add geoip usage example | PH-10/12 |
