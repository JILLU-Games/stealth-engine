# Feature List

All 26 features below define the stable public scope of stealth_engine. The set is treated as a compatibility contract: features are not removed or renamed, and additions stay additive.

---

| ID  | Feature                                                                                                                                                                | Status      |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| A   | **Async & sync launch API** — `await engine.alaunch()` and managed-loop `engine.launch()`; page operations remain async; `BrowserSession` supports `with`/`async with` | Implemented |
| B   | **Bulk runner with bounded concurrency** — `BulkRunner` uses an asyncio semaphore to cap simultaneous browser contexts                                                 | Implemented |
| C   | **Camoufox-based engine-level fingerprint configuration** — supported native options are used; the full generated identity is not injected                             | Partial     |
| D   | **Coherent identity generation via browserforge** — a consistent proposal is generated/validated; only supported values are applied to the browser                     | Partial     |
| E   | **Persistent per-profile seeds** — device/location seeds persist; complete fingerprint equality across runs is not guaranteed                                          | Partial     |
| F   | **GeoIP-aware proxy binding** — locale/timezone behavior follows `geoip`; third-party proxy behavior is not certified                                                  | Partial     |
| G   | **Isolated persistent sessions per profile** — each profile gets its own `user_data_dir`; no cookies or storage are shared                                             | Implemented |
| H   | **Async interaction hooks** — `ahuman_move`/`ahuman_type`/`ahuman_scroll`/`adwell`; sync helper variants raise `AutomationError`                                       | Implemented |
| I   | **Importable, installable package** — `pip install -e .` makes the package available as `from stealth_engine import ...`                                               | Implemented |
| J   | **JSON-based profile config via Pydantic** — `ProfileConfig` is a Pydantic model; configs can be serialised to / deserialised from JSON                                | Implemented |
| K   | **Loguru structured logging** — profile-owned records have scoped level/scrubbing; legacy module-global records remain process-global                                  | Partial     |
| L   | **Per-profile isolation** — separate profile roots and guarded ownership; no universal cross-filesystem isolation guarantee                                            | Partial     |
| M   | **Proxy selection/rotation helpers** — standalone `ProxyManager` supports pools; an engine profile uses its configured single proxy                                    | Partial     |
| N   | **Engine-level fingerprint configuration** — JavaScript spoofing is off by default; `js_noise` is an opt-in experimental exception                                     | Implemented |
| O   | **Orchestrator retries with backoff** — `BulkRunner` retries failed tasks with configurable exponential backoff                                                        | Implemented |
| P   | **Pluggable identity providers** — browserforge is the default provider; the interface allows swapping in custom generators                                            | Implemented |
| Q   | **Proxy health check + failover** — selection code exists; real third-party proxy behavior remains unverified                                                          | Partial     |
| R   | **Reusable across any automation script** — the package has no framework coupling; import and use in any Python script                                                 | Implemented |
| S   | **Seed-controlled reproducibility** — persisted device seeds and proxy selection can be deterministic; complete BrowserForge fingerprints are not                      | Partial     |
| T   | **Timezone/locale consistency** — locale/timezone are resolved by mode; currency is metadata-only and not applied to the browser                                       | Partial     |
| U   | **Typed engine error model** — engine-defined exceptions share a base; Pydantic/stdlib/third-party exceptions may remain distinct                                      | Partial     |
| V   | **Versioned config schema** — `ProfileConfig` carries a `schema_version` field; unknown fields are ignored for forward compatibility                                   | Implemented |
| W   | **WebRTC configuration guards** — hints/GeoIP are configured where supported; no general DNS/STUN/WebRTC leak-free guarantee                                           | Partial     |
| X   | **eXportable session artifacts** — `session.py` can export cookies and Playwright storage state to disk                                                                | Implemented |
| Y   | **YAML/JSON profile import-export** — `ProfileConfig` can be loaded from and saved to both YAML and JSON files                                                         | Implemented |
| Z   | **Profile-scoped engine state** — profile data is instance-scoped; BrowserForge randomness and Loguru handlers retain process-global behavior                          | Partial     |

## Forensic Audit Clarifications

