# Module: engine.py

**File:** `stealth_engine/engine.py`
**Status:** Implemented with documented backend limitations (v0.3.0 Core Preview)
**Verification:** Scoped Core CI includes real Camoufox lifecycle checks; third-party proxy behavior and complete generated-identity parity are not certified.
**Public names:** `StealthEngine`, `BrowserSession`

## Purpose

Core stealth browser engine. Wires identity, session, proxy, and camoufox together into a unified sync/async launch flow. Returns a `BrowserSession` wrapping a live Playwright context.

## Public API

### StealthEngine

|| Method | Signature | Description ||
|| ---------- | ---------------------------- | --------------------------------------------------------------------------------------------- ||
|| `__init__` | `(config: ProfileConfig, *, identity_provider=None)` | Store config; create SessionManager, IdentityGenerator (with optional custom provider), ProxyManager (if proxy set). No I/O. ||
|| `launch` | `() -> BrowserSession` | Starts a managed background asyncio loop for the session lifetime. Raises `LaunchError` if called from a running event loop. BrowserSession page operations remain async. ||
|| `alaunch` | `async () -> BrowserSession` | Async launch: runs full a→i sequence; cleans up on failure. ||

### BrowserSession

|| Member | Type | Description ||
|| ---------------------------------- | --------------- | ------------------------------------------------------------------------- ||
|| `page` | property | Current active Playwright `Page` ||
|| `context` | property | Underlying Playwright `BrowserContext` ||
|| `new_page_async()` | async method | Open new page (awaited `ctx.new_page()`, BF-04/B-24) ||
|| `new_page()` | method | Raises `AutomationError` — async context; use `new_page_async()` ||
|| `save_state()` | method | Raises `AutomationError` — async context; use `save_state_async()` ||
|| `close()` | method | Sync close; rejects an active event loop before side effects. Idempotent. ||
|| `aclose()` | async method | Async counterpart to `close()`. Idempotent. ||
|| `human_move(page, x, y)` | method | Raises `AutomationError` — async context; use `ahuman_move()` (PF-02) ||
|| `human_type(page, selector, text)` | method | Raises `AutomationError` — use `ahuman_type()` (PF-02) ||
|| `human_scroll(page, dy)` | method | Raises `AutomationError` — use `ahuman_scroll()` (PF-02) ||
|| `ahuman_move(page, x, y)` | async method | Async variant of `human_move` — `asyncio.sleep`, non-blocking (PH-11) ||
|| `ahuman_type(page, selector, text)`| async method | Async variant of `human_type` (PH-11) ||
|| `ahuman_scroll(page, dy)` | async method | Async variant of `human_scroll` (PH-11) ||
|| `human_dwell(page, min_s, max_s)` | method | Raises `AutomationError` — use `adwell()` (PF-02) ||
|| `adwell(page, min_s, max_s)` | async method | Async variant of `human_dwell` (PH-15) ||
|| `warmup(url, template?, scrolls?, dwell_s?)` | async method | Warmup flow; templates: default/social/commerce/search (PH-18/20) ||
|| `add_listener(event, callback)` | method | Playwright context event listener — request/response/console/page (PH-18) ||
|| `add_route(pattern, handler)` | async method | Request interception — header inject / tracker block (PH-18, N6) ||
|| `verify_stealth(page?, geo?, fingerprint?)` | async method | Composite audit: probe+risk+geo+fp → `{consistent, summary}` (PH-19, M1) ||
|| `cdp_session(page)` | async method | Raw CDP session wrapper; unsupported on tested Firefox/Juggler backend (PH-19, M2) ||
|| `new_context(**kwargs)` | async method | Spawn an ephemeral context via camoufox `AsyncNewContext` when browser handle is exposed; caller owns lifecycle (PH-19, M4) ||
|| `block_trackers(extra_domains?)` | async method | Abort configured tracker/analytics domains via catch-all route (PH-20, G2) ||
|| `session_age_days()` | method | Days since first recorded launch (fingerprint_history.json) (PH-20, G4) ||
|| `save_state_async()` | async method | Export storage state — awaited `storage_state()` (BF-01 fix) ||
|| `save_state()` | method | Raises `AutomationError` — use `save_state_async()` on async context ||
|| `__enter__` / `__exit__` | context manager | `__exit__` calls `close()`; never suppresses exceptions ||

## Launch Sequence (mandatory order)

```
a) session.ensure_dirs()
b) session.acquire_lock()
c) seeds = identity.get_or_create_seeds()
d) fp = identity.generate()  # copied before launch-specific values are applied
e) pick the configured profile proxy and GeoInfo, if a proxy is configured
f) resolve locale/timezone from GeoIP only when cfg.geoip is true; otherwise
   use persisted seeds. Explicit "auto" values resolve from proxy GeoInfo or
   host GeoResolver and are not persisted as the literal "auto".
g) build AsyncCamoufox kwargs. Device seeds go in the Camoufox config dict;
   timezone is added there only when GeoIP is disabled; configured
   hardwareConcurrency is added when valid; a Mode A webrtc:ipv4 hint is
   added only when globally routable. Other options are conditional.
h) await AsyncCamoufox context entry; optionally add localStorage/js_noise
   init scripts; wrap the persistent context in BrowserSession.
i) ensure an initial Page exists, then record fingerprint history and return.
```

