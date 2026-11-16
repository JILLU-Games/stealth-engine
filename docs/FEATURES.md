# Feature List

All 26 features below define the stable public scope of stealth_engine. The set is treated as a compatibility contract: features are not removed or renamed, and additions stay additive.

---

| ID  | Feature                                                                                                                                                                      | Status |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| A   | **Async & sync launch API** — `await engine.alaunch()` and `engine.launch()`; `BrowserSession` supports `with`/`async with`                                                                      | Implemented |
| B   | **Bulk runner with bounded concurrency** — `BulkRunner` uses an asyncio semaphore to cap simultaneous browser contexts                                                       | Implemented |
| C   | **Camoufox-based C++ engine-level fingerprint spoofing** — all fingerprint overrides are applied inside the browser engine, not via JavaScript injection                     | Implemented |
| D   | **Coherent identity generation via browserforge** — UA string, navigator object, screen resolution, WebGL renderer, and Canvas fingerprint are generated as a consistent set | Implemented |
| E   | **Deterministic identity via seed** — passing an integer seed to `ProfileConfig` produces the same fingerprint on every run                                                  | Implemented |
| F   | **GeoIP-aware proxy binding** — timezone, locale, and WebRTC IP are automatically matched to the proxy's geolocation                                                         | Implemented |
| G   | **Isolated persistent sessions per profile** — each profile gets its own `user_data_dir`; no cookies or storage are shared                                                   | Implemented |
| H   | **Human-like behavior hooks** — async primitives (`ahuman_move`/`ahuman_type`/`ahuman_scroll`/`adwell`) for mouse movement, typing cadence, and scroll events                                                     | Implemented |
| I   | **Importable, installable package** — `pip install -e .` makes the package available as `from stealth_engine import ...`                                                     | Implemented |
| J   | **JSON-based profile config via Pydantic** — `ProfileConfig` is a Pydantic model; configs can be serialised to / deserialised from JSON                                      | Implemented |
| K   | **Loguru-based structured logging** — all engine events are emitted via loguru with structured fields                                                                        | Implemented |
| L   | **Multi-profile isolation** — running N profiles in parallel produces zero cross-profile state leakage                                                                       | Implemented |
| M   | **Native proxy rotation support** — each browser context can be assigned a different proxy without restarting the engine                                                     | Implemented |
| N   | **Engine-level fingerprint spoofing** — overrides applied at the C++ camoufox layer; `page.evaluate` is not used for spoofing by default (opt-in experimental `js_noise` mode documented separately)                                                       | Implemented |
| O   | **Orchestrator retries with backoff** — `BulkRunner` retries failed tasks with configurable exponential backoff                                                              | Implemented |
| P   | **Pluggable identity providers** — browserforge is the default provider; the interface allows swapping in custom generators                                                  | Implemented |
| Q   | **Proxy health check + failover** — `proxy.py` checks proxy liveness before use and falls over to the next available proxy                                                   | Implemented |
| R   | **Reusable across any automation script** — the package has no framework coupling; import and use in any Python script                                                       | Implemented |
| S   | **Seed-controlled reproducibility across runs** — the same seed always produces the same identity, proxy selection order, and session path                                   | Implemented |
| T   | **Timezone/locale/currency consistency with proxy IP** — all locale-sensitive browser properties are derived from the proxy's GeoIP record                                   | Implemented |
| U   | **Uniform error model** — all exceptions inherit from a single `StealthEngineError` base; callers catch one type                                                             | Implemented |
| V   | **Versioned config schema** — `ProfileConfig` carries a `schema_version` field; unknown fields are ignored for forward compatibility                                         | Implemented |
| W   | **WebRTC leak prevention** — WebRTC IP exposure is suppressed by delegating to camoufox's built-in geoip handling                                                            | Implemented |
| X   | **eXportable session artifacts** — `session.py` can export cookies and Playwright storage state to disk                                                                      | Implemented |
| Y   | **YAML/JSON profile import-export** — `ProfileConfig` can be loaded from and saved to both YAML and JSON files                                                               | Implemented |
| Z   | **Zero global state** — each `StealthEngine` instance is fully independent; importing the package modifies no global Python state                                            | Implemented |

## Forensic Audit Clarifications

- Feature I packaging now uses `setuptools.build_meta` and limits discovery to `stealth_engine*`.
- Feature F honors `ProfileConfig.geoip` for Camoufox GeoIP and locale/timezone overrides. Proxy health selection still uses the GeoIP endpoint.
- Features D/E are not fully realized by the current launch path: the generated BrowserForge dict is not passed to Camoufox's `fingerprint` argument, and browserforge sampling uses process-global randomness. Identical seeds do not currently guarantee identical complete fingerprints across generator instances.
- Feature Z is not fully realized by identity generation: the installed browserforge sampler mutates process-global `random` state.
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
- PH-19 engine depth: `verify_stealth` one-call audit, `cdp_session` passthrough, `new_context` multi-identity contexts, HAR/video recording options.
- PH-20 advanced layer: `js_noise` opt-in canvas/WebGL readback noise (experimental JS-level patch — documented trade-off), `block_trackers` route preset, warmup templates, `session_age_days`.
- PH-21 verification: expanded env-gated smoke suite, fingerprint canary tests, `examples/stealth_example.py` full-stack demo.
- BF-01..BF-04 bugfix sweep: 23 findings fixed — `save_state_async`/`new_page_async` (unawaited-coroutine bugs), Windows-safe `_pid_alive`, domain-boundary export filter, host-IP fallback, offscreen-canvas noise, `resolve_ip` path fix, and 12 minor items. Tests: 188.

- PF-03 live verification: real camoufox launch green; `warmup`,
  `block_trackers`, `new_context`, `save_state_async` verified live.
  HAR recording works; `record_video_dir` is rejected (Chromium-only
  in Playwright). `cdp_session` confirmed unavailable on Firefox —
  documented. WebRTC: Mode A exposes the real host IP by design;
  the `webrtc:ipv4` config patch is passed but deep ICE-level effect
  is unverified — documented limitation.
