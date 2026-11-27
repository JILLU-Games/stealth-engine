> 🔒 FROZEN PLAN: see docs/ROADMAP-v2-FREEZE.md. All future engine work must follow that document.

# Project Memory

This file is the concise, durable context for future work on this project. Keep it factual and update it when implementation, architecture, dependencies, or project rules change. Read it together with `AGENTS.md` and `AI_INSTRUCTIONS.md` before making changes.

## Project Overview

- Package: `stealth_engine`, version `0.4.0` Core Preview release candidate; published v0.3.0 remains historical until separately authorized publication.
- Python requirement: `>=3.10`; build backend: setuptools via `pyproject.toml`.
- Packaging uses `setuptools.build_meta` and explicitly discovers only `stealth_engine*`.
- The project root is this `stealth-engine/` directory. There is no database, GUI, or web application framework.
- The project aims to provide isolated browser profiles, coherent identity generation, persistent sessions, proxy/GeoIP handling, and concurrent task orchestration.

## Current Resume Baseline (2026-11-26)

- Frozen pre-release main `3bfdbcb74d1ad8447273938bdaf6a3bed1df6188`, tree `0c0cab836b053104a32aa1e031d89db52fa36c5e`; GitLab main `f78977d2d2ac6c3f26d85e71df0b67016cb07853`, 239/239 entries identical.
- CI #45918602866 CORE_CI_ACCEPTED: 1,304 passed, 21 expected skips, 160 subtests, 75 SDK focused passes; five clean package jobs, five lock audits, notes manifest 108/108.
- SDK-LIFECYCLE-01, FQA-LIFECYCLE-01/A01 and CI-RECOVERY-03 merged and accepted within tested scope. Main protection disabled; deprecated aiohttp API migration, actual GUI manual-close/native restore E2E and external acceptance remain unresolved.
- RELEASE-04 S01–S05 candidate preparation approved; exact CI/merge acceptance pending. Publication and GitLab final sync S06–S07 require separate authorization. Preserve existing v0.3.0 tag `b695b2c6eee3c207132c6a58e2ea8993a50ad921`. GitHub Actions only, no connected machines. See notes/RELEASE-04.md.

## Tech Stack & Dependencies

| Technology        | Purpose                                                           |
| ----------------- | ----------------------------------------------------------------- |
| Python            | Package implementation; Python 3.10 or newer                      |
| Camoufox          | Browser launch/runtime with engine-level fingerprint capabilities |
| Playwright        | Browser context, page, and storage-state APIs                     |
| browserforge      | Browser fingerprint generation                                    |
| Pydantic          | Profile/proxy models and validation                               |
| aiohttp           | Async proxy health and GeoIP HTTP requests                        |
| Loguru            | Logging                                                           |
| tzlocal           | Host IANA timezone detection, including Windows timezone mapping  |
| PyYAML            | YAML serialisation for ProfileConfig file IO (lazy import)        |
| setuptools, wheel | Package build requirements                                        |

Public dependency metadata retains compatible ranges (aiohttp<4); CI has five exact hash locks. No database, frontend framework, or additional runtime service is declared there.

## Architecture & Layout

The package is layered: public configuration and entry points compose identity generation, proxy selection, and profile session management over Camoufox/Playwright. `BulkRunner` coordinates multiple engine sessions. Exceptions and logging are shared support modules.

```text
stealth-engine/
├── .github/copilot-instructions.md  # Repository-specific AI workflow
├── MEMORY.md                        # Durable project context
├── docs/                            # Engine usage, architecture, feature references
├── examples/                        # Example scripts
├── notes/                           # Tracked planning, research, and project-history records
├── project/                         # Permanent module and feature documentation
├── stealth_engine/
│   ├── config.py                    # ProfileConfig and ProxyConfig
│   ├── identity.py                  # IdentityGenerator
│   ├── engine.py                    # StealthEngine and BrowserSession
│   ├── session.py                   # Profile directories, locks, saved state
│   ├── proxy.py                     # ProxyManager and GeoInfo
│   ├── orchestrator.py              # BulkRunner and per-profile results
│   ├── exceptions.py                # Shared exception hierarchy
│   └── utils/logging.py             # Loguru configuration/helpers
├── tests/                           # Unit, regression, hardening, and gated browser tests
├── pyproject.toml
└── README.md
```

