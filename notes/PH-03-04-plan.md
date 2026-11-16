# PH-03/PH-04 Plan — engine.py Mode A/Mode B Launch Logic

Date: 2026-10-20
Phase: PH-03/PH-04 (combined)

## Preconditions and inventory

- `AGENTS.md` was read first
- PH-01 complete: `ProfileConfig.proxy` optional, `target_ip` present
- PH-02 complete: `get_or_create_seeds()` implemented, `tzlocal` added
- Forensic audit (`PH-03-04-FORENSIC-AUDIT.md`) confirms:
  - Step 3 (Mode A) is NOT STARTED
  - Step 4 (Mode B) is PARTIAL (GeoIP works, device seeds ignored)
- Current `engine.py` state:
  - Line 138: calls `identity.generate()`, NOT `get_or_create_seeds()`
  - `_build_launch_kwargs()` does NOT pass device seeds to Camoufox
  - WebRTC IP (`webrtc:ipv4`) is NOT set
  - Mode A does not use `seeds.json` locale/timezone_id

## What changes and why

**PH-03 — Step 3 (Mode A - No Proxy):**
1. In `StealthEngine.alaunch()`, call `seeds = self._identity.get_or_create_seeds()` before fingerprint generation
2. Build device seed overrides:
   - `canvas:seed` from `seeds["canvas"]`
   - `audio:seed` from `seeds["audio"]`
   - `fonts:spacing_seed` from `seeds["fonts"]`
3. Implement or import host IP resolution for WebRTC:
   - Use `config.target_ip` if provided
   - Otherwise resolve actual host IP
4. Set `webrtc:ipv4` in launch kwargs
5. Ensure `geoip = False` and `proxy = None` for Mode A
6. Override locale/timezone_id from seeds (NOT from fingerprint)

**PH-04 — Step 4 (Mode B - With Proxy):**
1. In `StealthEngine.alaunch()`, for proxy path:
   - Call `seeds = self._identity.get_or_create_seeds()` (same as Mode A)
   - Pass device seeds to Camoufox (same as Mode A)
   - Keep existing GeoIP logic for locale/timezone_id (GeoIP wins over seeds)
   - Ensure `geoip = True` and proxy is configured
2. Device seeds preserve fingerprint consistency across proxy rotations

## Files/modules affected

- `stealth_engine/engine.py`:
  - Modify `alaunch()` to call `get_or_create_seeds()`
  - Add device seed extraction and passing to Camoufox
  - Add host IP resolution function
  - Update `_build_launch_kwargs()` to accept seed overrides and WebRTC IP
- `project/modules/engine.md`:
  - Document Mode A/Mode B launch logic
  - Document seed consumption
  - Document WebRTC IP handling
- `docs/ROADMAP-v2-FREEZE.md`:
  - Update Step 3/4 status to COMPLETE after implementation
- `MEMORY.md`:
  - Record PH-03/PH-04 completion
- `notes/PH-03-04-plan.md`, `notes/PH-03-04-log.md`, `notes/MANIFEST.md`:
  - Private plan/log/index

## Expected outcome

- Mode A (no proxy):
  - Uses `seeds.json` for device seeds, locale, timezone_id
  - WebRTC advertises host IP
  - `geoip = False`
- Mode B (with proxy):
  - Uses `seeds.json` for device seeds
  - GeoIP overrides locale/timezone_id
  - WebRTC advertises proxy IP
  - `geoip = True`
- All 5 existing tests continue to pass
- Device seeds ensure fingerprint consistency across launches

## Rollback

Planned: `git checkout -- stealth_engine/engine.py`
(Workspace has no `.git`; fallback is manual revert)

## Explicit non-goals

- No changes to `config.py`, `identity.py`, `proxy.py`, `session.py`, `orchestrator.py`, `exceptions.py`, `__init__.py`, or `utils/*`
- No test changes in PH-03/PH-04 (checks #23-26 grouped into PH-05)
- No public API changes
- No renaming of existing methods
