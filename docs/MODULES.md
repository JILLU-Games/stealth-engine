# Module Reference

Each module below corresponds to exactly one `.py` file in `stealth_engine/`. No module may be renamed, merged, or removed.

---

## `config.py`

**Purpose:** Define and validate all profile and proxy configuration.

|                  |                                                                                                                                                                                            |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Exposes**      | `ProfileConfig`, `ProxyConfig` (Pydantic models); `ProfileConfig.save_json`/`load_json`/`save_yaml`/`load_yaml` file IO (Feature Y)                                                        |
| **Inputs**       | Raw dict, JSON string, YAML string, or JSON/YAML file path                                                                                                                                 |
| **Outputs**      | Validated model instances ready for consumption by other modules                                                                                                                           |
| **Dependencies** | pydantic, pyyaml (lazy import inside YAML methods)                                                                                                                                         |
| **Does**         | Schema validation, default population, version field management, JSON/YAML serialisation; atomic file writes (`.tmp` → `os.replace`); accepts optional `target_ip` host IP hint for Mode A |
| **Does NOT**     | Launch browsers, make network requests, hold mutable runtime state                                                                                                                         |

---

## `identity.py`

**Purpose:** Generate and validate browser-identity proposals and persist profile seeds. Complete fingerprint reproducibility is not guaranteed.

|                  |                                                                                                                                                                                                                                          |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exposes**      | `IdentityProvider` (Protocol), `BrowserForgeIdentityProvider` (default), `IdentityGenerator.generate()`, `fingerprint_hash()`, `get_or_create_seeds()`                                                                                   |
| **Inputs**       | `ProfileConfig` (seed, locale, timezone, user_data_dir); optional custom `IdentityProvider`                                                                                                                                              |
| **Outputs**      | Fingerprint dict from the configured provider; persisted seed dict with device seeds, locale/timezone values, and source metadata                                                                                                        |
| **Dependencies** | browserforge; tzlocal (lazy import for host IANA timezone detection)                                                                                                                                                                     |
| **Does**         | Delegate raw fingerprint construction to the provider; apply config locale/timezone overrides and validation uniformly; persist Canvas/audio/font seeds at `<user_data_dir>/seeds.json`; select config → host → fallback location values |
| **Does NOT**     | Inject JavaScript or interact with the browser directly                                                                                                                                                                                  |

---

## `engine.py`

**Purpose:** Core stealth browser lifecycle — launch, configure, yield context.

|                  |                                                                                                                                                                          |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Exposes**      | `StealthEngine`                                                                                                                                                          |
| **Inputs**       | `ProfileConfig`, fingerprint dict from `identity.py`, proxy URL from `proxy.py`, optional `IdentityProvider`                                                             |
| **Outputs**      | `BrowserSession` exposing a Playwright `BrowserContext`; page operations remain async, including after the managed-loop sync launch                                      |
| **Dependencies** | camoufox, playwright, `identity.py`, `session.py`, `proxy.py`, `config.py`                                                                                               |
| **Does**         | Launch Camoufox with supported configured overrides; attach a persistent profile session; use the profile's configured proxy; provide async and managed-loop sync launch |
| **Does NOT**     | Apply every BrowserForge field, promise complete generated-to-browser parity, or provide synchronous Playwright page helpers                                             |

---

## `session.py`

**Purpose:** Manage persistent per-profile browser sessions and artifact export.

|                  |                                                                                                                       |
| ---------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Exposes**      | Session lifecycle helpers                                                                                             |
| **Inputs**       | Profile ID, `user_data_dir` path, Playwright `BrowserContext`                                                         |
| **Outputs**      | Persistent context with isolated storage; exported cookies / storage state files                                      |
| **Dependencies** | playwright                                                                                                            |
| **Does**         | Create and manage isolated `user_data_dir` per profile; export cookies and Playwright storage state to disk on demand |
| **Does NOT**     | Share storage between profiles; modify fingerprint settings; manage proxy                                             |

---

## `proxy.py`

**Purpose:** Proxy rotation, health checking, failover, and GeoIP matching.

|                  |                                                                                                                                                                                         |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exposes**      | Proxy manager / rotation helpers                                                                                                                                                        |
| **Inputs**       | List of proxy URLs or `ProxyConfig` objects                                                                                                                                             |
| **Outputs**      | Selected validated proxy URL and GeoIP metadata for a direct `ProxyManager` consumer                                                                                                    |
| **Dependencies** | aiohttp                                                                                                                                                                                 |
| **Does**         | Select/check/fail over among proxies configured on the manager; derive GeoIP metadata; apply country filters and TTL cache. `StealthEngine` creates its manager from one profile proxy. |
| **Does NOT**     | Modify browser fingerprint directly; manage sessions; log outside of structured loguru calls                                                                                            |

