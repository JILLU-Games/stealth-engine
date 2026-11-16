# 03 — PHASE LOG (advance work)

## Status dashboard

| Phase | Scope | Status | Date |
|---|---|---|---|
| PH-13 | Network/IP hardening | ✅ Complete | 2026-11-15 |
| PH-14 | Fingerprint depth | ✅ Complete | 2026-11-15 |
| PH-15 | Behavioral biometrics | ✅ Complete | 2026-11-15 |
| PH-16 | Session hygiene | ✅ Complete | 2026-11-15 |
| PH-17 | Orchestration/meta | ✅ Complete | 2026-11-15 |
| PH-18 | Practical UX pack | ✅ Complete | 2026-11-15 |

**Completed: ALL 6 (PH-13–18) · Pending: 0**

## Entries

(append per completed phase: date, scope, files, tests, out-of-scope findings)

### PH-13 — Network/IP hardening ✅ (2026-11-15)
- **Delivered:**
  - `ProxyConfig`: `socks5h://` accepted + normalised to `socks5://`;
    `socks4://` accepted.
  - `ProfileConfig`: `disable_ipv6` (→ `network.dns.disableIPv6` pref),
    `proxy_remote_dns` default True (→ `network.proxy.socks_remote_dns`
    for SOCKS proxies) via `firefox_user_prefs` launch kwarg.
  - N20 documented limitation: WebRTC IPv6/STUN full mask unavailable
    (camoufox exposes only `webrtc:ipv4`/`webrtc:ipv6` via geoip).
  - 8 new tests in `test_hardening.py` (ProxySchemeTests +
    NetworkLeakGuardTests).
- **Tests:** 75 total (74 pass + 1 gated skip).
- **Scope audit:** config.py, engine.py, tests, docs only — all in-scope.
- **Docs gap found+fixed:** PH-11 clarification was missing from
  `docs/MODULES.md` — added.
- **Out-of-scope findings:** none.