`StealthEngine` constructs its `ProxyManager` from the single `ProfileConfig.proxy` value. The manager supports standalone pools, but this is not an engine-level profile pool API.

## Failure Handling

- Any exception/cancellation during launch → `_emergency_cleanup()` → close Camoufox/proxy manager and release the owned profile lock
- `StealthEngineError` subclasses propagate unchanged
- All other exceptions wrapped in `LaunchError(details={"stage": ...})`

## Camoufox Integration

- Uses `camoufox.async_api.AsyncCamoufox` (async path)
- `persistent_context=True` + `user_data_dir` → returned object is BrowserContext (not Browser)
- `geoip=config.geoip` when a proxy is present; GeoIP-derived locale/timezone overrides apply only when enabled. Owner decision (PH-08): this gate is an intentional per-app ON/OFF toggle — the engine stays generic and each consuming app decides per use-case.
- Device seeds (`canvas:seed`, `audio:seed`, `fonts:spacing_seed`) are passed from `seeds.json` (PH-03/PH-04)
- Mode A (no proxy): a manual `webrtc:ipv4` hint is passed only for a globally routable IPv4; otherwise it is omitted. This is not a DNS/WebRTC leak guarantee.
- Mode B (with proxy): WebRTC IP handled by Camoufox's `geoip=True` mechanism
- The generated BrowserForge identity dict is not passed to Camoufox's `fingerprint` parameter; full identity wiring remains unverified
- JavaScript fingerprint modification is off by default. `ProfileConfig.js_noise=True` is a separate opt-in experimental init-script exception and may be detectable.
- HAR recording is supported through context options; `record_video_dir` and CDP are unsupported for the Camoufox/Firefox backend. `new_context()` is conditional on an exposed browser handle and returns an ephemeral context whose lifecycle belongs to the caller.

## Human Hooks

Sync `human_move`, `human_type`, `human_scroll`, and `human_dwell` raise `AutomationError` because the wrapped Playwright context is async. Use `ahuman_move`, `ahuman_type`, `ahuman_scroll`, and `adwell`; do not wrap the sync methods in `asyncio.to_thread`.

PH-15 added per-profile persisted behavior parameters from `behavior.py` (`behavior.json`): async mouse moves use cubic-bezier trajectories, async typing uses per-profile cadence, async scrolling uses physics chunks, and `adwell` provides a dwell hook. Sync `human_*` methods raise `AutomationError` after PF-02. Focus/blur events are not scriptable — documented limitation.

PH-16 session hygiene: `seed_localstorage=True` injects a deterministic-per-seed `localStorage` init script (empty storage is a bot signal). `BrowserSession.probe_fingerprint(page)` reads back live signals (canvas hash, WebGL renderer, UA, languages, hardwareConcurrency, deviceMemory, touch points, gamepad count, USB/serial presence, notification permission, timezone) for consistency audits; `fetch_headers(url)` returns response headers via the context request API for cache/server checks. Cross-profile `storage_state` isolation audited — per-profile paths verified, no leak found.

PH-17 meta: `fingerprint_diversity` config generates a per-launch salt → `IdentityGenerator(launch_salt=...)` (different rng stream each launch; `seeds.json` device seeds stay stable — documented trade-off). `_record_fingerprint()` appends `{ts, hash, diversity}` to `fingerprint_history.json` (max 50) and warns on drift when diversity is off. New `stealth_engine.risk.ban_risk_score(probe, geo, config)` heuristic exported.

BF-02 fixes: `_resolve_host_ip` is now best-effort (UDP probe → hostname resolution → `"0.0.0.0"` + warning; never raises `LaunchError`); `js_noise` `toDataURL` renders to an offscreen clone so live canvas pixels are never mutated.

BF-03 minor batch: `_last_mouse` position tracking (bezier start point); `verify_stealth` returns normalised `{"source","detail"}` mismatches (previously computed but dropped); `_record_fingerprint` moved post-launch; `__aenter__`/`__aexit__` for `async with`; js_noise adds `WebGL2RenderingContext.readPixels` coverage.

Timezone (PH-11): when Camoufox `geoip` is `False` (always Mode A; Mode B with `geoip=False`), `_build_launch_kwargs` passes `config={"timezone": fp["timezone_id"]}` so the browser timezone matches the resolved value instead of the host OS. When `geoip=True`, Camoufox derives timezone from the exit IP and no override is sent.

