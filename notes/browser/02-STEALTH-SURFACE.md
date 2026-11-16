# 02 — STEALTH SURFACE ANALYSIS

What each layer covers today vs what still leaks.

## Covered ✅

| Vector | Coverage |
|---|---|
| IP/geo/locale/timezone/WebRTC-IPv4 | Full (proxy + geoip + auto sentinel + webrtc:ipv4) |
| DNS leak (SOCKS) | Covered via socks_remote_dns pref |
| IPv6 leak | Opt-in disable_ipv6 pref |
| Canvas/Audio/Fonts seeds | audio real; canvas/fonts-spacing = camoufox no-ops |
| WebGL renderer | webgl_config wiring |
| Screen/fonts/hardware | screen_bounds/fonts/hw_concurrency wiring |
| Media devices | camoufox auto per-identity |
| Behavior | bezier/cadence/physics/dwell persisted per profile |
| Session storage | isolation verified + selective export + localStorage seed |
| Permissions/APIs | probe-verified consistent states |
| Meta | diversity, drift, risk scoring |

## Residual surface (honest limits) ⚠️

| Vector | Status | Why |
|---|---|---|
| TLS/JA3/JA4 fingerprint | ~60% | Firefox-native; consistent but version-pinned; can't customize |
| HTTP/2 fingerprint | ~60% | Browser-controlled SETTINGS/frames |
| Header order | ~50% | Browser-controlled; tampering = new fingerprint |
| Canvas pixel noise | ~30% | camoufox adds none (#528) — real gap |
| Behavioral ML analysis | ~70% | Heuristics good; sophisticated ML may still flag |
| IP reputation | n/a | Depends on proxy provider quality |
| Server-side timing | n/a | Out of engine scope |

## Overall stealth coverage estimate: ~80%

Remaining 20% is mostly upstream/browser-controlled — not fixable at
our layer without forking camoufox or Firefox itself.