### PH-14 — Fingerprint depth ✅ (2026-11-15)
- **Delivered:**
  - `ProfileConfig`: `webgl_config`, `fonts`, `custom_fonts_only`,
    `screen_bounds` (→ camoufox `Screen`), `hardware_concurrency`
    (→ `config["navigator.hardwareConcurrency"]`, merged with timezone).
  - `BrowserSession.expect_download(page, timeout_s)` async CM +
    `attach_file(page, selector, path)` helper.
  - **Verification finding (source-verified in camoufox pkg):**
    `audio:seed` → real audio noise; `canvas:seed`/`fonts:spacing_seed`
    are no-ops — camoufox adds NO canvas noise (#528) and NO glyph-spacing
    noise. Documented, not a bug.
  - Battery API + sensor mocks: **unsupported by camoufox** — documented.
  - `media_devices`: camoufox auto-generates realistic per-identity
    defaults already (`set_media_devices_defaults`) — no wiring needed.
- **Tests:** 84 total (83 pass + 1 gated skip); +9 new tests.
- **Scope audit:** config.py, engine.py, test_hardening.py, docs — in-scope.
- **Out-of-scope findings:** none.

### PH-15 — Behavioral biometrics ✅ (2026-11-15)
- **Delivered:**
  - New `stealth_engine/behavior.py`: `BehaviorProfile` (persisted
    `behavior.json`, seed-generated, self-healing), `bezier_path`
    (cubic-bezier + smoothstep + tremor), `physics_scroll_chunks`
    (exponential deceleration, exact dy sum), `dwell_plan`.
  - `BrowserSession` hooks rewired: bezier mouse paths (sync+async),
    per-profile typing cadence, physics scroll; new `human_dwell`/`adwell`.
  - `SessionManager.profile_dir` property added.
  - `BehaviorProfile` exported → 23 public names.
  - +15 tests (`test_behavior.py`); fixed test fakes for `_behavior` attr.
- **Tests:** 99 total (98 pass + 1 gated skip).
- **Bugs found during audit & fixed:** bezier start-point jitter;
  scroll chunk sign/double-sign math; async mouse fake shape.
- **Scope audit:** behavior.py (new), engine.py, session.py, __init__.py,
  tests, docs — all in-scope.
- **Out-of-scope findings:** focus/blur events not scriptable — documented.

### PH-16 — Session hygiene ✅ (2026-11-15)
- **Delivered:**
  - N42 storage_state leak **audit: NO LEAK FOUND** — per-profile
    `storage_state.json`/`user_data` paths verified isolated; regression
    tests added (`test_hygiene.py`).
  - N43 `ProfileConfig.seed_localstorage` — deterministic-per-seed
    localStorage init script (`_sp_id`/`sp_theme`/`sp_ver`/`sp_ts`).
  - N44 `BrowserSession.fetch_headers(url)` — response-header audit via
    context request API (cache/server consistency checks).
  - N47/N48/N49/N51/N52 `BrowserSession.probe_fingerprint(page)` —
    live readback: canvas hash, WebGL renderer, UA, languages,
    hardwareConcurrency, deviceMemory, touch, gamepad count,
    USB/serial presence, notification permission, timezone.
- **Tests:** 108 total (107 pass + 1 gated skip); +9 new tests.
- **Scope audit:** config.py, engine.py, session.py (read-only use),
  test_hygiene.py, docs — in-scope.
- **Out-of-scope findings:** none.

### PH-17 — Orchestration/meta ✅ (2026-11-15)
- **Delivered:**
  - N53 `ProfileConfig.fingerprint_diversity` → per-launch uuid salt →
    `IdentityGenerator(launch_salt)` → rng via `sha256(seed:salt)`.
    Honest limitation: browserforge core fields use global random anyway;
    `seeds.json` device seeds stay profile-stable (documented trade-off).
  - N9 `_record_fingerprint()` → `fingerprint_history.json` (max 50,
    atomic) + drift warning when diversity off.
  - N55 `risk.py` `ban_risk_score(probe, geo, config)` → 0-100 score,
    low/medium/high, per-signal explanations. Exported → 24 names.
  - N54/N56 deferred (optional, documented).
- **Tests:** 119 total (118 pass + 1 gated skip); +11 new tests.
- **Audit fix:** software-renderer penalty raised 30→65 (single strong
  tell should reach "high" level alone).
- **Scope audit:** config.py, identity.py, engine.py, risk.py (new),
  __init__.py, test_meta.py, docs — in-scope.
- **Out-of-scope findings:** none.

### PH-18 — Practical UX pack ✅ (2026-11-15)
- **Delivered (all 8 items, single phase):**
  - N1 `proxy.load_proxies(path)` — host:port:user:pass / user:pass@host /
    scheme:// formats, comments skipped, line-numbered errors.
  - N2 `identity.validate_fingerprint(fp)` — consistency scorer
    (keys, viewport≤screen, UA↔platform↔OS aliases, IANA tz, locale,
    ranges) → {consistent, issues, score}.
  - N3 `geo.StickyGeoStore` — JSON account→proxy+geo bindings.
  - N4 `geo.GeoDriftMonitor` — per-target geo-change detection +
    optional JSON persistence.
  - N5 `BrowserSession.warmup(url)` — goto→move→physics scrolls→dwell.
  - N6 `BrowserSession.add_listener`/`add_route` — context events +
    request interception.
  - N7 `ProfileConfig.preset(name)` + `preset_names()` — us-desktop /
    eu-desktop / mobile-android presets.
  - N8 `SessionManager.export_state(domains=...)` — selective export.
- **Exports:** +5 names → **29 public names**.
- **Tests:** 142 total (141 pass + 1 gated skip); +23 new tests.
- **Audit fix:** platform↔OS alias coherence (Win32→windows etc.).
- **Scope audit:** proxy.py, identity.py, geo.py, session.py, engine.py,
  config.py, __init__.py, test_uxpack.py, docs — in-scope.
- **Out-of-scope findings:** none.
