# PH-05 Plan — Verification of Step 3/4 Implementation

Date: 2026-10-20
Phase: PH-05

## Preconditions and inventory

- `AGENTS.md` was read first
- PH-01 complete: `ProfileConfig.proxy` optional, `target_ip` present
- PH-02 complete: `get_or_create_seeds()` implemented, `tzlocal` added
- PH-03/PH-04 complete: Mode A/Mode B launch logic implemented, device seeds passed to Camoufox
- Current test suite: 5 tests in `tests/test_forensic_regressions.py`
- Frozen plan requires:
  - All 22 existing checks must PASS
  - New checks #23-26 must be added and PASS
- TEST-BASELINE-AUDIT.md confirmed: no enumerated 1-22 checklist exists in project files
- Cannot verify against an unknown 22-check baseline; will verify the 5 existing tests and add #23-26

## What changes and why

**Test additions only — no code changes to engine/identity/proxy/config:**

1. Add test for check #23 (Mode A locale from seeds):
   - Create ProfileConfig with `proxy=None`
   - Mock Camoufox to capture launch_kwargs
   - Assert `launch_kwargs["locale"] == seeds["locale"]`

2. Add test for check #24 (Mode B locale from GeoIP):
   - Create ProfileConfig with proxy and `geoip=True`
   - Mock `pick_healthy()` to return GeoInfo with specific locale
   - Mock Camoufox to capture launch_kwargs
   - Assert `launch_kwargs["locale"] == geo.locale`

3. Add test for check #25 (seed persistence and fingerprint consistency):
   - Create ProfileConfig with seed
   - Launch once, capture fingerprint_hash
   - Launch again with same profile (reuses seeds.json)
   - Assert fingerprint_hash identical

4. Add test for check #26 (proxy=None launches Mode A):
   - Create ProfileConfig with `proxy=None`
   - Mock Camoufox to capture launch_kwargs
   - Assert `geoip=False` and `webrtc:ipv4` is set (host IP or target_ip)
   - Assert device seeds present in kwargs

## Files/modules affected

- `tests/test_forensic_regressions.py`:
  - Add test methods for checks #23-26
  - Keep existing 5 tests unchanged
- `project/modules/engine.md`:
  - Update verification status
- `docs/ROADMAP-v2-FREEZE.md`:
  - Mark Step 5 COMPLETE after verification
- `MEMORY.md`:
  - Record PH-05 completion and limitation about 22-check baseline
- `notes/PH-05-plan.md`, `notes/PH-05-log.md`, `notes/MANIFEST.md`:
  - Private plan/log/index

## Expected outcome

- All 5 existing tests continue to PASS
- New tests for #23-26 PASS
- Mode A/Mode B behavior matches frozen plan
- Limitation documented: 22-check baseline cannot be verified because the checklist does not exist in project files

## Rollback

Planned: `git checkout -- tests/test_forensic_regressions.py`
(Workspace has no `.git`; fallback is manual revert)

## Explicit non-goals

- No changes to `stealth_engine/engine.py`, `identity.py`, `proxy.py`, `config.py`, `session.py`, `orchestrator.py`, `exceptions.py`, `__init__.py`, or `utils/*`
- No public API changes
- No renaming of existing methods
- No attempt to invent or reconstruct the missing 22-check baseline
