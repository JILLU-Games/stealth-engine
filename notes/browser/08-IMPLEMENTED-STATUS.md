# 08 — IMPLEMENTED STATUS TRACKER (browser-depth)

## Current Release Snapshot (2026-11-18)

- v0.3.0 Core Preview prerelease is published; its accepted scope and exclusions are recorded in `notes/productions/16-CORE-PRODUCTION-ACCEPTANCE.md` and `18-CORE-RELEASE-PUBLICATION-EVIDENCE.md`.
- PR-01 local Windows/Python 3.12 verification: 245 passed, 5 expected skips, 32 subtests passed. Browser/canary flags were not enabled; this is not a live-browser result.
- 29 public API names; complete BrowserForge-to-Camoufox parity and external proxy/DNS/WebRTC behavior remain unverified.

## Per-phase additions

| Phase | Adds                                                                                                  | Status |
| ----- | ----------------------------------------------------------------------------------------------------- | ------ |
| PH-19 | `verify_stealth`, CDP wrapper (unsupported on tested Firefox backend), HAR, conditional `new_context` | ✅     |
| PH-20 | Opt-in experimental `js_noise`, `block_trackers`, warmup templates, session age                       | ✅     |
| PH-21 | Gated smoke/canary suite, example and documentation sweep                                             | ✅     |

## Historical Capability Estimates

Earlier percentage estimates were self-assessed, not measured acceptance results. They are retired and must not be used as current coverage claims. Use the source-backed A–Z status in `notes/productions/24-ACTUAL-WORKING-LEDGER.md`.

## PH-19 added ✅ (2026-11-16)

- `verify_stealth` composite audit; HAR options; conditional `new_context` via AsyncNewContext. CDP is unavailable on tested Firefox/Juggler; video is rejected on Firefox.
- Historical phase snapshot: 153 tests (152+1 gated skip)
- Current Firefox limitation: CDP is unavailable; video capture is rejected before launch.

## PH-20 added ✅ (2026-11-16)

- js_noise opt-in canvas/WebGL noise; block_trackers route preset;
  warmup templates; session_age_days
- Historical phase snapshot: 162 tests (161+1 gated skip)

## PH-21 added ✅ (2026-11-16)

- Expanded smoke suite (verify_stealth on real browser)
- Fingerprint canary tests (STEALTH_CANARY=1)
- examples/stealth_example.py full-stack demo
- Historical phase snapshot: 165 tests (161 pass + 4 gated skips)

## Roadmap Status

PH-19…21 are complete per the phase log. The former “85–90% coverage” estimate is not a measured result and has been retired. Core Preview acceptance is limited to the exact CI scope; external proxy behavior and arbitrary-network leak properties remain unverified.