---

## `orchestrator.py`

**Purpose:** Bounded-concurrency bulk task execution across multiple profiles.

|                  |                                                                                                                                    |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Exposes**      | `BulkRunner`                                                                                                                       |
| **Inputs**       | List of tasks (coroutines or callables), `ProfileConfig` list, concurrency limit, retry config, optional shared `IdentityProvider` |
| **Outputs**      | Async results / errors per task                                                                                                    |
| **Dependencies** | asyncio, `engine.py`, `config.py`                                                                                                  |
| **Does**         | Schedule N tasks with a semaphore-bounded asyncio pool; retry failed tasks with exponential backoff; emit per-task structured logs |
| **Does NOT**     | Share browser state between tasks; exceed the configured concurrency ceiling; swallow errors silently                              |

---

## `geo.py`

**Purpose:** Standalone reusable GeoIP resolution — no browser dependency.

|                  |                                                                                                                                                                                                                        |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exposes**      | `GeoResolver`, `GeoPolicy`, `matches_geo_policy`, `validate_geo_consistency`                                                                                                                                           |
| **Inputs**       | `ProxyConfig`, direct IP string, or `None` (host IP); optional country allow/block lists; ordered endpoint fallback list                                                                                               |
| **Outputs**      | `GeoInfo`; per-item `ProxyError` in batch mode; consistency report dict                                                                                                                                                |
| **Dependencies** | aiohttp, `config.py`, `proxy.py` (shared `parse_geo_data` + credential helpers)                                                                                                                                        |
| **Does**         | Resolve GeoIP via proxy/direct/host with multi-endpoint fallback; TTL cache; country filters; `GeoPolicy` presets; semaphore-bounded `resolve_many`; config-vs-geo consistency checks; extended GeoInfo fields (PH-10) |
| **Does NOT**     | Launch browsers, manage proxy pools/rotation (that's `proxy.py`), mutate config                                                                                                                                        |

---

## `exceptions.py`

**Purpose:** Shared hierarchy for engine-defined exceptions; external and validation exceptions may remain distinct.

|                  |                                                                                                            |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| **Exposes**      | `StealthEngineError` (base) and typed subclasses                                                           |
| **Inputs**       | n/a                                                                                                        |
| **Outputs**      | Exception classes                                                                                          |
| **Dependencies** | None                                                                                                       |
| **Does**         | Provide `StealthEngineError` and typed config, identity, proxy, session, launch, and automation subclasses |
| **Does NOT**     | Log, suppress, or re-raise errors; import any other stealth_engine module                                  |

---

## `utils/logging.py`

**Purpose:** Configure loguru for structured logging across all modules.

|                  |                                                                                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Exposes**      | Logger setup helper                                                                                                |
| **Inputs**       | Log level, optional sink path                                                                                      |
| **Outputs**      | Configured loguru logger                                                                                           |
| **Dependencies** | loguru                                                                                                             |
| **Does**         | Configure Loguru and provide profile-owned severity/scrubbing wrappers for records emitted through `ProfileLogger` |
| **Does NOT**     | Reconfigure global handlers per profile or guarantee profile filtering for legacy module-global Loguru records     |

## Verified Runtime Clarifications

- `proxy.py` strips URL-embedded credentials from proxy server URLs, passes authentication separately, uses redacted server values in logs, and retains default TLS certificate verification for GeoIP requests.
- `engine.py` applies GeoIP overrides only when `ProfileConfig.geoip` is true. Synchronous `BrowserSession.close()` refuses to run inside an active event loop before touching the context or session state.
- `engine.py` sync `launch()` owns a background event loop for the browser session. Sync page/state/human-helper variants reject async-context operations; use the async methods. `record_video_dir` and CDP are unsupported for the Firefox backend, while `new_context()` is conditional on a browser handle and returns caller-owned ephemeral state.
- `config.py` redacts both explicit and URL-embedded credentials in `ProfileConfig.to_public_dict()`.
- `identity.py` currently does not pass its BrowserForge result to Camoufox. Browserforge sampling consumes process-global `random` state and has no public per-instance seed parameter in the installed API; complete cross-instance seeded reproducibility and zero-global-state behavior are not guaranteed.
- `utils/logging.py` filters/scrubs profile-owned records only; legacy module-global Loguru records remain process-global.
- `IdentityGenerator.get_or_create_seeds()` persists the PH-02 device seeds and locale/timezone values to `<user_data_dir>/seeds.json`; creation and reload were verified. The launch path consumes those seeds (PH-03/PH-04): canvas/audio/fonts seeds and Mode A `webrtc:ipv4` are passed to Camoufox.
- Feature P (PH-06): `IdentityProvider` is a `typing.Protocol` with `build(config, rng) -> dict`; `BrowserForgeIdentityProvider` is the default. Custom providers plug in via `StealthEngine(config, identity_provider=...)` or `BulkRunner(..., identity_provider=...)`; config locale/timezone overrides and validation are applied by `IdentityGenerator` for every provider.
- Feature Y (PH-06): `ProfileConfig` supports `save_json`/`load_json`/`save_yaml`/`load_yaml` with atomic writes; YAML uses lazy `yaml.safe_load`/`safe_dump`.
- PH-07: `get_or_create_seeds()` validates loaded `seeds.json` against required keys/types (`canvas`/`audio`/`fonts` int, `locale`/`timezone_id` non-empty str) and regenerates on invalid payloads; seeds are written to the resolved profile root (`_profile_root()` mirrors `StealthEngine._derive_base_dir` + `SessionManager`), fixing the `user_data_dir`/`profile_name` mismatch edge case.
- **Owner decision (2026-11-15):** `ProfileConfig.geoip` is an intentional per-app ON/OFF toggle. `stealth_engine` is a global reusable API — `engine.py` stays generic and the consuming application decides per use-case whether GeoIP alignment is enabled. With a proxy and `geoip=False`, GeoIP overrides are skipped (seed locale/timezone used) and Camoufox receives `geoip=False`. This intentionally differs from the literal frozen Step-4 wording (`geoip=True` unconditional); the owner has approved the gated behavior.
- PH-09 added `geo.py`: `GeoResolver` (proxy/direct-IP/host-IP resolution, TTL cache, country allow/block filters, `resolve_many` batch), `matches_geo_policy`, and `validate_geo_consistency`. `ProxyManager` gained `allowed_countries`/`blocked_countries`/`cache_ttl_s` and shares the module-level `parse_geo_data()` parser. Public API is now 20 names.
- PH-10 extended geoip: `GeoInfo` gained optional `region`/`city`/`latitude`/`longitude`; `parse_geo_data` auto-detects ipinfo vs ip-api response shapes; `GeoResolver` accepts ordered `endpoints`/`endpoint` lists with sequential fallback (last error carries `attempts`); new `GeoPolicy` presets (`"any"`, `"us-strict"`, `"eu"`); `ProfileConfig.locale`/`timezone` accept `"auto"` sentinel — resolved from GeoIP at launch (proxy GeoInfo preferred, host geo fallback via `GeoResolver`; seeds treat `"auto"` as unset). Public API is now 21 names. PH-12 added `GeoInfo` to public exports → 22 names; version bumped to 0.2.0.
- PH-11 hardening: `ProxyManager` gained `geo_retries`/`health_threshold_ms`; `BrowserSession` gained async `ahuman_*` hooks; `BulkRunner` gained `task_timeout_s`; `_build_launch_kwargs` passes `config={"timezone": ...}` when `geoip=False` (Mode A timezone reaches the browser); `tests/test_smoke.py` is env-gated (`STEALTH_SMOKE=1`).
- PH-13 network hardening: `ProxyConfig` accepts `socks5h://` (normalised to `socks5://`) and `socks4://`; `ProfileConfig` gained `disable_ipv6` and `proxy_remote_dns` (default True) emitting `firefox_user_prefs` (`network.dns.disableIPv6`, `network.proxy.socks_remote_dns`) at launch. WebRTC IPv6/STUN full masking remains a documented limitation.
- PH-14 fingerprint depth: `ProfileConfig` gained `webgl_config`, `fonts`/`custom_fonts_only`, `screen_bounds`, `hardware_concurrency` — forwarded to camoufox launch kwargs/`config`. Verified: `audio:seed` produces real noise; `canvas:seed`/`fonts:spacing_seed` are no-ops in current camoufox (browser adds no canvas/glyph noise — upstream limitation). Battery/sensor APIs unsupported by camoufox. Added `BrowserSession.expect_download` + `attach_file` helpers.
- PH-15 behavioral helpers: `BehaviorProfile` persists per-profile typing/scroll/mouse parameters; async hooks use those profiles. Sync `human_*` helpers raise `AutomationError` after PF-02; use `ahuman_*`/`adwell`. `BehaviorProfile` is exported.
- PH-16 session hygiene: `ProfileConfig.seed_localstorage` init-script option; `BrowserSession.probe_fingerprint` + `fetch_headers` verification helpers; storage_state cross-profile isolation audited (no leak).
- PH-17 meta: `ProfileConfig.fingerprint_diversity` (per-launch salt → different identity; seeds.json stays stable); `fingerprint_history.json` drift tracking in profile dir; new `risk.py` — `ban_risk_score()` heuristic (0-100, low/medium/high). Public API is now 24 names.
- PH-18 practical UX pack: `proxy.load_proxies()` pool-file import (4 formats); `identity.validate_fingerprint()` consistency scorer; `geo.StickyGeoStore` + `geo.GeoDriftMonitor`; `BrowserSession.warmup`/`add_listener`/`add_route`; `ProfileConfig.preset()`/`preset_names()` (us-desktop/eu-desktop/mobile-android); `SessionManager.export_state(domains=...)` selective export. Public API is now 29 names.
- PH-19 engine depth: `verify_stealth()` composite audit; `cdp_session()` wrapper (unsupported on tested Firefox/Juggler backend); `new_context()` via `AsyncNewContext` when a browser handle is available; HAR options. `record_video_dir` is rejected on Firefox with `AutomationError`.
- PH-20 advanced layer: `ProfileConfig.js_noise` opt-in seeded canvas/WebGL readback noise (experimental JS-level); `BrowserSession.block_trackers()` aborts ~20 tracker domains; `warmup(template=...)` presets (default/social/commerce/search); `session_age_days()` from launch history.
- BF-01 critical fixes: `save_state_async()` (awaited `storage_state()` — silent data-loss bug fixed; sync `save_state()` now raises clear error), `_pid_alive` Windows-safe via ctypes `OpenProcess` (was killing live lock-holders via `os.kill(pid,0)`→`TerminateProcess`), unawaited `ctx.close()` removed from sync `close()`.
- BF-02 major fixes: `export_state(domains=)` dot-boundary domain matching (cross-domain leak closed), `_resolve_host_ip` best-effort fallback chain (no more launch-killing LaunchError), `js_noise` offscreen-canvas rendering (live canvas no longer mutated), `GeoResolver.resolve_ip` endpoint path normalization (both provider URL shapes).
- BF-03 minor batch (12 items): mouse position tracking, docstring fix, ProxyError wrapping, `verify_stealth` normalised mismatches (now actually returned), OS inference in `validate_fingerprint`, post-launch drift recording, WebGL2 noise coverage, timezone case-normalisation, `BulkRunner.run()` re-entry guard, masked geo-cache key, `__aenter__`/`__aexit__`, stage comments.

- PF-01 launch unblocker (B-27/B-28): `_build_launch_kwargs` moves all
  camoufox patch properties into the `config` dict (was top-level
  kwargs → `launch_persistent_context` TypeError — engine could not
  launch any real browser). `test_smoke.py` now fails on launch
  errors instead of skipping. Verified: `STEALTH_SMOKE=1` +
  `STEALTH_CANARY=1` → 188/188 pass, 0 skips, real camoufox launch.

- PF-02 dead-hook fix (B-25/B-26): sync `human_move`/`human_type`/
  `human_scroll`/`human_dwell` raised nothing but silently no-oped
  (unawaited coroutines) — they now raise `AutomationError` directing
  to `ahuman_*`/`adwell`. `adwell` jiggle now uses tracked
  `_last_mouse` instead of the nonexistent `mouse.position` getter.

- PF-03 verification depth: live-tested warmup/block_trackers/
  new_context/HAR recording on real camoufox. `record_video_dir`
  now raises a clear `AutomationError` (was a driver crash — B-33).
  `cdp_session` documented as Firefox-unavailable. WebRTC srflx
  candidate exposes host IP in Mode A (expected — real IP is the
  identity); `webrtc:ipv4` config key passed but ICE-level effect
  unverified (documented).

## CI build and dependency boundary

Five native x64 CI locks under `requirements/ci-*.lock` preserve exact PyPI wheel hashes. CI creates fresh environments, verifies wheel bytes, installs offline and uses no build isolation for project builds. Independent wheel/sdist acceptance on five platforms; Twine remains on Python 3.12; all matrix versions are audited from the locked 3.12 auditor. OS/browser assets are not locked; no byte-identical build guarantee. The aiohttp public requirement is constrained to <4 due to the documented deprecated API; runtime migration is deferred. Candidate acceptance pending exact CI.

## SDK-LIFECYCLE-01 (candidate; CI pending)

Optional `StealthEngine(config, on_close=..., on_error=...)` callbacks run on the owning asyncio loop, accept sync or async callables, and are isolated from cleanup. `on_close(profile_name)` runs once after cleanup attempts; `on_error(profile_name, exception)` reports launch/cleanup errors. Dispatch GUI updates to the GUI thread as appropriate. The context-close notification is post-close: final storage capture is best effort and the previous export is retained on capture failure. Explicit close saves before closing. Session lock/disk operations and lazy behavior-profile loading are offloaded; this does not claim all engine work is nonblocking. `auto_resolve_host_ip=True` preserves the original lookup; false skips only that lookup when no explicit target is provided. `restore_state=False` preserves native persistent storage. True loads only the same profile snapshot and uses the supported Playwright context API (1.59+); this replaces storage, not a merge. No existing public methods or test suites removed.
