# notes/production/ — Production Forensic Audit Reports

Source-code + live-verification audit of stealth_engine @ 84da98f+MIT
(2026-11-16). Camoufox binary v156.0.1-beta.36 present — real-browser
verification was performed, not just unit tests.

| File | Contents |
|---|---|
| README.md | Index |
| 01-PRODUCTION-AUDIT.md | All findings with exact code proof + severity |
| 02-VERIFIED-WORKING.md | Feature verification matrix (real vs mocked) |
| 03-FIX-ROADMAP.md | Proposed fix phases (NO implementation yet) |

## Status — COMPLETE ✅ (v0.3.0)

All 4 fix phases done (PF-01..04, commits 3d585c7..HEAD):

- **B-27 FIXED** — engine launches real camoufox (config-dict kwargs)
- **B-25 FIXED** — dead sync hooks raise clear errors → async API
- **B-28 FIXED** — smoke tests fail on launch errors, not skip
- **B-33 FIXED** — record_video_dir rejected (Chromium-only)
- **Verified live:** launch, pages, probe, verify_stealth,
  new_context, save_state, warmup, block_trackers, HAR recording
- **188 tests: all pass** (real smoke + canary included)

Remaining documented limitations (by design, not bugs):
cdp_session unavailable on Firefox, video recording Chromium-only,
webrtc:ipv4 ICE-effect unverified, TLS/HTTP2 browser-controlled,
js_noise experimental opt-in.
