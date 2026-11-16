# PH-07 Plan — Audit-Debt Cleanup

Date: 2026-11-15
Owner-approved scope (from forensic audit `notes/2026-11-15-forensic-audit-resume.md`).

## Items

1. **Stale status sync** — `project/features/*.md` files still say
   "Planned (Phase N)" though code exists; sync each to real status.
   Also fix remaining stale lines in `docs/` and `project/modules/`.
2. **Check #25 upgrade** — replace mocked `fingerprint_hash` test with real
   `IdentityGenerator` + real `seeds.json`: two launches of same profile must
   produce identical persisted seeds and identical device-seed launch kwargs.
   NOTE: cross-instance `fingerprint_hash` equality is NOT asserted —
   browserforge consumes process-global `random` (documented limitation);
   seeds persistence is the real verifiable contract.
3. **seeds.json schema validation** — `get_or_create_seeds()` currently returns
   loaded JSON unvalidated → `KeyError` at engine launch on incomplete file.
   Add required-key/type check; invalid → warn + regenerate.
4. **user_data_dir/profile_name path fix** — seeds.json must land in the same
   profile root SessionManager resolves: `udd` when basename==profile_name,
   else `udd/profile_name` (mirrors `StealthEngine._derive_base_dir` +
   `SessionManager._profile_dir`, including the empty-dirname → `./profiles`
   fallback). Implement `_profile_root()` helper in identity.py.
5. **Step-4 geoip deviation mark** — document (docs/MEMORY only, NO code
   change, frozen doc untouched) that Mode B uses `cfg.geoip` gate instead of
   unconditional `geoip=True`.

## Files affected

- `stealth_engine/identity.py` — `_profile_root()` + seeds validation
- `tests/test_forensic_regressions.py` — upgrade check #25 test
- `project/features/*.md` (~17 files) — status sync
- `project/modules/*.md`, `docs/*.md`, `MEMORY.md` — stale lines + deviation mark
- `notes/PH-07-plan.md`, `notes/PH-07-log.md`, `notes/MANIFEST.md`

## Expected outcome

- seeds.json always written to the real profile root; corrupt/incomplete
  seeds.json self-heals instead of crashing launch.
- Check #25 verifies actual persistence behavior.
- All feature docs reflect implemented status; geoip deviation documented.
- All tests pass.

## Non-goals

- NO change to `docs/ROADMAP-v2-FREEZE.md` (frozen; owner approval required).
- NO code change for geoip gating (item 5 is docs-only).
- No new features; no refactor beyond items above.
