# 03 — PROPOSED FIX PHASES (awaiting approval — NO implementation yet)

Ordered by production risk. Each phase = scope-locked, tests, docs.

## PF-01 — Launch unblocker (CRITICAL, smallest diff)

Scope: `engine.py` `_build_launch_kwargs` only + smoke-test fix.

- Move `audio:seed` into `config` dict (`config["audio:seed"]`)
- Map `webrtc:ipv4` → `config["webrtcIP"]` (verify camoufox actually
  applies it; else use `geoip`/documented mechanism)
- DROP `canvas:seed` + `fonts:spacing_seed` (not camoufox keys —
  already documented no-ops; keep values in seeds.json for js_noise)
- Fix `test_smoke.py`: skip ONLY on ImportError/binary-missing;
  FAIL on launch TypeError
- Verify: `STEALTH_SMOKE=1` real launch green

## PF-02 — Dead sync hooks (CRITICAL)

Scope: `engine.py` human_* methods + docs.

- Option A: sync hooks delegate via internal loop — fragile, not recommended
- Option B (recommended): mark sync `human_move/type/scroll/dwell`
  deprecated → raise `AutomationError` directing to `ahuman_*`/`adwell`
  (consistent with save_state/new_page pattern)
- Fix `adwell` jiggle center → `self._last_mouse` (B-26)
- Update docs/features that claim sync hooks work

## PF-03 — WebRTC + verification depth (MAJOR)

- Verify `webrtcIP` actually applied (real WebRTC candidate probe)
- If ignored: switch Mode A to camoufox-supported mechanism or
  document limitation
- `cdp_session`: mark Firefox-unavailable in docs (keep graceful error)
- Live-verify: warmup, block_trackers, js_noise injection, recording

## PF-04 — Release hygiene (MINOR)

- Version bump + CHANGELOG final
- `LeakWarning` noise reduction if feasible
- Final docs sweep + notes close-out

## Out of scope (locked)

- No new features; no API breaks beyond deprecating dead sync hooks
- TLS/HTTP2 fingerprint work remains documented limitation
