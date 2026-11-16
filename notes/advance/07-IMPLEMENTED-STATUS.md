# 05 — IMPLEMENTED STATUS TRACKER (advance)

## Working now ✅ (v0.2.0 baseline)

All A-Z features + geoip engine (see 02-CURRENT-STATE.md in notes/geoip/).

## Per-phase additions (fill as phases complete)

| Phase | Adds | Status |
|---|---|---|
| PH-13 | DNS/IPv6/WebRTC hardening | ✅ |
| PH-14 | Camoufox fingerprint depth wiring | ✅ |
| PH-15 | Bezier/typing/scroll/attention biometrics | ✅ |
| PH-16 | Storage/permission/API consistency | ✅ |
| PH-17 | Diversity/drift/risk-score meta | ✅ |
| PH-18 | Proxy import, fingerprint validator, sticky geo, hooks, presets | ✅ |

## Stealth coverage score (self-assessed)

| Layer | Before | Target after all phases |
|---|---|---|
| IP/geo | ~70% | ~90% (DNS/IPv6 remaining) |
| Canvas/Audio/Fonts | ~50% (unverified) | ~80% (verify+wire) |
| WebGL/Screen/HW | ~40% | ~80% |
| Behavioral | ~60% | ~85% |
| Session/API hygiene | ~50% | ~80% |
| TLS/HTTP2 | ~50% (Firefox-native) | ~60% (verify-only) |
| **Overall** | **~55%** | **~80%** |

> "Total identity hide" is asymptotic — residual surface: TLS/HTTP2
> fingerprint (browser-controlled), advanced ML behavioral analysis,
> server-side timing analysis. These are documented limits, not bugs.

## PH-13 added ✅ (2026-11-15)
- SOCKS5h/SOCKS4 proxy schemes (socks5h→socks5 normalised)
- `disable_ipv6` Firefox pref (IPv6 leak guard)
- `proxy_remote_dns` for SOCKS proxies (DNS leak guard, default on)

## PH-14 added ✅ (2026-11-15)
- Camoufox fingerprint wiring: webgl_config/fonts/screen_bounds/hw_concurrency
- expect_download + attach_file session helpers
- Verified: audio seed real; canvas/fonts-spacing seeds = camoufox no-ops
- Battery/sensor APIs unsupported (documented)

## PH-15 added ✅ (2026-11-15)
- Bezier mouse trajectories, per-profile persisted typing cadence,
  physics scroll, attention dwell hooks — behavior.json per profile
- Public API 23 names (BehaviorProfile exported)

## PH-16 added ✅ (2026-11-15)
- storage_state isolation audit (no leak) + regression tests
- seed_localstorage option; probe_fingerprint + fetch_headers helpers

## PH-17 added ✅ (2026-11-15)
- fingerprint_diversity per-launch identities (launch_salt)
- fingerprint_history.json drift detection
- ban_risk_score heuristic (risk.py) — 24 public names
- N54/N56 deferred (optional)

## PH-18 added ✅ (2026-11-15)
- load_proxies file import; validate_fingerprint scorer; StickyGeoStore;
  GeoDriftMonitor; warmup flows; request/response hooks; config presets;
  selective storage export — 29 public names
