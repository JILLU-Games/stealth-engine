# PF Phase Log

## PF-01 — Launch unblocker ✅ (committed 3d585c7)
- config dict fix, smoke-test fail-not-skip, 188/188 real+unit pass

## PF-02 — Dead sync hooks ✅ (2026-11-16)
- B-25: sync human_move/type/scroll/dwell → AutomationError directing
  to ahuman_*/adwell (were silent no-ops — unawaited coroutines)
- B-26: adwell jiggle → _last_mouse (was dead mouse.position getter)
- Tests: 186 pass + 4 gated skips; HookIntegrationTests rewritten
  to assert the error contract; AsyncHookTests unchanged
- Docs: engine.md, feature H, FEATURES.md, MODULES.md synced

## PF-03 — WebRTC + verification depth ✅ (2026-11-16)
- webrtc:ipv4 config key passed to camoufox; live ICE probe shows
  srflx candidate = real host IP — EXPECTED in Mode A (host IP IS the
  identity, no mismatch). Deep patch effect unverified → documented.
- cdp_session: confirmed always fails on camoufox/Firefox → docstring
  + docs now state it plainly.
- LIVE verified: warmup ✅, block_trackers ✅, new_context ✅,
  js_noise init injected (no error), HAR recording ✅ (rec.har written)
- B-33 NEW BUG found & fixed: record_video_dir crashed the Firefox
  driver at launch (Playwright video = Chromium-only) → now raises
  clear AutomationError before launch. +2 regression tests.

## PF-04 — Release hygiene ✅ (2026-11-16)
- Version 0.2.0 → 0.3.0 (pyproject + __version__); CHANGELOG
  restructured — 0.3.0 section now holds PH-13..21 + BF + PF + docs.
- LeakWarning noise: camoufox warned on every Mode-A launch because
  manual `timezone` config looks like a leak. Intentional by design —
  now passes `i_know_what_im_doing=True` ONLY when geoip=False and a
  timezone is injected (camoufox's designed escape hatch). Verified:
  real smoke launch shows zero warnings.
- Docs sweep: version refs checked (only historical PH-12 record
  mentions 0.2.0 — correct), FEATURES/MODULES/engine.md synced.
- PRODUCTION AUDIT ROADMAP COMPLETE: PF-01..04 all done.
  Remaining documented limitations (not bugs): cdp_session
  Firefox-unavailable, record_video_dir Chromium-only,
  webrtc:ipv4 ICE-effect unverified, TLS/HTTP2 fingerprint
  browser-controlled, js_noise experimental.