Public imports include `ProfileConfig`, `ProxyConfig`, `StealthEngine`, `BrowserSession`, `BulkRunner`, `IdentityProvider`, `BrowserForgeIdentityProvider`, `GeoResolver`, `GeoPolicy`, `matches_geo_policy`, `validate_geo_consistency`, result/status types, and the exception types; see `stealth_engine/__init__.py` for the exact exported API (29 names).

## Implemented Behavior

- `ProfileConfig` and `ProxyConfig` are Pydantic models. They validate required strings, proxy URL schemes, non-negative seeds, and extra headers. `ProfileConfig.target_ip` is an optional host-IP hint for PH-03 Mode A and is not consumed by engine launch code in PH-01. `to_public_dict()` strips URL-embedded credentials from the server URL and masks explicit and embedded proxy credentials.
- `IdentityGenerator` accepts an optional `IdentityProvider` (`build(config, rng) -> dict`); the default `BrowserForgeIdentityProvider` preserves prior behavior. Config `locale`/`timezone` overrides and `_validate()` run uniformly after `provider.build()`. `StealthEngine(config, identity_provider=...)` and `BulkRunner(..., identity_provider=...)` expose the hook (Feature P, PH-06).
- `ProfileConfig` supports atomic JSON/YAML file IO via `save_json`/`load_json`/`save_yaml`/`load_yaml` (Feature Y, PH-06); PyYAML is imported lazily and declared as `pyyaml>=6.0`.
- `IdentityGenerator` obtains a browserforge fingerprint, converts it to primitive fields, applies locale/timezone overrides, caches defensive copies, and computes a SHA-256 fingerprint hash. Its local RNG controls selected traits, but browserforge itself consumes process-global `random` state; runtime verification confirms state changes, and identical seeds do not reproduce complete fingerprints across generator instances. Browserforge exposes no public isolated seed hook in the installed version.
- `IdentityGenerator.get_or_create_seeds()` persists deterministic Canvas/audio/font seed values and config → host → fallback locale/timezone values in the resolved profile root's `seeds.json` (PH-07: `_profile_root()` mirrors engine/session path resolution; loaded files are schema-validated and regenerated when invalid). PH-02 persistence and reload behavior passed a focused two-instance probe. Engine consumption is implemented in PH-03/PH-04.
- **Owner decision (2026-11-15):** `ProfileConfig.geoip` is an intentional per-app ON/OFF toggle — the engine stays a generic reusable API and each consuming app decides per use-case. Proxy + `geoip=False` → seed locale/timezone, Camoufox `geoip=False`. This intentionally differs from the literal frozen Step-4 wording; approved by owner, documented in `docs/MODULES.md`.
- `StealthEngine` exposes sync and async launch methods and composes identity, profile storage, proxy resolution, and a persistent Camoufox context. Launch kwargs include OS, headless mode, profile directory, locale, proxy/GeoIP, device seeds (canvas/audio/fonts from `seeds.json`), and WebRTC IP (host IP in Mode A). Mode A (no proxy) uses seeds for locale/timezone_id and sets `webrtc:ipv4` to `config.target_ip` or the resolved host IP. Mode B (with proxy) uses device seeds but lets GeoIP override locale/timezone_id. The generated identity dict is not passed to Camoufox's `fingerprint` option; full BrowserForge-to-Camoufox identity application is not established. No JavaScript fingerprint injection is intended. `ProfileConfig.geoip` controls Camoufox GeoIP and whether returned GeoIP locale/timezone overrides are applied; proxy health selection still resolves GeoIP.
- `BrowserSession` exposes the Playwright context/page, supports page creation and storage-state saving, and provides sync/async close methods and context-manager use. Human interaction primitives include mouse movement and typing.
- `SessionManager` manages per-profile directories, lock files, and persisted Playwright storage state.
- `stealth_engine/geo.py` (PH-09/PH-10) provides the standalone reusable GeoIP layer: `GeoResolver` resolves GeoIP via `ProxyConfig`, direct IP (`resolve_ip`), or host IP (`resolve(None)`) with ordered multi-endpoint fallback; supports TTL cache (`cache_ttl_s`), country allow/block filters, semaphore-bounded `resolve_many()` with per-item error collection, and `aclose()`. `GeoPolicy.preset()` provides `"any"`/`"us-strict"`/`"eu"` policies. `matches_geo_policy()` is a pure country filter check; `validate_geo_consistency(geo, config)` reports locale/timezone mismatches without raising. `ProxyManager` gained `allowed_countries`/`blocked_countries`/`cache_ttl_s` and shares the module-level `parse_geo_data()` parser, which auto-detects ipinfo vs ip-api shapes and fills extended `GeoInfo` fields (`region`/`city`/`latitude`/`longitude`).
- PF-04 release hygiene: version 0.3.0 (pyproject + **version**), CHANGELOG restructured (0.3.0 = PH-13..21+BF+PF), LeakWarning silenced via targeted `i_know_what_im_doing` (Mode A manual timezone only). PRODUCTION AUDIT ROADMAP COMPLETE — all limitations documented.
- PF-03 verification depth: live-tested warmup/block_trackers/new_context/HAR recording on real camoufox — all work. B-33 NEW BUG: `record_video_dir` crashed Firefox driver at launch (Playwright video=Chromium-only) → now raises clear AutomationError. `cdp_session` confirmed Firefox-unavailable → documented. WebRTC srflx=host IP expected in Mode A. Tests: 188.
- PF-02 dead-hook fix (B-25/B-26): sync `human_move`/`human_type`/`human_scroll`/`human_dwell` were silent no-ops (unawaited coroutines on always-async ctx) → now raise `AutomationError` directing to `ahuman_*`/`adwell`; `adwell` jiggle uses `_last_mouse`. Tests: 186+4 skips.
- PF-01 launch unblocker (B-27/B-28 CRITICAL): `_build_launch_kwargs` sent camoufox patch keys (`canvas:seed`/`audio:seed`/`fonts:spacing_seed`/`webrtc:ipv4`) as top-level kwargs → `launch_persistent_context` TypeError → engine could not launch ANY real browser (masked by smoke-test skip). All moved into `config` dict (verified valid keys vs camoufox properties.json). Smoke tests now fail on launch errors, skip only on missing binary. VERIFIED: STEALTH_SMOKE=1+CANARY=1 → 188/188 pass, 0 skips, real camoufox launch + verify_stealth green. Side-fix: canary IdentityGenerator import path.
- Markdown forensic audit + rewrite: README rewritten (correct quickstart, full tree, honest limits), FEATURES/SECURITY/ARCHITECTURE/ROADMAP stale info fixed, all LOCKED banners + "ghost" naming removed. New bug B-24 found: `new_page()` unawaited coroutine → `new_page_async()` added. Tests: 188.
- BF-04 verification sweep: full suite green (188 tests), scope audit clean, stale docs fixed. BUGFIX ROADMAP COMPLETE — all 23 findings fixed.
- BF-03 minor batch (12 fixes): mouse tracking, verify_stealth mismatches returned, OS inference, WebGL2 noise, run guard, **aexit**, masked cache key, etc. Tests: 188.
- BF-02 major fixes: domain dot-boundary export filter, host-IP fallback chain, js_noise offscreen canvas, resolve_ip path normalization. Tests: 181.
- BF-01 critical bugfixes: `save_state_async()` real storage persistence (was silently broken), Windows-safe `_pid_alive` (ctypes OpenProcess — os.kill(pid,0) killed processes), unawaited `ctx.close()` removed. Tests: 173.
- PH-21 verification: expanded smoke suite (`verify_stealth` on real camoufox, STEALTH_SMOKE=1), fingerprint canary tests (STEALTH_CANARY=1), `examples/stealth_example.py` full-stack demo. Tests: 165 (161 pass + 4 gated skips). engine roadmap complete — all PH-19..21 done.
- PH-20 advanced layer: `js_noise` config (seeded canvas/WebGL noise init script, experimental); `block_trackers()` tracker-domain route; `warmup(template=)` presets; `session_age_days()`. Tests: 162.
- PH-19 engine depth: `verify_stealth()` composite audit, `cdp_session()` CDP passthrough, `new_context()` via camoufox AsyncNewContext, `record_har_*`/`record_video_dir` config options (relative→profile dir). Tests: 153.
- PH-18 UX pack: `proxy.load_proxies()` file import; `validate_fingerprint()` scorer; `StickyGeoStore`/`GeoDriftMonitor` in geo.py; `BrowserSession.warmup`/`add_listener`/`add_route`; `ProfileConfig.preset()`/`preset_names()`; `export_state(domains=)` selective export. Public API 29 names.
- PH-17 meta: `ProfileConfig.fingerprint_diversity` → per-launch `launch_salt` → `IdentityGenerator` derives rng via `sha256(seed:salt)` (seeds.json device seeds stay profile-stable); `_record_fingerprint()` writes `fingerprint_history.json` (max 50) + drift warning; new `risk.py` `ban_risk_score()` (0-100 heuristic). Public API 24 names.
- PH-16 session hygiene: `ProfileConfig.seed_localstorage` (deterministic init-script localStorage seeding); `BrowserSession.probe_fingerprint(page)` live-signal audit + `fetch_headers(url)`; storage_state cross-profile isolation audited — no leak.
- PH-15 behavioral biometrics: new `behavior.py` — `BehaviorProfile` persists per-profile typing/scroll/mouse params to `behavior.json` (seeded, self-healing); human hooks now use cubic-bezier mouse paths, per-profile typing cadence, physics scroll; `human_dwell`/`adwell` attention hooks added; `SessionManager.profile_dir` property. `BehaviorProfile` exported → 23 public names.
- PH-14 fingerprint depth: `ProfileConfig` gained `webgl_config`, `fonts`/`custom_fonts_only`, `screen_bounds` (→ camoufox `Screen`), `hardware_concurrency` (→ `config["navigator.hardwareConcurrency"]`); `BrowserSession.expect_download` + `attach_file` helpers. Verified in camoufox source: `audio:seed` is real; `canvas:seed`/`fonts:spacing_seed` are accepted but no-op (camoufox adds no canvas/glyph noise); battery/sensor APIs unsupported.
- PH-13 network hardening: `ProxyConfig` accepts `socks5h://` (normalised to `socks5://`) and `socks4://`; `ProfileConfig` gained `disable_ipv6` (→ `network.dns.disableIPv6` pref) and `proxy_remote_dns` (default True, → `network.proxy.socks_remote_dns` for SOCKS proxies) emitted via `firefox_user_prefs` launch kwarg. WebRTC IPv6/STUN full masking documented as limitation.
- PH-11 hardening: `ProxyManager` gained `geo_retries` (transient-failure retries with linear backoff) and `health_threshold_ms` (replaces hardcoded 5000 ms pick cutoff); `BrowserSession` gained async `ahuman_move`/`ahuman_type`/`ahuman_scroll`; `BulkRunner` gained `task_timeout_s` (`asyncio.wait_for`, retryable failure); `_build_launch_kwargs` passes `config={"timezone": fp["timezone_id"]}` when `geoip=False` so Mode A timezone reaches the browser; `tests/test_smoke.py` is an env-gated (`STEALTH_SMOKE=1`) real camoufox launch test.
- `ProfileConfig.locale`/`timezone` accept `"auto"` (PH-10): engine resolves the value from GeoIP at launch — proxy `GeoInfo` when available (even with `geoip=False`; explicit opt-in), else host geo via `GeoResolver`; seeds treat `"auto"` as unset.
- `ProxyManager` supports proxy health checks, selection/rotation, and GeoIP-derived metadata. Embedded proxy URL credentials are removed from request/browser server URLs and passed as separate auth fields; `to_public_dict()`, logs, and `mask()` redact credentials. GeoIP HTTPS requests use aiohttp's default certificate verification. Its default endpoint is `https://ipinfo.io/json`; network behavior should be considered when using proxies.
- `BrowserSession.close()` rejects calls from an active event loop before saving state or closing the context; use `await session.aclose()` in async code.
- `BulkRunner` runs async tasks across profiles with bounded concurrency, retries/backoff, ordered results, and shutdown handling.
- Errors use the `StealthEngineError` hierarchy. Logging uses Loguru with module-bound loggers; proxy credentials are masked in public config output and relevant engine logs.

