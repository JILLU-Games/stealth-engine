# PH-03/PH-04 Forensic Audit — 2026-10-20

## Recent Session Completed: PH-02

**What was implemented:**
1. `stealth_engine/identity.py`:
   - Added `_detect_host_locale()` (lines 37-55)
   - Added `_detect_host_timezone()` (lines 58-76)
   - Added `IdentityGenerator.get_or_create_seeds()` (lines 172-252)
   - New imports: `os`, `secrets`, `Path`
   - Method returns dict with 7 keys: `canvas`, `audio`, `fonts`, `locale`, `timezone_id`, `locale_source`, `timezone_source`
   - Persisted to `<user_data_dir>/seeds.json` atomically

2. `pyproject.toml`:
   - Added `"tzlocal>=5.0"` dependency (line 16)

3. Documentation updates:
   - `project/modules/identity.md` — updated with PH-02 status
   - `project/features/E-deterministic-seed.md` — updated with PH-02 status
   - `project/DEPENDENCIES.md` — created and indexed
   - `notes/PH-02-plan.md` and `notes/PH-02-log.md` — created

**Verification status (from PH-02-log):**
- All 5 existing tests pass
- Seed persistence probe passed
- `generate()` and `fingerprint_hash()` unchanged (baseline snapshots match)
- Public API remains 15 names

---

## Current Project State vs Frozen Plan

### Frozen Plan Step 3 — Mode A (No Proxy) Launch Logic

**Required (from docs/ROADMAP-v2-FREEZE.md lines 111-125):**
```
When config.proxy is None:
  - seeds = identity.get_or_create_seeds()
  - locale = seeds["locale"]
  - timezone_id = seeds["timezone_id"]
  - config_overrides = {
      "canvas:seed": seeds["canvas"],
      "audio:seed": seeds["audio"],
      "fonts:spacing_seed": seeds["fonts"],
      "webrtc:ipv4": config.target_ip or resolved_host_ip(),
    }
  - geoip = False
  - proxy = None
```

**Actual state in stealth_engine/engine.py:**
- Line 138: `fp = self._identity.generate()` — NO call to `get_or_create_seeds()`
- Lines 275-294 (`_build_launch_kwargs`):
  - NO `canvas:seed`, `audio:seed`, `fonts:spacing_seed` passed to Camoufox
  - NO `webrtc:ipv4` passed
  - `geoip = False` is correctly set when no proxy (line 288)
  - `locale` comes from `fp.get("locale", "en-US")` (line 280), NOT from `seeds["locale"]`

**Gap:** Step 3 is NOT implemented. Mode A does not use `seeds.json` or device seeds.

---

### Frozen Plan Step 4 — Mode B (With Proxy) Launch Logic

**Required (from docs/ROADMAP-v2-FREEZE.md lines 127-136):**
```
When config.proxy is not None:
  - geo = await proxy_manager.pick_healthy()
  - geoip = True
  - proxy = proxy_manager.to_playwright(config.proxy)
  - locale = geo.locale
  - timezone_id = geo.timezone_id
  - config_overrides retains canvas/audio/fonts seeds from seeds.json
```

**Actual state in stealth_engine/engine.py:**
- Lines 146-147: `proxy_cfg, geo = await self._proxy_manager.pick_healthy()` — EXISTS
- Line 286: `kwargs["geoip"] = cfg.geoip` — EXISTS
- Line 285: `kwargs["proxy"] = self._proxy_manager.to_playwright(proxy_cfg)` — EXISTS
- Lines 150-152: GeoIP overrides to `fp["timezone_id"]` and `fp["locale"]` — EXISTS
- MISSING: Device seeds (canvas/audio/fonts) from `seeds.json` are NOT passed to Camoufox

**Gap:** Step 4 is PARTIALLY implemented. GeoIP works, but device seeds are ignored.

---

## Implementation Status Summary

| Step | Status | Details |
|------|--------|---------|
| Step 1 (config.py) | ✅ COMPLETE | `proxy` optional, `target_ip` added in PH-01 |
| Step 2 (identity.py) | ✅ COMPLETE | `get_or_create_seeds()` implemented in PH-02 |
| Step 3 (engine.py - Mode A) | ❌ NOT STARTED | Seeds not loaded, device seeds not passed, WebRTC IP not set |
| Step 4 (engine.py - Mode B) | ⚠️ PARTIAL | GeoIP works, but device seeds ignored |
| Step 5 (Verification) | ❌ NOT STARTED | Checks #23-26 not yet written or executable |

---

## What Needs to Happen Next

**PH-03 — Implement Step 3 (Mode A):**
1. In `StealthEngine.alaunch()`, before generating fingerprint:
   - Call `seeds = self._identity.get_or_create_seeds()`
2. Build device seed overrides:
   - `canvas:seed`, `audio:seed`, `fonts:spacing_seed` from `seeds`
3. Implement or import `resolved_host_ip()` for WebRTC
   - Use `config.target_ip` if provided, else resolve host IP
4. Pass these to Camoufox launch kwargs
5. Ensure `geoip = False` and `proxy = None` for Mode A

**PH-04 — Complete Step 4 (Mode B):**
1. In `StealthEngine.alaunch()`, for proxy path:
   - Call `seeds = self._identity.get_or_create_seeds()` (same as Mode A)
   - Pass device seeds to Camoufox (same as Mode A)
   - Keep existing GeoIP logic for locale/timezone_id
   - Ensure `geoip = True` and proxy is configured

**PH-05 — Verification:**
1. Write tests for checks #23-26
2. Verify all 22 existing checks still pass
3. Confirm Mode A/Mode B behavior matches frozen plan

---

## Files to Modify

- `stealth_engine/engine.py`:
  - Modify `alaunch()` to call `get_or_create_seeds()`
  - Add device seed passing to Camoufox
  - Add WebRTC IP resolution
  - Update `_build_launch_kwargs()` to accept seed overrides

- `stealth_engine/identity.py`:
  - No changes needed (PH-02 already complete)

- `tests/test_forensic_regressions.py`:
  - Add checks #23-26 (PH-05)

- Documentation updates (after code changes):
  - `project/modules/engine.md`
  - `docs/ROADMAP-v2-FREEZE.md` (if status tracking needed)
  - `MEMORY.md`
