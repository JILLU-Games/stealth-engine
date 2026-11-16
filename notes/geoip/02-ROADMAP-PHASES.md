# 02 — ROADMAP: GeoIP & Production Phases

Step-by-step implementation plan. Each phase is **scope-locked** — only the
listed items may be touched; anything else found goes to the log as
"out-of-scope finding" for a later phase.

Phase numbering continues from PH-08. Order is dependency-driven:
core primitives → extended providers → hardening/release.

---

## PH-09 — GeoIP Core (M1–M5)

**Goal:** standalone reusable geoip layer inside the engine.

**Scope lock — ALLOWED files:**
- `stealth_engine/proxy.py` (extend) or new `stealth_engine/geo.py`
  (decision at plan time — prefer new module `geo.py` for clean separation)
- `stealth_engine/__init__.py` (exports)
- `tests/` (new test file)
- `project/modules/`, `project/features/` (new feature docs if warranted)
- `docs/MODULES.md`, `docs/FEATURES.md`, `MEMORY.md`, `CHANGELOG.md`
- `notes/geoip/03-PHASE-LOG.md`

**Deliverables:**
1. `GeoResolver` class — `resolve(ip_or_proxy)` works with `ProxyConfig`,
   direct IP string, or `None` (host IP). Reuses aiohttp session pattern,
   credential separation, `mask()`, typed `ProxyError`.
2. Country filter — `allowed_countries`/`blocked_countries` params applied
   in `ProxyManager.pick_healthy` and `GeoResolver`.
3. TTL cache — `cache_ttl_s` param; keyed by proxy server/IP; `aclose()`
   clears.
4. `resolve_many(proxies, concurrency=...)` — `asyncio.Semaphore`-bounded
   `asyncio.gather`.
5. `validate_geo_consistency(proxy_geo, config)` helper — compares
   `GeoInfo.locale/timezone_id` vs `ProfileConfig.locale/timezone`.

**Non-goals:** no GeoInfo field changes, no provider chain, no engine.py
behavior change (ProxyManager may internally delegate to GeoResolver —
allowed if behavior identical).

**Verification:** new unit tests (mocked aiohttp) + all 20 existing tests pass.

---

## PH-10 — GeoIP Extended (M6, M7, M8, V3)

**Scope lock:** same module set as PH-09 + `config.py` (only for `locale="auto"`
sentinel if chosen).

**Deliverables:**
1. `GeoInfo` extended fields: `region`, `city`, `latitude`, `longitude`
   (optional, provider-dependent; ipinfo free tier may lack them — must
   degrade gracefully).
2. Multi-provider fallback — ordered endpoint list with per-provider
   response-shape adapters.
3. Geo policy presets — e.g. `GeoPolicy(name, allowed_countries, ...)`
   thin wrapper over PH-09 filters.
4. `ProfileConfig.locale="auto"` / `timezone="auto"` sentinel → resolved
   from GeoIP at launch (engine.py minimal hook).

**Non-goals:** no geolocation API mock, no currency injection, no new
browser kwargs beyond what Camoufox natively supports.

---

## PH-11 — Production Hardening

**Scope lock:** `proxy.py`, `engine.py`, `orchestrator.py`, `identity.py`
(docs/comments only where noted), tests, docs.

**Deliverables:**
1. **H1** Real camoufox smoke test — first actual browser launch
   (headless, `example.com` or `about:blank`), env-gated
   (`STEALTH_SMOKE=1`) so CI without camoufox binary stays green.
2. **H2** `geo_retries` + `health_threshold_ms` params on ProxyManager.
3. **H3** `ahuman_move`/`ahuman_type`/`ahuman_scroll` async variants using
   `asyncio.sleep`.
4. **H4** `BulkRunner(task_timeout_s=...)` per-task timeout → FAILED.
5. **H5** `.git` init — OWNER DECISION REQUIRED before running.
6. **B4** Mode A timezone: document limitation OR pass timezone to
   Camoufox if a supported kwarg exists (verify Camoufox API first).
7. **B5** seeds.json cross-process note in docs (or lockfile if cheap).
8. **D1** `docs/MANIFEST.md` add missing `ROADMAP-v2-FREEZE.md` row.

**Non-goals:** no new features; fixes/hardening only.

---

## PH-12 — Release Prep

**Scope lock:** version files, README, examples, CHANGELOG, docs only.

**Deliverables:**
1. **H6** Version bump → `0.2.0` (new features since 0.1.0) in
   `pyproject.toml` + `__init__.py`.
2. README quickstart refresh + geoip usage example in `examples/`.
3. Final docs sweep — every feature doc matches code.
4. Release checklist run (build wheel, install clean venv, import test).

---

## Dependency graph

```
PH-09 (core) ──→ PH-10 (extended) ──→ PH-12 (release)
     └────────→ PH-11 (hardening) ──→ PH-12
```

PH-09 and PH-11 could swap order if owner prefers hardening first;
PH-10 depends on PH-09 (GeoResolver + filters are its foundation).

## Completion criteria per phase

- All existing tests still pass + new tests for new behavior
- `project/` + `docs/` updated in same unit
- `notes/geoip/03-PHASE-LOG.md` entry written
- Scope-lock respected: nothing outside listed files changed
