# 00 — BASELINE: Current Browser Stack (verified)

Baseline: `stealth_engine` v0.2.0 + PH-13..18 (commit d2ecb8f), 2026-11-15.

## Stack

```
camoufox (patched Firefox, C++-level fingerprint spoofing)
    └── playwright (Python async/sync automation API)
        └── stealth_engine wrapper (config/identity/proxy/geo/session/orchestrator)
```

## Verified camoufox facts (from installed package source)

- `launch_options(**kwargs)` accepts `config` dict, `firefox_user_prefs`,
  `geoip` (bool|IP str), `webgl_config`, `fonts`, `screen`, `locale`,
  `humanize`, `os`, `proxy`, `addons`, `window`, `fingerprint`,
  `ff_version`, `main_world_eval`, `enable_cache`, plus **kwargs catch-all
  for config keys like `webrtc:ipv4`, `audio:seed`, `timezone`.
- `audio:seed` → real audio fingerprint noise.
- `canvas:seed` / `fonts:spacing_seed` → **no-ops** (camoufox adds no
  canvas/glyph-spacing noise — upstream issues #528).
- `navigator.hardwareConcurrency` → config key; drives CPU pinning.
- `mediaDevices:*` → auto-generated realistic per-identity defaults.
- Battery API, sensor APIs → **unsupported**.
- `context.add_init_script` is a coroutine in async API.
- `Screen` class in `camoufox.fingerprints` = fingerprint-gen bounds
  (min/max w/h), not exact resolution.

## Engine capabilities already exposed by stealth_engine

- StealthEngine/BulkRunner/BrowserSession lifecycle
- IdentityProvider protocol + seeds.json persistence
- GeoIP engine (GeoResolver/GeoPolicy/GeoInfo extended)
- Proxy management (rotation, health, retries, country filters, cache)
- Network leak guards (socks_remote_dns, disableIPv6)
- Fingerprint depth wiring (webgl/fonts/screen/hw concurrency)
- Behavioral biometrics (behavior.json, bezier, cadence, physics scroll, dwell)
- Session hygiene (localStorage seed, probe_fingerprint, fetch_headers)
- Meta (fingerprint_diversity, drift history, ban_risk_score)
- UX pack (proxy import, validate_fingerprint, sticky geo, drift monitor,
  warmup, listeners/routes, presets, selective export)

## Public API: 29 names — all additive, backward compatible.