The README's A-Z feature table is a project feature specification, not by itself proof that every feature is fully implemented or wired into the launch path. Features P (pluggable identity providers) and Y (YAML/JSON profile IO) were implemented in PH-06. `tests/test_placeholder.py` remains a placeholder; `tests/test_forensic_regressions.py` covers the audited packaging-related runtime fixes and frozen-roadmap checks #23-26; `tests/test_feature_p_y.py` covers PH-06.

## Current Runtime Contract (2026-11-18)

This addendum is authoritative where earlier phase-summary bullets above describe pre-release behavior differently.

- `StealthEngine.launch()` owns a managed background asyncio loop; `alaunch()` is async. BrowserSession page operations remain async, and sync page/state/human-helper variants raise `AutomationError`.
- Camoufox patch properties are passed through its `config` dictionary. Mode A only passes a manual `webrtc:ipv4` hint for a globally routable address; otherwise it is omitted. This is not a DNS/STUN/WebRTC leak guarantee.
- JavaScript fingerprint modification is off by default; `ProfileConfig.js_noise` is an opt-in experimental exception. BrowserForge output is not passed wholesale to Camoufox, so full identity parity/reproducibility is not claimed.
- The engine creates `ProxyManager` from one profile `ProxyConfig`; pool selection is a standalone manager capability. Video and CDP are unsupported on the tested Firefox backend; `new_context()` depends on an exposed browser handle and returns caller-owned ephemeral state.
- `StealthEngineError` covers engine-defined error subclasses, not every Pydantic, filesystem, network-library, or third-party exception. `ProfileLogger` filters/scrubs profile-owned records only; legacy Loguru records remain process-global.

