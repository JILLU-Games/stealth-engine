# Plan: proxy.py Implementation

**Date:** 2026-10-19  
**Status:** In progress

## What is being changed and why

Implementing `stealth_engine/proxy.py` — the proxy rotation, health-check,
and GeoIP resolution layer. This is Phase 4 of the roadmap.

## Files affected

- `stealth_engine/proxy.py` (create implementation from skeleton)
- `project/modules/proxy.md` (update status)

## Expected outcome

`ProxyManager` class with 7 public methods:
- `resolve_geo`, `health_check`, `pick_healthy`, `to_playwright`, `mask`, `aclose`
- `GeoInfo` Pydantic model

## Phase log

### Phase 1 — Read existing stable files
- Read config.py for ProxyConfig shape ✅
- Checked aiohttp and asyncio patterns ✅

### Phase 2 — Write proxy.py
- In progress...

### Phase 2 — proxy.py written ✅

- `GeoInfo` Pydantic model with 5 fields
- `ProxyManager` with 7 public methods exactly as specced
- Lazy `aiohttp.ClientSession` via `_get_session()`
- Seeded `random.Random` isolated from global state
- `asyncio.Lock` in `pick_healthy()` for concurrency safety
- `mask()` used in all log lines and exception details — password never exposed
- Static country→locale and country→currency mapping tables (~50 entries each)
- `aclose()` idempotent: checks `session.closed` before closing

### Phase 3 — project/modules/proxy.md updated ✅

Done. No issues encountered.
