# Changelog

All notable changes to stealth_engine are recorded here.

## [0.2.0] — 2026-11-15

### Added

- Feature P (PH-06): pluggable identity providers — `IdentityProvider` protocol, `BrowserForgeIdentityProvider` default, `identity_provider` kwarg on `StealthEngine` and `BulkRunner`.
- Feature Y (PH-06): `ProfileConfig.save_json`/`load_json`/`save_yaml`/`load_yaml` — atomic JSON/YAML file IO; new `pyyaml>=6.0` dependency (lazy import).
- Frozen roadmap Steps 1–5 (PH-01…PH-05): optional proxy + `target_ip`, persistent `seeds.json` via `get_or_create_seeds()`, Mode A/Mode B launch logic with device seeds and WebRTC IP handling, verification checks #23-26.
- PH-09 geoip core: `geo.py` module — `GeoResolver` (proxy/direct-IP/host-IP resolution, TTL cache, country filters, `resolve_many` batch), `matches_geo_policy`, `validate_geo_consistency`; `ProxyManager` country filters + GeoIP cache + shared `parse_geo_data()`.
- PH-10 geoip extended: `GeoInfo` fields (`region`/`city`/`latitude`/`longitude`), ipinfo+ip-api auto-detect, multi-endpoint fallback, `GeoPolicy` presets (`any`/`us-strict`/`eu`), `locale`/`timezone="auto"` sentinel.
- PH-11 hardening: `ProxyManager` `geo_retries`/`health_threshold_ms`, async `ahuman_*` hooks, `BulkRunner.task_timeout_s`, Mode A timezone via camoufox `config` kwarg, env-gated smoke test.
- PH-12 release: version 0.2.0, `GeoInfo` public export, README/examples refresh. Public API is now 22 names.

### Changed

- `IdentityGenerator` constructor accepts optional `provider`; browserforge extraction moved into `BrowserForgeIdentityProvider` (behavior identical).
- PH-07: `get_or_create_seeds()` writes to the resolved profile root (fixes `user_data_dir`/`profile_name` mismatch) and validates/rejects malformed `seeds.json` payloads; check #25 test now verifies real seed persistence; all `project/features/` statuses synced to implementation reality.
- PH-08 (docs-only): owner decision recorded — `ProfileConfig.geoip` is an intentional per-app ON/OFF toggle for GeoIP alignment; engine remains a generic reusable API.

## [0.3.0] — 2026-11-16

### Added

