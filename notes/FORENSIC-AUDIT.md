# FORENSIC AUDIT — stealth_engine

## 0. Metadata

- Audit date: 2026-10-19
- Audit target commit/hash: no VCS
- Files scanned: 13 Python files: `stealth_engine/__init__.py`, `stealth_engine/config.py`, `stealth_engine/engine.py`, `stealth_engine/exceptions.py`, `stealth_engine/identity.py`, `stealth_engine/orchestrator.py`, `stealth_engine/proxy.py`, `stealth_engine/session.py`, `stealth_engine/utils/__init__.py`, `stealth_engine/utils/logging.py`, `tests/__init__.py`, `tests/test_forensic_regressions.py`, `tests/test_placeholder.py`
- Total lines scanned: 3,046 (2,854 package lines; 192 test lines)

## 1. Executive Summary

- Total files scanned: 13 (10 package, 3 test)
- Total classes / methods / functions counted: 18 classes; 69 class methods; 5 module-level functions; 1 nested function (`BrowserSession.close`'s `_async_close`).
- Count of gaps found per step: Step 1: 1; Step 2: 5; Step 3: 5; Step 4: 5; Step 5: 4 (3 absent checks and 1 partially covered check).
- Count of files that MUST change per step: Step 1: 1; Step 2: 1; Step 3: 1; Step 4: 2; Step 5: 1.
- Count of UNVERIFIED items: 2.
- Verdict: READY FOR STEP 1 (source audit complete; implementation not performed).

## 2. File Inventory

| Path                                 | Lines | Top-of-file docstring/comment                                                 | Top-level classes / functions                                                                                        | Imports (stdlib / third-party / internal)                                                                                                                                                                                    |
| ------------------------------------ | ----: | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `stealth_engine/__init__.py`         |   104 | `stealth_engine — a reusable stealth browser runtime for browser automation.` | `__getattr__`                                                                                                        | stdlib: `__future__`; third-party: none; internal: `config`, `exceptions` (eager); `engine`, `orchestrator` (lazy map at 34–40)                                                                                              |
| `stealth_engine/config.py`           |   183 | `Configuration models and defaults for the stealth engine.`                   | `_split_proxy_credentials`; `ProxyConfig`; `ProfileConfig`                                                           | stdlib: `__future__`, `typing`, `urllib.parse`; third-party: `pydantic`; internal: none                                                                                                                                      |
| `stealth_engine/engine.py`           |   696 | `Core stealth browser engine lifecycle management.`                           | `StealthEngine`; `BrowserSession`                                                                                    | stdlib: `__future__`, `asyncio`, `os`, `random`, `time`, `types`, `typing`; third-party: Camoufox is imported inside `alaunch` at 165–166; internal: `config`, `exceptions`, `identity`, `proxy`, `session`, `utils.logging` |
| `stealth_engine/exceptions.py`       |    81 | `Custom exception types for the stealth engine.`                              | `StealthEngineError`, `ConfigError`, `IdentityError`, `ProxyError`, `SessionError`, `LaunchError`, `AutomationError` | stdlib: `__future__`; third-party: none; internal: none                                                                                                                                                                      |
| `stealth_engine/identity.py`         |   365 | `Browser identity and fingerprint profile management.`                        | `IdentityGenerator`                                                                                                  | stdlib: `__future__`, `copy`, `hashlib`, `json`, `random`, `typing`; third-party: `browserforge.fingerprints`; internal: `config`, `exceptions`, `utils.logging`                                                             |
| `stealth_engine/orchestrator.py`     |   424 | `Bulk runner and task orchestration across multiple sessions.`                | `ProfileStatus`, `ProfileResult`, `BulkRunner`                                                                       | stdlib: `__future__`, `asyncio`, `random`, `time`, `dataclasses`, `enum`, `typing`; third-party: none; internal: `config`, `engine`, `exceptions`, `utils.logging`                                                           |
| `stealth_engine/proxy.py`            |   457 | `Proxy configuration, rotation, and validation.`                              | `GeoInfo`, `ProxyManager`                                                                                            | stdlib: `__future__`, `asyncio`, `random`, `time`, `typing`; third-party: `aiohttp`, `pydantic`; internal: `config`, `exceptions`, `utils.logging`                                                                           |
| `stealth_engine/session.py`          |   494 | `Browser session creation, management, and teardown.`                         | `_pid_alive`; `SessionManager`                                                                                       | stdlib: `__future__`, `asyncio`, `hashlib`, `json`, `os`, `shutil`, `time`, `pathlib`, `typing`; third-party: none; internal: `config`, `exceptions`, `utils.logging`                                                        |
| `stealth_engine/utils/__init__.py`   |     1 | `Utility sub-package for shared helpers.`                                     | none                                                                                                                 | stdlib: none; third-party: none; internal: none                                                                                                                                                                              |
| `stealth_engine/utils/logging.py`    |    49 | `Logging setup and configuration using loguru.`                               | `configure_logging`, `get_logger`                                                                                    | stdlib: `__future__`, `sys`; third-party: `loguru`; internal: none                                                                                                                                                           |
| `tests/__init__.py`                  |     1 | `Test suite for the stealth_engine package.`                                  | none                                                                                                                 | stdlib: none; third-party: none; internal: none                                                                                                                                                                              |
| `tests/test_forensic_regressions.py` |   190 | `Focused regression tests for verified forensic audit findings.`              | `ProxyCredentialTests`, `EngineRegressionTests`                                                                      | stdlib: `asyncio`, `io`, `tempfile`, `unittest`, `pathlib`, `types`, `unittest.mock`; third-party: `loguru`; internal: `stealth_engine` public API and modules                                                               |
| `tests/test_placeholder.py`          |     1 | No docstring; first line is `# placeholder — tests will be added later`       | none                                                                                                                 | stdlib: none; third-party: none; internal: none                                                                                                                                                                              |

## 3. Per-File Deep Scan

### `stealth_engine/__init__.py`

- Module variables: `__version__` (`str`, line 12, value `"0.1.0"`); `_LAZY` (`dict[str, str]`, lines 34–40); `_LAZY_CACHE` (`dict[str, object]`, line 43); `__all__` (`list[str]`, lines 84–104).
- Classes: none.
- Functions: `__getattr__(name: str) -> object`, lines 46–78; no decorators.
- `__all__` contains 15 names; exact declaration range 84–104.

### `stealth_engine/config.py`

- Module variables: no module-level constants or mutable variables.
- Classes: `ProxyConfig(BaseModel)`, lines 21–55; methods: `_validate_server(cls, v: str) -> str`, lines 36–55, decorators `@field_validator("server")`, `@classmethod`.
- `ProfileConfig(BaseModel)`, lines 58–183; methods: `_reject_empty_strings(cls, v: str) -> str`, lines 91–108, decorators `@field_validator("profile_name", "user_data_dir")`, `@classmethod`; `_validate_seed(cls, v: int | None) -> int | None`, lines 110–126, decorators `@field_validator("seed")`, `@classmethod`; `_validate_extra_headers(cls, v: dict[str, str]) -> dict[str, str]`, lines 128–151, decorators `@field_validator("extra_headers")`, `@classmethod`; `to_public_dict(self) -> dict`, lines 153–183, no decorators.
- Module function: `_split_proxy_credentials(server: str) -> tuple[str, str | None, str | None]`, lines 11–18.

### `stealth_engine/engine.py`

- Module variables: `_log` (line 19); `PlaywrightPage = Any` (line 24); `PlaywrightBrowserContext = Any` (line 25).
- `StealthEngine`, lines 28–319; methods: `__init__(self, config: ProfileConfig) -> None`, 40–60; `launch(self) -> "BrowserSession"`, 66–93; `alaunch(self) -> "BrowserSession"`, 95–207; `_derive_base_dir(self, config: ProfileConfig) -> str | None`, 213–257; `_build_launch_kwargs(self, fp: dict[str, Any], proxy_cfg: Any | None) -> dict[str, Any]`, 259–294; `_emergency_cleanup(ctx_handle: Any | None, session: SessionManager) -> None`, 296–319, decorator `@staticmethod`.
- `BrowserSession`, lines 327–696; methods: `__init__(self, ctx: PlaywrightBrowserContext, ctx_handle: Any, session: SessionManager, proxy_manager: ProxyManager | None, config: ProfileConfig) -> None`, 346–372; `page(self) -> PlaywrightPage`, 378–385, `@property`; `context(self) -> PlaywrightBrowserContext`, 387–394, `@property`; `new_page(self) -> PlaywrightPage`, 400–417; `save_state(self) -> None`, 423–445; `close(self) -> None`, 451–511; `aclose(self) -> None`, 513–547; `__enter__(self) -> "BrowserSession"`, 553–559; `__exit__(self, exc_type: type | None, exc: BaseException | None, tb: object) -> None`, 561–574; `human_move(self, page: PlaywrightPage, x: int, y: int) -> None`, 580–626; `human_type(self, page: PlaywrightPage, selector: str, text: str) -> None`, 628–666; `human_scroll(self, page: PlaywrightPage, dy: int) -> None`, 668–696.
- Nested function: `_async_close() -> None`, lines 492–502.

### `stealth_engine/exceptions.py`

- Module variables: none.
- Classes: `StealthEngineError(Exception)`, lines 6–27, methods `__init__(self, message: str = "An unexpected stealth engine error occurred.", details: dict | None = None) -> None`, 14–21, and `__str__(self) -> str`, 23–27. `ConfigError(StealthEngineError)`, 30–36; `IdentityError(StealthEngineError)`, 39–45; `ProxyError(StealthEngineError)`, 48–54; `SessionError(StealthEngineError)`, 57–63; `LaunchError(StealthEngineError)`, 66–72; `AutomationError(StealthEngineError)`, 75–81. The six subclasses declare no methods.

### `stealth_engine/identity.py`

- Module variables: `_log` (line 17); `_PLATFORM_MAP` (line 20); `_DEFAULT_DEVICE_MEMORY` (line 27); `_COLOR_SCHEMES` (line 30); `_REDUCED_MOTION_OPTIONS` (line 31).
- `IdentityGenerator`, lines 34–364; methods: `__init__(self, config: ProfileConfig) -> None`, 46–64; `generate(self) -> dict[str, Any]`, 70–103; `fingerprint_hash(self) -> str`, 105–125; `_build_fingerprint(self) -> dict[str, Any]`, 131–175; `_extract(self, raw: Any, os_name: str) -> dict[str, Any]`, 177–262; `_derive_timezone(locale: str) -> str`, 264–304, `@staticmethod`; `_validate(fp: dict[str, Any]) -> None`, 306–364, `@staticmethod`.
- No method named `get_or_create_seeds` occurs in the complete file. The public method inventory transitions from `fingerprint_hash` at 105–125 to the internal-helper section at 127–130.

### `stealth_engine/orchestrator.py`

- Module variables: `_log` (line 17); `_NON_RETRYABLE` (line 21).
- Classes: `ProfileStatus(str, Enum)`, lines 24–35, no declared methods; `ProfileResult`, lines 38–57, decorator `@dataclass`, no declared methods; `BulkRunner`, lines 60–424, methods: `__init__(self, profiles: list[ProfileConfig], *, concurrency: int = 3, max_attempts: int = 3, backoff_base_s: float = 1.0, backoff_max_s: float = 30.0, min_start_gap_s: float = 0.0) -> None`, 86–142; `run(self, task_fn: Callable[[BrowserSession], Awaitable[None]]) -> list[ProfileResult]`, 148–210; `run_sync(self, task_fn: Callable[[BrowserSession], Awaitable[None]]) -> list[ProfileResult]`, 212–240; `shutdown(self) -> None`, 242–261; `_run_profile(self, task_fn: Callable[[BrowserSession], Awaitable[None]], idx: int, profile: ProfileConfig, results: list[ProfileResult | None]) -> None`, 267–307; `_enforce_start_gap(self) -> None`, 309–325; `_attempt_profile(self, task_fn: Callable[[BrowserSession], Awaitable[None]], profile: ProfileConfig) -> ProfileResult`, 327–424.

### `stealth_engine/proxy.py`

- Module variables: `_log` (line 17); `_COUNTRY_LOCALE` (line 24); `_COUNTRY_CURRENCY` (line 66); `_FALLBACK_LOCALE` (line 90); `_FALLBACK_CURRENCY` (line 91).
- Classes: `GeoInfo(BaseModel)`, lines 94–109, no methods; `ProxyManager`, lines 112–457. Methods: `__init__(self, proxies: list[ProxyConfig], *, geo_endpoint: str = "https://ipinfo.io/json", timeout_s: float = 8.0, seed: int | None = None) -> None`, 131–154; `_get_lock(self) -> asyncio.Lock`, 156–167; `resolve_geo(self, proxy: ProxyConfig) -> GeoInfo`, 173–239; `health_check(self, proxy: ProxyConfig) -> float`, 241–261; `pick_healthy(self) -> tuple[ProxyConfig, GeoInfo]`, 263–303; `to_playwright(self, proxy: ProxyConfig) -> dict[str, str]`, 305–327; `mask(self, proxy: ProxyConfig) -> dict[str, str | None]`, 329–350; `aclose(self) -> None`, 352–360; `_get_session(self) -> aiohttp.ClientSession`, 366–374; `_build_proxy_url(proxy: ProxyConfig) -> str`, 376–390, `@staticmethod`; `_build_proxy_auth(proxy: ProxyConfig) -> "aiohttp.BasicAuth | None"`, 392–408, `@staticmethod`; `_proxy_parts(proxy: ProxyConfig) -> tuple[str, str | None, str | None]`, 410–413, `@staticmethod`; `_parse_geo(self, data: dict[str, Any], proxy: ProxyConfig) -> GeoInfo`, 415–457.
- No `pick_healthy` definition occurs in the complete file.

### `stealth_engine/session.py`

- Module variables: `_log` (line 18); `_LOCK_MAX_AGE_S` (line 21).
- Module function: `_pid_alive(pid: int) -> bool`, lines 24–41.
- `SessionManager`, lines 44–494; methods: `__init__(self, config: ProfileConfig, base_dir: str | None = None) -> None`, 69–116; `user_data_dir(self) -> str`, 122–129, `@property`; `storage_state_path(self) -> str`, 131–138, `@property`; `lock_path(self) -> str`, 140–147, `@property`; `ensure_dirs(self) -> None`, 153–185; `acquire_lock(self) -> None`, 191–210; `_try_acquire_lock(self, *, retry: bool) -> None`, 212–279; `release_lock(self) -> None`, 281–291; `force_reset(self) -> None`, 297–310; `export_state(self, storage_state: dict) -> None`, 316–374; `import_state(self) -> dict | None`, 376–401; `has_state(self) -> bool`, 407–423; `state_metadata(self) -> dict[str, Any]`, 425–460; `__enter__(self) -> "SessionManager"`, 466–477; `__exit__(self, exc_type: type | None, exc: BaseException | None, tb: object) -> None`, 479–494.

### `stealth_engine/utils/__init__.py`

- Module variables: none. Classes/functions: none.

### `stealth_engine/utils/logging.py`

- Module variable: `_configured: bool = False`, line 10.
- Functions: `configure_logging(level: str = "INFO", json_mode: bool = False) -> None`, lines 13–34; `get_logger(name: str) -> "logger.__class__"`, lines 37–49. Classes: none.

## 4. Step 1 Gap — config.py

- Current fields: `ProfileConfig` is at `stealth_engine/config.py:58–183`; fields are `profile_name`, `os`, `user_data_dir`, `proxy`, `geoip`, `seed`, `headless`, `locale`, `timezone`, `extra_headers`, `log_level`, `schema_version` at lines 78–89.
- `proxy` is already optional:
  ```python
  78:    profile_name: str
  79:    os: Literal["windows", "macos", "linux"] = "windows"
  80:    user_data_dir: str
  ```
  ```python
  81:    proxy: ProxyConfig | None = None
  82:    geoip: bool = True
  83:    seed: int | None = None
  ```
- `target_ip` is missing from the complete `ProfileConfig` field block at lines 78–89. Exact adjacent fields:
  ```python
  85:    locale: str | None = None
  86:    timezone: str | None = None
  87:    extra_headers: dict[str, str] = Field(default_factory=dict)
  ```
- Existing validators: `_validate_server` lines 36–55; `_reject_empty_strings` 91–108; `_validate_seed` 110–126; `_validate_extra_headers` 128–151. Their source declarations include:
  ```python
  36:    @field_validator("server")
  37:    @classmethod
  38:    def _validate_server(cls, v: str) -> str:
  ```
  ```python
  91:    @field_validator("profile_name", "user_data_dir")
  92:    @classmethod
  93:    def _reject_empty_strings(cls, v: str) -> str:
  ```
- Gap count: 1 — `target_ip: str | None = None` is absent. The optional proxy requirement is already present at line 81.
- Insertion point: `stealth_engine/config.py`, within `ProfileConfig`’s field block at lines 78–89, adjacent to `proxy` (line 81).
- Callers: `StealthEngine.__init__` accepts and stores `ProfileConfig` at `stealth_engine/engine.py:40–60`; `IdentityGenerator.__init__` accepts it at `stealth_engine/identity.py:46–64`; `SessionManager.__init__` accepts it at `stealth_engine/session.py:69–116`; `BulkRunner.__init__` accepts `list[ProfileConfig]` at `stealth_engine/orchestrator.py:86–142`. Test construction sites: `tests/test_forensic_regressions.py:37`, `99`, `173`.
- `__all__` is declared at `stealth_engine/__init__.py:84–104`; `ProfileConfig` is already exported at line 87. `target_ip` would be a model field, not a new name in the current export list.

## 5. Step 2 Gap — identity.py

- Current class: `IdentityGenerator`, `stealth_engine/identity.py:34–364`; current methods are listed in Section 3. No `get_or_create_seeds` method exists in the complete file.
- Existing seed handling: constructor creates a local `random.Random(config.seed)` at lines 60–64:
  ```python
  60:        if config.seed is not None:
  61:            # Isolated RNG — never touches the global random state.
  62:            self._rng: random.Random = random.Random(config.seed)
  ```
  BrowserForge generation at lines 143–146 receives `os`, but no seed:
  ```python
  144:            gen = FingerprintGenerator(os=os_name)
  145:            raw = gen.generate(os=os_name)
  ```
- `generate()` signature is `generate(self) -> dict[str, Any]`, lines 70–103. Its implementation returns a deep copy on a cached path and stores `_build_fingerprint()` on first call:
  ```python
  98:        if self._cached_fingerprint is not None:
  99:            # Return a deep copy so callers cannot corrupt the internal cache.
  100:            return copy.deepcopy(self._cached_fingerprint)
  ```
  ```python
  102:        self._cached_fingerprint = self._build_fingerprint()
  103:        return copy.deepcopy(self._cached_fingerprint)
  ```
- `fingerprint_hash()` signature is `fingerprint_hash(self) -> str`, lines 105–125. It calls `generate()` and hashes sorted JSON:
  ```python
  119:        if self._cached_hash is not None:
  120:            return self._cached_hash
  121:
  ```
  ```python
  122:        fp = self.generate()
  123:        serialised = json.dumps(fp, sort_keys=True, ensure_ascii=True)
  124:        self._cached_hash = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
  ```
  ```python
  125:        return self._cached_hash
  ```
- Current documented-in-code `generate()` output keys are listed at lines 81–92: `user_agent`, `viewport`, `screen`, `locale`, `timezone_id`, `platform`, `hardware_concurrency`, `device_memory`, `color_scheme`, `reduced_motion`, `is_mobile`, `has_touch`. The returned mapping is assembled at lines 243–262.
- Gap count: 5 — method absent; no `seeds.json` load; no five-value seed derivation/fallback via `secrets.randbits(32)`; no atomic temp-file/`os.replace` persistence; no returned seed dict with `canvas`, `audio`, `fonts`, `locale`, `timezone_id`.
- Insertion point: `stealth_engine/identity.py` after `fingerprint_hash()` ends at line 125 and before the internal-helper separator at lines 127–130. `generate()` and `fingerprint_hash()` remain at lines 70–125.
- Callers: `StealthEngine.alaunch` calls `self._identity.generate()` at `stealth_engine/engine.py:138` and `self._identity.fingerprint_hash()` at line 194. `fingerprint_hash()` calls `self.generate()` at `stealth_engine/identity.py:122`. Constructors occur at `stealth_engine/engine.py:55` and tests `tests/test_forensic_regressions.py:105`.

## 6. Step 3 Gap — engine.py (Mode A)

- `StealthEngine.__init__` creates a `ProxyManager` only when `config.proxy is not None`, `stealth_engine/engine.py:55–58`:
  ```python
  55:        self._proxy_manager: ProxyManager | None = (
  56:            ProxyManager([config.proxy], seed=config.seed)
  57:            if config.proxy is not None
  ```
- Current `alaunch()` sequence is `stealth_engine/engine.py:95–207`. It acquires the session lock at lines 130–134, calls BrowserForge identity generation at line 138, and enters proxy selection only if `_proxy_manager` exists at lines 144–147:
  ```python
  138:            fp: dict[str, Any] = self._identity.generate()
  139:            # Work on a mutable copy — do not mutate the cached fingerprint.
  140:            fp = dict(fp)
  ```
  ```python
  144:            proxy_cfg = None
  145:            geo: GeoInfo | None = None
  146:            if self._proxy_manager is not None:
  ```
- Current no-proxy launch kwargs use locale from `fp`; no `timezone_id`, `config_overrides`, `target_ip`, `resolved_host_ip`, `seeds.json`, `get_or_create_seeds`, or `webrtc:ipv4` reference occurs in the package source. `_build_launch_kwargs` is at `stealth_engine/engine.py:259–294`:
  ```python
  275:        kwargs: dict[str, Any] = {
  276:            "os": cfg.os,
  277:            "headless": cfg.headless,
  ```
  ```python
  279:            "user_data_dir": self._session.user_data_dir,
  280:            "locale": fp.get("locale", "en-US"),
  281:        }
  ```
- No-proxy `geoip=False` is already assigned at lines 283–288:
  ```python
  287:        else:
  288:            kwargs["geoip"] = False
  ```
- Gap count: 5 — no seeds call; no locale/timezone from host seeds; no Canvas/Audio/Fonts/WebRTC `config_overrides`; no host-IP resolver or `target_ip` use; no explicit `proxy=None` keyword in the no-proxy branch. Source evidence for the final item is `_build_launch_kwargs` lines 283–288, where only the proxy-present branch assigns `kwargs["proxy"]`.
- Insertion point: `StealthEngine.alaunch` after identity retrieval at lines 136–140 and in the proxy/no-proxy branch at lines 142–152; launch option assembly is `_build_launch_kwargs` at lines 259–294.
- Callers: synchronous `launch()` invokes `alaunch()` at `stealth_engine/engine.py:93`; `BulkRunner._attempt_profile` invokes `engine.alaunch()` at `stealth_engine/orchestrator.py:355`.

## 7. Step 4 Gap — engine.py (Mode B)

- Current proxy branch in `StealthEngine.alaunch`, `stealth_engine/engine.py:142–152`:
  ```python
  146:            if self._proxy_manager is not None:
  147:                proxy_cfg, geo = await self._proxy_manager.pick_healthy()
  ```
  ```python
  150:            if geo is not None and cfg.geoip:
  151:                fp["timezone_id"] = geo.timezone_id
  152:                fp["locale"] = geo.locale
  ```
- `ProxyManager` defines `pick_healthy()` returning `(ProxyConfig, GeoInfo)` at `stealth_engine/proxy.py:263–303`; no `pick_healthy` method exists in the complete package source. Proxy conversion is `to_playwright()` at `stealth_engine/proxy.py:305–327`; engine calls it at `stealth_engine/engine.py:285`.
- Camoufox `geoip` is currently assigned from `cfg.geoip` in the proxy branch, not unconditionally `True`, at `stealth_engine/engine.py:283–288`:
  ```python
  284:        if proxy_cfg is not None and self._proxy_manager is not None:
  285:            kwargs["proxy"] = self._proxy_manager.to_playwright(proxy_cfg)
  286:            kwargs["geoip"] = cfg.geoip
  ```
- GeoIP-derived locale/timezone mutation occurs only when `cfg.geoip` is true, lines 150–152. `_build_launch_kwargs` passes `locale` at line 280; it does not pass a `timezone_id` keyword. Seed-derived Canvas/Audio/Fonts overrides and `seeds.json` references are absent from package Python files.
- Gap count: 5 — required `pick_healthy()` name absent; `geoip=True` is not unconditional; locale/timezone override is conditional on `cfg.geoip`; `timezone_id` is not forwarded in launch kwargs; persisted Canvas/Audio/Fonts seeds are not consumed.
- Insertion point: `StealthEngine.alaunch` proxy branch at lines 142–152; launch-option construction at `stealth_engine/engine.py:275–292`; `ProxyManager` method block immediately after `pick_healthy()` ends at line 303 for the required named lookup.
- Mode divergence: no-proxy kwargs set `geoip=False` at line 288; proxy kwargs set `geoip=cfg.geoip` at line 286. The proxy branch sets a `proxy` key at line 285; the no-proxy branch does not set one.
- Callers: engine-to-proxy call at `stealth_engine/engine.py:147`; proxy-to-GeoInfo resolution within `ProxyManager.pick_healthy` at `stealth_engine/proxy.py:285–295`; `to_playwright` call at `stealth_engine/engine.py:285`.

## 8. Step 5 Gap — Tests

- Test files scanned: `tests/__init__.py` (1 line; no test); `tests/test_placeholder.py` (1 line; placeholder comment only); `tests/test_forensic_regressions.py` (190 lines; five test methods).
- Existing test methods and locations:
  - `test_embedded_credentials_are_separated_and_redacted`, lines 23–44.
  - `test_proxy_logs_do_not_include_embedded_password`, lines 46–64.
  - `test_geo_request_keeps_tls_verification_enabled`, lines 66–93.
  - `test_geoip_setting_controls_launch_and_overrides`, lines 95–157.
  - `test_sync_close_rejects_running_loop_before_side_effects`, lines 159–188.
- Check 23 is absent: no test references `get_or_create_seeds`, `seeds["locale"]`, or a no-proxy engine launch. The existing GeoIP test builds a `ProxyConfig` in its loop at lines 97–103.
- Check 24 is partially covered by `test_geoip_setting_controls_launch_and_overrides`: `geo.locale` is set to `"de-DE"` at lines 114–120 and the launch locale is checked at lines 151–155, but the assertion compares to a literal rather than `geo.locale` directly.
- Check 25 is absent: tests contain no `seeds.json` or cross-launch `fingerprint_hash()` assertion. `fingerprint_hash` appears only in engine source at `stealth_engine/engine.py:194`, not in test code.
- Check 26 is absent: no test both constructs `ProfileConfig(proxy=None)` and calls `StealthEngine.alaunch()`; the no-proxy config at test line 173 is used only for `BrowserSession.close()`.
- Gap count: 4 checks, with #24 partial and #23/#25/#26 absent. The test files contain five methods, not 22 separate check methods.
- Insertion points: Mode A launch assertion adjacent to the engine launch assertions at `tests/test_forensic_regressions.py:151–155`; persistence assertion after the launch checks in `EngineRegressionTests` (method ends at line 157); no-proxy launch coverage can be placed in `EngineRegressionTests` after line 157. The existing Mode B locale assertion is at lines 151–155.
- The inline requirement that 22 previous checks remain has no corresponding set of 22 test methods in the scanned test Python files.

## 9. Cross-File Dependency Map

Text graph:

```text
stealth_engine.__init__ --eager--> config.py, exceptions.py
stealth_engine.__init__ --lazy--> engine.py, orchestrator.py
engine.py --> config.py, exceptions.py, identity.py, proxy.py, session.py, utils/logging.py
identity.py --> config.py, exceptions.py, utils/logging.py, browserforge
proxy.py --> config.py, exceptions.py, utils/logging.py, aiohttp, pydantic
session.py --> config.py, exceptions.py, utils/logging.py
orchestrator.py --> config.py, engine.py, exceptions.py, utils/logging.py
engine.py --alaunch--> identity.generate, proxy.pick_healthy, session.ensure_dirs/acquire_lock
orchestrator.py --_attempt_profile--> engine.alaunch, BrowserSession.aclose
```

| From → To                                                              | Evidence                                                                                                                |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `__init__.py` → `config.py`, `exceptions.py`                           | `stealth_engine/__init__.py:17–25`                                                                                      |
| `__init__.py` → `engine.py`, `orchestrator.py` lazy names              | `stealth_engine/__init__.py:34–40`; resolution via `importlib.import_module` at 60–66                                   |
| `engine.py` → `identity.py`                                            | Import at `stealth_engine/engine.py:14`; construction at line 55; `generate()` at line 138                              |
| `engine.py` → `proxy.py`                                               | Import at `stealth_engine/engine.py:15`; selection at line 147; conversion at line 285                                  |
| `engine.py` → `session.py`                                             | Import at `stealth_engine/engine.py:16`; `ensure_dirs()` line 130; `acquire_lock()` line 134; `release_lock()` line 317 |
| `identity.py` → `config.py`, `exceptions.py`, logging                  | Imports at `stealth_engine/identity.py:13–15`                                                                           |
| `proxy.py` → `config.py`, `exceptions.py`, logging                     | Imports at `stealth_engine/proxy.py:13–15`                                                                              |
| `session.py` → `config.py`, `exceptions.py`, logging                   | Imports at `stealth_engine/session.py:14–16`                                                                            |
| `orchestrator.py` → `engine.py`, `config.py`, `exceptions.py`, logging | Imports at `stealth_engine/orchestrator.py:12–15`; `alaunch()` at line 355; `aclose()` at line 399                      |
| `utils/logging.py` → Loguru                                            | Import at `stealth_engine/utils/logging.py:7`                                                                           |

## 10. Risk Assessment

- Public API surface: `__all__` is explicitly enumerated at `stealth_engine/__init__.py:84–104`. `ProfileConfig` and `IdentityGenerator` are not both in the same export set (`ProfileConfig` is at line 87; `IdentityGenerator` has no `__all__` entry). Step 1 adds a model field; Step 2 adds an instance method. Those changes affect exposed model/method behavior even if `__all__` text remains unchanged.
- Test coverage: only five test methods exist at `tests/test_forensic_regressions.py:23`, `46`, `66`, `95`, and `159`; Mode A seed persistence has no test call sites. Check #24 has the partial coverage recorded in Section 8.
- Lazy import chain: `StealthEngine` and `BulkRunner` are resolved lazily through `stealth_engine/__init__.py:34–40`; `__getattr__` imports the target module at lines 60–66. `engine.py` imports `identity.py` at line 14, and `identity.py` imports `browserforge.fingerprints` at line 11. A new eager import in `identity.py` is therefore reachable through lazy engine access.
- Session concurrency: per-profile lock creation is atomic through `open(lock, "x")` at `stealth_engine/session.py:233–236`; stale lock removal/retry is at lines 242–279. A seed file located under the profile path would be accessed inside the engine launch flow after `acquire_lock()` at engine lines 130–138; direct `IdentityGenerator` callers do not pass through that engine call sequence.
- Bulk concurrency: semaphore creation is at `stealth_engine/orchestrator.py:179`; each profile task enters it at line 285. The start-gap lock is created at line 180 and used at `orchestrator.py:309–325`.
- Resource cleanup: launch failures route to `_emergency_cleanup()` at `stealth_engine/engine.py:200–203`, whose implementation releases the session lock at lines 296–319. `BrowserSession.close()` and `aclose()` release the lock at engine lines 509 and 539. `BulkRunner._attempt_profile()` calls `session.aclose()` in `finally` at `orchestrator.py:396–404`. Seed load/persist failures inserted inside the current `alaunch()` try block fall within the existing exception handling at engine lines 198–207.
- GeoIP API coupling: `StealthEngine` currently unpacks the tuple returned by `ProxyManager.pick_healthy()` at `engine.py:147`; `ProxyManager.pick_healthy()` returns `(proxy, geo)` at `proxy.py:295`. The inline Step 4 method name `pick_healthy()` has no definition in package source.

## 11. Files to Modify (Exact List)

| File                                 | Steps touching it | Change type                                                            | Line anchor                                                                                           |
| ------------------------------------ | ----------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `stealth_engine/config.py`           | 1                 | add field                                                              | `ProfileConfig` field block, lines 78–89; `proxy` already exists at 81                                |
| `stealth_engine/identity.py`         | 2                 | add method and seed persistence behavior                               | `IdentityGenerator` public API ends at `fingerprint_hash()` line 125; insertion point before line 127 |
| `stealth_engine/engine.py`           | 3, 4              | modify launch method and kwargs method                                 | `alaunch()` lines 95–207; `_build_launch_kwargs()` lines 259–294                                      |
| `stealth_engine/proxy.py`            | 4                 | add the required `pick_healthy()` callable or equivalent named surface | `pick_healthy()` ends at line 303; `to_playwright()` begins at line 305                               |
| `tests/test_forensic_regressions.py` | 5                 | add checks 23–26 while retaining existing methods                      | existing engine tests at lines 95–188                                                                 |

Files confirmed untouched by the inline five steps: `stealth_engine/__init__.py`, `stealth_engine/exceptions.py`, `stealth_engine/orchestrator.py`, `stealth_engine/session.py`, `stealth_engine/utils/__init__.py`, `stealth_engine/utils/logging.py`, `tests/__init__.py`, `tests/test_placeholder.py`.

## 12. Unverified Items

- UNVERIFIED — whether Camoufox interprets omission of the `proxy` keyword in `StealthEngine._build_launch_kwargs()` as `proxy=None`; requires manual inspection of the installed Camoufox launch-option source. Package source evidence: `stealth_engine/engine.py:283–288`.
- UNVERIFIED — whether the named 22-check F6-Final baseline exists outside the scanned Python test files; requires manual inspection of the external check definition. The scanned test files contain five test methods.

## 13. Attestation

I did not modify any .py/.toml/.json file. I did not read any .md file during this audit. Every claim above is backed by a cited code line. Files written by this audit: notes/FORENSIC-AUDIT.md only.