Network leak guards (PH-13): `_build_launch_kwargs` emits `firefox_user_prefs` when needed — `network.dns.disableIPv6` when `ProfileConfig.disable_ipv6`, and `network.proxy.socks_remote_dns` for SOCKS proxies when `proxy_remote_dns` is true (default). WebRTC IPv6/STUN full masking is a documented limitation (Camoufox exposes `webrtc:ipv4`/`webrtc:ipv6` only via geoip).

Fingerprint depth (PH-14): `webgl_config`, `fonts`/`custom_fonts_only`, `screen` (from `screen_bounds` via camoufox `Screen`), and `navigator.hardwareConcurrency` (merged into the `config` dict alongside `timezone`) are forwarded when configured. Seed verification finding: camoufox consumes `audio:seed` for real audio-fingerprint noise, but the current camoufox build adds **no canvas noise and no glyph-spacing noise** — `canvas:seed`/`fonts:spacing_seed` kwargs are accepted but are no-ops upstream (documented, not a bug). Battery API and sensor mocks are not supported by camoufox — documented limitation. `BrowserSession.expect_download(page, timeout_s)` async context manager and `attach_file(page, selector, path)` helper added.

## Does NOT

- Implement bulk concurrency (orchestrator's job)
- Retry camoufox launch
- Apply JavaScript fingerprint modification by default; the opt-in `js_noise` exception is experimental
- Modify storage state structure
- Import orchestrator

## Change History

|| Version | Change ||
|| ------- | ------------------------------------------------------------------------------------------- ||
|| 0.1.0 | Initial implementation — Phase 5 ||
|| 0.1.0 | Honor `ProfileConfig.geoip` and guard sync close before resource side effects ||
|| PH-03/04| Load seeds from `get_or_create_seeds()`, pass device seeds to Camoufox, add host IP resolution for WebRTC (Mode A), and ensure Mode A uses seeds for locale/timezone_id ||
|| PH-05 | Added verification tests for checks #23-26 (Mode A/Mode B locale from seeds/GeoIP, seed persistence, proxy=None launches Mode A); all tests PASS ||
|| PH-06 | Added optional `identity_provider` kwarg forwarded to `IdentityGenerator` (Feature P) |
|| PH-11 | Added `ahuman_move`/`ahuman_type`/`ahuman_scroll` async hooks; `config={"timezone": ...}` launch kwarg when `geoip=False` so Mode A timezone reaches the browser |

PF-01/B-27: camoufox patch properties (`canvas:seed`, `audio:seed`,
`fonts:spacing_seed`, `webrtc:ipv4`, `navigator.hardwareConcurrency`,
`timezone`) are passed inside the `config` dict — never as top-level
kwargs (playwright rejects them). This was the production launch
blocker; `STEALTH_SMOKE=1` now launches a real browser green.
B-28: smoke tests skip only on missing binary, not launch errors.

PF-03/B-33: `record_video_dir` raises `AutomationError` at launch —
Playwright video recording is Chromium-only and crashed the Firefox
driver (verified live). `record_har_path`/`record_har_content` work
(real .har produced). `cdp_session` verified unavailable on
camoufox/Firefox (Juggler has no CDP) — documented, graceful error.

## SDK-LIFECYCLE-01 (candidate; CI pending)

Optional `StealthEngine(config, on_close=..., on_error=...)` callbacks run on the owning asyncio loop, accept sync or async callables, and are isolated from cleanup. `on_close(profile_name)` runs once after cleanup attempts; `on_error(profile_name, exception)` reports launch/cleanup errors. Dispatch GUI updates to the GUI thread as appropriate. The context-close notification is post-close: final storage capture is best effort and the previous export is retained on capture failure. Explicit close saves before closing. Session lock/disk operations and lazy behavior-profile loading are offloaded; this does not claim all engine work is nonblocking. `auto_resolve_host_ip=True` preserves the original lookup; false skips only that lookup when no explicit target is provided. `restore_state=False` preserves native persistent storage. True loads only the same profile snapshot and uses the supported Playwright context API (1.59+); this replaces storage, not a merge. No existing public methods or test suites removed.

## FQA-LIFECYCLE-01 (offline candidate)

Close completion now includes lifecycle callback completion before marking the session closed. The owned sync loop shares a single close future among external callers. Initialization-time close notification is registered immediately after context entry; launch owns teardown until setup succeeds, and an observed early close fails launch rather than returning a closed session. Explicit state saves and final capture are serialized using a session lock; new saves are rejected when close begins. Existing seed/history filesystem calls are offloaded without changing their logic. Manual-close final capture remains best effort; preserve the previous snapshot if capture is unavailable. Native restore and actual GUI close E2E remain unverified; no claim that all SDK calls are nonblocking.

FQA-LIFECYCLE-01-A01: manual and explicit close share one stop request protected by the existing close guard. Multiple close callers may join the same worker, but cannot enqueue another stop during executor shutdown. Recovery CI treats unhandled thread exceptions as errors; final acceptance pending.