## Conventions & Project Rules

- Preserve the current Python package structure and public API. Avoid breaking changes to `StealthEngine`, `BulkRunner`, and `ProfileConfig` without explicit approval.
- Follow the existing style: four-space Python indentation, type annotations, module/class/function docstrings, Pydantic models for validated configuration, underscore-prefixed private helpers, and typed project exceptions.
- Keep engine instances and profile state independent; use per-instance state and seeded `random.Random` objects rather than the module-global random generator.
- Preserve engine-level Camoufox fingerprinting; do not replace it with JavaScript injection or plain Playwright.
- `notes/` is tracked and shared with repository contributors. Commit relevant plans/logs with their work; do not store credentials or sensitive personal/production data there. Write a plan before changes and maintain a phase log during work.
- `project/` is the permanent module/feature record. Update the corresponding docs there when package code changes. Update `docs/` when engine behavior or its reference documentation changes.
- Keep changes scoped to the request and run focused verification. The suite contains unit/regression tests plus environment-gated browser tests; establish dependencies before interpreting a collection failure.
- Do not add hidden telemetry or external data transmission.

## Documentation Map

- `AGENTS.md`: mandatory repository workflow and documentation rules.
- `AI_INSTRUCTIONS.md`: universal development workflow and safety rules.
- `README.md`: package overview, quickstart, and A-Z feature specification.
- `docs/`: engine-level references; `docs/ARCHITECTURE.md` documents the intended layers and public API.
- `project/`: permanent per-module and per-feature implementation records.
- `notes/productions/19-CURRENT-BASELINE-FREEZE.md` through `24-ACTUAL-WORKING-LEDGER.md`: current baseline, findings, readiness roadmap/log, error model, and A-Z status; historical reports remain separate.

## Frozen Roadmap Status

- PH-01 (`config.py` optional proxy and `target_ip`) is complete.
- PH-02 (`identity.py` persistent seeds) is implemented and locally verified; engine integration is now complete.
- PH-03/PH-04 engine integration is complete: Mode A uses seeds for locale/timezone_id and device seeds for Camoufox, WebRTC advertises host IP. Mode B uses device seeds but GeoIP overrides locale/timezone_id.
- PH-05 verification is complete: 4 new checks (#23-26) added and PASS; existing 5 tests continue to PASS. The frozen roadmap references 22 prior checks, but no enumerated 1–22 checklist exists in the available project files, so coverage against that baseline is unverified.
- Do not alter `docs/ROADMAP-v2-FREEZE.md` without owner approval.
