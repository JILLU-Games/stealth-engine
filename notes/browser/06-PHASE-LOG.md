# 06 — PHASE LOG (browser-depth work)

## Status dashboard

| Phase | Scope | Status | Date |
|---|---|---|---|
| PH-19 | Engine depth core (M1-M4) | ✅ Complete | 2026-11-16 |
| PH-20 | Ghost layer (G1-G4) | ✅ Complete | 2026-11-16 |
| PH-21 | Verification & hardening | ✅ Complete | 2026-11-16 |

**Completed: ALL 3 (PH-19-21) · Pending: 0**

## Entries

(append per completed phase: date, scope, files, tests, out-of-scope findings)

### PH-19 — Engine Depth Core ✅ (2026-11-16)
- **Delivered:**
  - M1 `BrowserSession.verify_stealth(page?, geo?, fingerprint?)` —
    composite audit composing probe_fingerprint + ban_risk_score +
    validate_geo_consistency + validate_fingerprint → unified report.
  - M2 `BrowserSession.cdp_session(page)` — raw CDP passthrough via
    `context.new_cdp_session`; graceful AutomationError when unsupported
    (Firefox/Juggler may lack full CDP — verify at runtime).
  - M3 `ProfileConfig.record_har_path`/`record_har_content`/
    `record_video_dir` — relative paths resolve under profile dir,
    passed to launch_persistent_context options.
  - M4 `BrowserSession.new_context(**kwargs)` — camoufox
    `AsyncNewContext` (per-context fpgen identity) with plain
    `browser.new_context` fallback; graceful error when no browser obj.
- **Verification:** 153 tests (152 pass + 1 gated skip); +11 new tests.
- **Camoufox findings:** `AsyncNewContext` exists and gives each
  context its own fpgen fingerprint (navigator/screen/WebGL/fonts/
  voices via init script) — M4 feasible. Persistent context exposes
  `ctx.browser` → used for new_context.
- **Scope audit:** engine.py, config.py, test_engine_depth.py, docs —
  in-scope.
- **Out-of-scope findings:** CDP support on Firefox/Juggler unverified
  live — graceful error path shipped per roadmap.

### PH-20 — Ghost Layer ✅ (2026-11-16)
- **Delivered:**
  - G1 `ProfileConfig.js_noise` + `_js_noise_init_script(seed)` —
    deterministic mulberry32-seeded noise on toDataURL/getImageData/
    readPixels; experimental, documented JS-level trade-off.
  - G2 `BrowserSession.block_trackers(extra_domains?)` — catch-all
    route aborting ~20 tracker domains (GA/GTM/FB pixel/Twitter/LI/
    Hotjar/Segment/Mixpanel/Amplitude/ad networks).
  - G3 `warmup(template=...)` — presets default/social/commerce/
    search; explicit scrolls/dwell_s still override.
  - G4 `BrowserSession.session_age_days()` — age from first
    fingerprint_history.json entry.
- **Verification:** 162 tests (161 pass + 1 gated skip); +9 new tests.
- **Audit fixes:** session_age_days used nonexistent class attr →
  literal filename; test session needed base_dir for isolated
  profile_dir; assertIn-in-or bug in test.
- **Scope audit:** engine.py, config.py, test_ghost.py, docs —
  in-scope.
- **Out-of-scope findings:** none.

### PH-21 — Verification & Hardening ✅ (2026-11-16)
- **Delivered:**
  - V1 `test_smoke.py` expanded — `test_verify_stealth_real_browser`
    runs full audit on real camoufox (env-gated STEALTH_SMOKE=1).
  - V2 `FingerprintCanaryTests` — env-gated STEALTH_CANARY=1:
    generated fingerprints pass validate_fingerprint across seeds +
    required-keys check.
  - V3 `examples/ghost_example.py` — full-stack demo (config→launch→
    human hooks→verify_stealth→risk→session_age).
  - V4 docs sweep — README example listed, MEMORY/CHANGELOG/MODULES/
    FEATURES synced.
- **Verification:** 165 tests (161 pass + 4 gated skips: 2 smoke +
  2 canary).
- **Scope audit:** tests/, examples/, docs only — zero source changes.
- **Out-of-scope findings:** none.