- Feature I packaging now uses `setuptools.build_meta` and limits discovery to `stealth_engine*`.
- Feature F honors `ProfileConfig.geoip` for Camoufox GeoIP and locale/timezone overrides. Proxy health selection still uses the GeoIP endpoint.
- Feature M's pool interface belongs to standalone `ProxyManager`; `StealthEngine` constructs it from one `ProfileConfig.proxy` value.
- Features D/E are not fully realized by the current launch path: the generated BrowserForge dict is not passed to Camoufox's `fingerprint` argument, and browserforge sampling uses process-global randomness. Identical seeds do not currently guarantee identical complete fingerprints across generator instances.
- Feature Z is not fully realized by identity generation: the installed browserforge sampler mutates process-global `random` state.
- Feature K's profile logger scopes engine-owned records only; legacy module-global Loguru records are not profile-isolated.
- Feature W configures a WebRTC hint/GeoIP path but does not guarantee leak prevention across arbitrary DNS, STUN, NAT, proxy, or host-network conditions.
- Feature S: `IdentityGenerator.get_or_create_seeds()` persists deterministic Canvas/audio/font seed values per profile, and the launch path consumes them (PH-03/PH-04). Complete fingerprint reproducibility remains limited by browserforge's process-global `random` usage.
- Feature T: host locale/timezone seed detection follows config → host → fallback precedence. Host IANA timezone lookup uses a lazy tzlocal import; engine launch integration is complete (PH-03/PH-04).
- Feature P (PH-06): implemented via `IdentityProvider` protocol, `BrowserForgeIdentityProvider` default, and `identity_provider` kwargs on `StealthEngine`/`BulkRunner`.
- Feature Y (PH-06): implemented via `ProfileConfig.save_json`/`load_json`/`save_yaml`/`load_yaml` (atomic writes, lazy PyYAML).
- PH-09 geoip core: `geo.py` adds `GeoResolver` (proxy/direct-IP/host-IP resolution, TTL cache, country filters, batch `resolve_many`), `matches_geo_policy`, `validate_geo_consistency`; `ProxyManager` gained country filters + GeoIP cache. Public API is now 20 names.
- PH-10 geoip extended: `GeoInfo` extended fields (`region`/`city`/`latitude`/`longitude`), multi-endpoint fallback, `GeoPolicy` presets (`any`/`us-strict`/`eu`), and `locale`/`timezone="auto"` sentinel resolved from GeoIP at launch. Public API is now 21 names.
- PH-11 hardening: `ProxyManager` `geo_retries`/`health_threshold_ms`, async `ahuman_*` hooks, `BulkRunner.task_timeout_s`, Mode A timezone via camoufox `config` kwarg, env-gated real-browser smoke test (`tests/test_smoke.py`).
- PH-13 network hardening: SOCKS5h/SOCKS4 proxy schemes, `disable_ipv6` + `proxy_remote_dns` Firefox prefs for DNS/IPv6 leak prevention.
- PH-14 fingerprint depth: `webgl_config`/`fonts`/`screen_bounds`/`hardware_concurrency` config options wired to camoufox; audio seed verified real, canvas/fonts-spacing seeds documented as camoufox no-ops; `expect_download`/`attach_file` session helpers.
- PH-15 behavioral biometrics: persisted per-profile `behavior.json` (typing cadence, scroll physics, mouse style); bezier mouse paths; `human_dwell`/`adwell` attention hooks. Public API is now 23 names.
- PH-16 session hygiene: `seed_localstorage` option, `probe_fingerprint`/`fetch_headers` audit helpers, storage_state isolation verified.
- PH-17 meta: `fingerprint_diversity` per-launch identities, `fingerprint_history.json` drift detection, `ban_risk_score` heuristic. Public API is now 24 names.
- PH-18 practical UX pack: proxy pool file import, `validate_fingerprint` scorer, sticky geo bindings, geo drift monitor, warmup flows, request/response hooks, config presets, selective storage export. Public API is now 29 names.
- PH-19 engine depth: `verify_stealth` one-call audit, conditional `cdp_session` wrapper, `new_context`, and HAR options. `cdp_session` is unsupported on the tested Firefox/Juggler backend; `record_video_dir` is rejected for Firefox.
- PH-20 advanced layer: `js_noise` opt-in canvas/WebGL readback noise (experimental JS-level patch — documented trade-off), `block_trackers` route preset, warmup templates, `session_age_days`.
- PH-21 verification: expanded env-gated smoke suite, fingerprint canary tests, `examples/stealth_example.py` full-stack demo.
- BF-01..BF-04 bugfix sweep: 23 findings fixed — `save_state_async`/`new_page_async` (unawaited-coroutine bugs), Windows-safe `_pid_alive`, domain-boundary export filter, host-IP fallback, offscreen-canvas noise, `resolve_ip` path fix, and 12 minor items. The 188-test count is the historical phase snapshot, not the current suite count.

- PF-03 live verification: real camoufox launch green; `warmup`,
  `block_trackers`, `new_context`, `save_state_async` verified live.
  HAR recording works; `record_video_dir` is rejected (Chromium-only
  in Playwright). `cdp_session` confirmed unavailable on Firefox —
  documented. `new_context()` was verified on the tested Camoufox runtime.
  The Mode A ICE observation applies only to that test environment; the
  `webrtc:ipv4` config hint is not a general leak-prevention guarantee.
