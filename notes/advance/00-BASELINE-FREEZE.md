# 00 — BASELINE FREEZE (2026-11-15)

Frozen reference for all "next-level stealth" work. Verified state.

## Code baseline

- Package: `stealth_engine` **v0.2.0**, commit `3bb1ca0`
- Public API: **22 names** (`__init__.py` `__all__`)
- Modules: `config`, `exceptions`, `identity`, `engine`, `session`,
  `proxy`, `geo`, `orchestrator`, `utils/logging`
- Tests: **67 total** — 66 PASS + 1 env-gated smoke skip
- Git: initialized, clean tree, author Vib Tools
- Wheel: `dist/stealth_engine-0.2.0-py3-none-any.whl` verified

## Completed work (all verified)

| Phase | Scope | Status |
|---|---|---|
| Init/F1-F5 | Package + 12 fixes | ✅ |
| PH-01…05 | Frozen roadmap Steps 1-5 | ✅ |
| PH-06 | Feature P (providers) + Y (file IO) | ✅ |
| PH-07 | Audit-debt cleanup | ✅ |
| PH-08 | GeoIP gate owner decision | ✅ |
| PH-09 | GeoIP core (GeoResolver, filters, cache, batch, validator) | ✅ |
| PH-10 | GeoIP extended (fields, fallback, presets, "auto") | ✅ |
| PH-11 | Hardening (smoke, retries, async hooks, timeout, tz fix) | ✅ |
| PH-12 | Release v0.2.0 | ✅ |

## Stealth surface coverage TODAY

| Layer | Covered | Gaps |
|---|---|---|
| IP/geo | ✅ geoip, webrtc, locale/tz | DNS leak, IPv6 leak, SOCKS5 UDP, header order |
| Canvas/Audio/Fonts | ⚠️ seeds passed to camoufox | pixel-level noise verify |
| WebGL | ⚠️ partial | renderer consistency |
| Navigator/hardware | ⚠️ partial | hw_concurrency/media devices/battery |
| Behavioral | ✅ human hooks | biometrics (bezier, cadence, scroll physics) |
| Session/cookies | ✅ isolation + export | selective export, fingerprint consistency |
| Permissions/API | ❌ none | notification/geo/clipboard/gamepad states |
| TLS/HTTP2 | ⚠️ Firefox-native | JA3/JA4/H2 fingerprint verify |

## Frozen constraints (do NOT violate)

- No JS-injection spoofing (Feature N)
- No BrowserForge→Camoufox wiring (Stage 4A non-goal)
- Engine stays generic; apps own policy
- `geoip` = per-app toggle
- Credential safety, TLS verify ON
- `notes/` never committed

## Known limitations

L1 browserforge global random · L2 partial fp application ·
L3 currency metadata-only · L4 no per-page geo ·
L5 no CI · L6 "22-check baseline" nonexistent