- PH-13 network hardening: `ProxyConfig` SOCKS5h/SOCKS4 schemes (`socks5h` normalised), `ProfileConfig.disable_ipv6` + `proxy_remote_dns` → `firefox_user_prefs` DNS/IPv6 leak guards.
- PH-14 fingerprint depth: `webgl_config`/`fonts`/`screen_bounds`/`hardware_concurrency` ProfileConfig options wired to camoufox; `expect_download`/`attach_file` session helpers; canvas/fonts-spacing seeds documented as camoufox no-ops, battery/sensor unsupported.
- PH-15 behavioral biometrics: `behavior.py` module — persisted per-profile `behavior.json` params, bezier mouse paths, per-profile typing cadence, physics scroll, `human_dwell`/`adwell` attention hooks; `SessionManager.profile_dir` property; `BehaviorProfile` public export (23 names).
- PH-16 session hygiene: `seed_localstorage` config option, `probe_fingerprint`/`fetch_headers` BrowserSession audit helpers, storage_state isolation audit (no leak found).
- PH-17 meta: `fingerprint_diversity` per-launch identities, `fingerprint_history.json` drift detection, `risk.py` `ban_risk_score` heuristic; `IdentityGenerator.launch_salt` param; `BehaviorProfile`+`ban_risk_score` exports → 24 public names.
- PH-18 practical UX pack: `load_proxies` pool-file import, `validate_fingerprint` scorer, `StickyGeoStore`/`GeoDriftMonitor`, `warmup`/`add_listener`/`add_route` session helpers, `ProfileConfig.preset()`/`preset_names()`, selective `export_state(domains=)`; public API → 29 names.
- PH-19 engine depth: `verify_stealth()` composite audit, `cdp_session()`, `new_context()` (camoufox AsyncNewContext per-context identity), `record_har_path`/`record_har_content`/`record_video_dir` recording options.
- PH-20 advanced layer: `js_noise` opt-in canvas/WebGL readback noise (experimental), `block_trackers()` preset, `warmup(template=)` presets, `session_age_days()`.
- PH-21 verification & hardening: expanded `STEALTH_SMOKE` suite with `verify_stealth` real-browser audit, `STEALTH_CANARY` fingerprint consistency tests, `examples/stealth_example.py` full-stack demo.
- BF-01 critical fixes: `save_state_async()` (storage_state was never persisted — silent data loss), Windows-safe `_pid_alive` (os.kill(pid,0) terminated live processes), removed unawaited `ctx.close()` in sync `close()`.
- BF-02 major fixes: `export_state(domains=)` dot-boundary matching, `_resolve_host_ip` fallback chain, `js_noise` offscreen-canvas fix, `resolve_ip` endpoint path normalization.
- BF-03 minor batch: mouse position tracking, `verify_stealth` normalised mismatches (now returned), `validate_fingerprint` OS inference, post-launch drift recording, WebGL2 noise, timezone normalisation, `BulkRunner.run()` re-entry guard, masked geo-cache key, `__aenter__`/`__aexit__`.
- BF-04 verification & docs sweep: scope audit clean (only declared files), stale-doc fixes, bugfix roadmap closed — all 23 findings resolved.
- PF-03 verification depth: live-verified warmup/block_trackers/new_context/HAR recording on real camoufox; `record_video_dir` now raises a clear error (was a driver crash — Chromium-only feature); `cdp_session` documented as Firefox-unavailable; WebRTC Mode A behaviour documented.
- PF-02 dead-hook fix: sync `human_move`/`human_type`/`human_scroll`/`human_dwell` now raise `AutomationError` directing to the working `ahuman_*`/`adwell` async API (previously silent no-ops); `adwell` jiggle uses tracked mouse position.
- PF-01 launch unblocker: camoufox patch properties (`canvas:seed`, `audio:seed`, `fonts:spacing_seed`, `webrtc:ipv4`, `navigator.hardwareConcurrency`, `timezone`) now passed via the `config` dict — previously sent as top-level kwargs, causing `launch_persistent_context` TypeError on every real launch. Smoke tests now fail on launch errors instead of skipping; verified with `STEALTH_SMOKE=1` real-browser run (188/188 tests, 0 skips).
- Docs audit: README rewritten (correct async quickstart, complete tree, honest limitations); FEATURES/SECURITY/ARCHITECTURE/ROADMAP stale claims fixed; `new_page_async()` added (B-24 unawaited-coroutine fix); `ghost_example.py` renamed to `stealth_example.py`; marketing/lock-banner wording removed.

### Changed

- PF-04 release: version 0.3.0, MIT LICENSE, GitHub-ready docs (README badges/A-Z table/author), CONTRIBUTING.md + SECURITY.md, camoufox warning noise handled via targeted `i_know_what_im_doing`.

## [0.1.0] — 2026-10-19

### Added

- Documentation-only initial scaffold.
- `README.md`: project overview, install instructions, quickstart import, A-Z feature table, non-goals.
- `docs/ARCHITECTURE.md`: layer diagram, module responsibilities, data flow, public API surface.
- `docs/FEATURES.md`: full A-Z feature list, each marked LOCKED.
- `docs/MODULES.md`: per-module purpose, inputs, outputs, dependencies, does/does-not.
- `docs/SECURITY.md`: stealth guarantees, threat model, forbidden regressions, allowed extensions.
- `docs/ROADMAP.md`: six-phase implementation plan (engine → identity → session → proxy → orchestrator → bulk).
- `CHANGELOG.md`: this file.

### Changed

- Nothing (first release).

### Fixed

- Nothing (first release).
