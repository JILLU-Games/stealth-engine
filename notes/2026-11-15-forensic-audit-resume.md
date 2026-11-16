# Forensic Audit — Project Resume Baseline (2026-11-15)

Full re-audit of notes/ plans vs actual source. Verified by reading all package
source and running the test suite (`.venv`, `python -m unittest discover -s tests -v`
→ 9/9 PASS).

## Verified implemented

- PH-01 / Frozen Step 1: `config.py` — `proxy: ProxyConfig | None = None` (line 81),
  `target_ip: str | None = None` (line 82). Validators intact.
- PH-02 / Frozen Step 2: `identity.py:172-252` `get_or_create_seeds()` — loads
  `<user_data_dir>/seeds.json`, derives canvas/audio/fonts via seeded RNG
  (`secrets.randbits(32)` fallback), locale/timezone via config → host
  (tzlocal/locale) → fallback, atomic tmp → `os.replace`. Returns 7 keys.
- PH-03 / Frozen Step 3 (Mode A): `engine.py:139` seeds loaded before fingerprint;
  lines 160-161 set locale/timezone_id from seeds when no GeoIP; `_build_launch_kwargs`
  (305-353) passes `canvas:seed`, `audio:seed`, `fonts:spacing_seed`, and
  `webrtc:ipv4` = `config.target_ip` or `_resolve_host_ip()` (UDP 8.8.8.8 route
  lookup, lines 226-257); `geoip=False`; no `proxy` kwarg in Mode A.
- PH-04 / Frozen Step 4 (Mode B): `pick_healthy()` exists (proxy.py:263);
  geo locale/timezone override at engine.py:155-157 gated on `cfg.geoip`;
  device seeds passed in both modes. `kwargs["geoip"] = cfg.geoip` (line 339).
- PH-05 / Frozen Step 5: 4 tests added (`PH05_VerificationTests`,
  test_forensic_regressions.py:198-477). Suite = 9 tests, all PASS (verified today).

## Gaps / deviations found

1. Step 4 deviation: frozen text says Mode B `geoip = True` unconditionally and
   `locale = geo.locale`. Code uses `cfg.geoip` gate; with proxy + `geoip=False`
   it falls back to seed locale/timezone. Likely intentional (preserves feature F
   toggle) but differs from frozen wording — owner decision needed.
2. Check #25 is vacuous: `fingerprint_hash` is mocked to a constant in both
   engines; it does not exercise real `seeds.json` persistence or fingerprint
   reproducibility. Seed persistence itself was probed in PH-02 but has no
   committed test.
3. Mode A `timezone_id` never reaches Camoufox: `fp["timezone_id"]` is set but
   `_build_launch_kwargs` only forwards `locale` from fp; the fp dict itself is
   not passed (frozen non-goal). `config.timezone` / seeds timezone are inert at
   browser level in Mode A.
4. seeds.json path edge case: identity writes to `config.user_data_dir/seeds.json`
   directly; if `user_data_dir` does not end with `profile_name`, SessionManager
   creates `<udd>/<profile_name>/` and seeds land outside the real profile dir.
5. `get_or_create_seeds` reload returns JSON unvalidated — a syntactically valid
   but incomplete seeds.json causes `KeyError` at engine.py:331 → wrapped as
   LaunchError.
6. A–Z feature docs drift: most `project/features/*.md` still say "Planned
   (Phase N)" though code exists; `docs/FEATURES.md:44-45`,
   `docs/MODULES.md:35,133`, `project/modules/identity.md:4`,
   `project/modules/config.md:29`, features E/S/T still claim engine seed
   consumption "pending PH-03/PH-04" — now stale.
7. `docs/ROADMAP-v2-FREEZE.md` §8 Freeze Checklist still shows `[ ]` for all
   steps although §4 marks them ✅ (MEMORY.md is authoritative per doc itself).
8. Genuinely unimplemented features: **P** (pluggable identity provider — no
   interface in identity.py) and **Y** (YAML/JSON profile import-export — no
   yaml usage, no load/save methods on ProfileConfig). J partially (Pydantic
   JSON via model_dump only; no file IO).
9. The "22 existing checks" F6-Final baseline does not exist anywhere —
   permanently unverifiable (TEST-BASELINE-AUDIT.md). Current real coverage = 9 tests.
10. No `.git` directory — no version control; rollback was manual throughout.

## Re-audit 2026-11-15 (post PH-06/07/08) — FINAL BASELINE

Re-verified after PH-06 (Feature P+Y), PH-07 (audit-debt cleanup), PH-08
(geoip owner decision). All claims re-checked against source.

- Tests: **20/20 PASS** (`unittest discover`).
- `project/features/`: all 26 files show Implemented or Partially
  implemented — zero "Planned" remaining.
- `notes/MANIFEST.md`: was missing 7 files (5 dated implementation notes +
  FORENSIC-AUDIT.md + TEST-BASELINE-AUDIT.md) — fixed; now indexes all 25.
- Every notes/ phase has matching plan+log pairs; nothing planned-but-
  unimplemented remains.
- Code spot-checks: `get_or_create_seeds`/`_profile_root`/`_valid_seed_dict`
  present; `identity_provider` wired in engine+orchestrator; config file IO
  present; public API = 17 names.
- PH-08 geoip gate recorded as owner-approved design (docs-only).

### Residual known items (documented, NOT pending work)

1. browserforge consumes process-global `random` → complete fingerprint
   reproducibility impossible without upstream change.
2. BrowserForge fingerprint dict not passed to Camoufox `fingerprint` option
   — frozen non-goal (Stage 4A proved incompatible).
3. `GeoInfo.currency` is metadata-only; no browser currency override.
4. Mode A `timezone_id` is set on fp but no Camoufox launch kwarg consumes it
   (geoip=False path) — locale IS forwarded; timezone relies on host OS.
5. "22 existing checks" F6-Final baseline does not exist — unverifiable.
6. No `.git` — no version control in this workspace.
7. Real camoufox browser launch never smoke-tested (all tests mock it).

### Resume point

NONE — all documented phases complete. Next work is optional: real-browser
smoke test, version bump/release, or new owner-approved scope.

## Resume point

Frozen roadmap Steps 1–5 are code-complete. Remaining work is NOT in the frozen
5 steps: (a) reconcile Step 4 geoip gating with frozen text or get owner waiver;
(b) fix stale project//docs/ status entries; (c) decide fate of features P and Y
(outside frozen scope — need owner approval to schedule); (d) optionally harden
#25 into a real persistence test and validate seeds.json schema on load.
