# P-04 Implementation — Source Evidence and Verification Limits

**Scope:** P-04 only, F-03/F-04/F-10/F-13/F-19.  **Date:** 2026-11-16 UTC.  **Status:** source patch applied, **61/61 focused offline pass**; **2/6 legacy config tests fail due to intentional secret-redaction default**; Camoufox + Windows not verified.  **Fully production accepted:** NO.

- **Frozen initial source baseline:** `a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`.
- **Pre-P04 main HEAD:** `639f3a461973524155f39b645193e20b09416153`.
- **P-04 source commit:** [997e5dd5087d4e366dc573f561e2e9ac3a063520](https://gitlab.com/ivibtools/stealth-engine/-/commit/997e5dd5087d4e366dc573f561e2e9ac3a063520).
- **Source paths edited:** `stealth_engine/identity.py`, `stealth_engine/config.py`, `stealth_engine/engine.py`, `stealth_engine/utils/logging.py` and `tests/test_forensic_regressions.py` (**5 files**). No other executable/source/test file changed.
- **Test runner:** Python 3.13.5 / Linux, `cd /mnt/data/stealth_audit_workspace && PYTHONPATH=/mnt/data/stealth_audit_workspace python /mnt/data/stealth_phase01_test_shim/run_p04_tests.py` — 61 tests, 61 pass, exit=0. This external test harness injects *import-only* placeholder `browserforge`/`camoufox` modules. **No actual browser launched**.
- **Legacy Feature Y test runner:** `unittest.TestLoader().loadTestsFromTestCase(tests.test_feature_p_y.FeatureY_Tests)` — **6 run, 4 pass, 2 FAIL** (`test_json_round_trip`, `test_yaml_round_trip`). Old tests expected embedded proxy credentials to survive default export; new approved secure default intentionally removes them. **No change was made to out-of-scope `tests/test_feature_p_y.py`.** Full legacy compatibility gate unresolved; the next authorized test-contract update needs explicit scope approval.

## Source Git blobs before/after P-04

| Allowed path | Pre P-04 blob | Post P-04 blob |
|---|---|---|
| `stealth_engine/identity.py` | `e5943855b416890b8b718a1d778c00ed61f24b48` | `202fb682941abdf4911436e22eec52f015d743ea` |
| `stealth_engine/config.py` | `a28529363a408803b0797ae773f3a9e2a439ef01` | `5e6f48f80c9ec0766efd32f4cf189aadc305e5ba` |
| `stealth_engine/engine.py` | `eab1e32682dd083ac574c223d51dcb59c91fcb64` | `d7181136ceeae87630004c423fd94635f5325316` |
| `stealth_engine/utils/logging.py` | `024e6153dbcd5ff9df05e103c4ed38668aa1d248` | `a796d9c4413c3c069429542bdfb7c1bd81a16807` |
| `tests/test_forensic_regressions.py` | `8a7582798afb1dfd8eba26f5a761410e5909b438` | `16c1b015c9063898da5d2f7bf8149a284ede6449` |

## F-03 — Generated identity and actual Camoufox launch mapping (code patch; live parity pending)

**Observed code behavior:** generated dict is an *identity proposal*, not a live fingerprint proof. `_build_launch_kwargs` passes explicit `locale`, timezone (when geoip false), `os`, valid seeds, and `navigator.hardwareConcurrency`. For generated `hardware_concurrency`, the key is forwarded unless `ProfileConfig.hardware_concurrency` was explicitly set, which takes precedence. Generated `user_agent`, viewport, screen, `platform`, `device_memory`, `color_scheme`, motion/touch are **not** forwarded as top-level or config overrides. Camoufox generates its own browser-side identity; user-agent/viewport-forcing can cause false consistency. This is a scoped mapping correction and truthful limitation, **NOT verified browser-visible equality**.

**[Source: `stealth_engine/identity.py:426-452`](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/identity.py#L426-452)**

```python
 426 |         The result is cached on the instance.  Calling this method more
 427 |         than once always returns the identical dict (by reference for the
 428 |         cache, structurally identical in all cases).
 429 | 
 430 |         Returns:
 431 |             A generated identity *proposal*, not a guarantee of browser-visible
 432 |             values. Camoufox generates its own browser fingerprint at launch;
 433 |             only the explicitly supported fields mapped by
 434 |             ``StealthEngine._build_launch_kwargs`` are applied. The remaining
 435 |             fields are diagnostics and must not be reported as live spoofed
 436 |             properties. Contains the following keys:
 437 | 
 438 |             - ``user_agent`` (:class:`str`)
 439 |             - ``viewport`` (:class:`dict` with ``width`` / ``height``)
 440 |             - ``screen`` (:class:`dict` with ``width`` / ``height``)
 441 |             - ``locale`` (:class:`str`)
 442 |             - ``timezone_id`` (:class:`str`)
 443 |             - ``platform`` (:class:`str`)
 444 |             - ``hardware_concurrency`` (:class:`int`)
 445 |             - ``device_memory`` (:class:`int`)
 446 |             - ``color_scheme`` (:class:`str`)
 447 |             - ``reduced_motion`` (:class:`str`)
 448 |             - ``is_mobile`` (:class:`bool`)
 449 |             - ``has_touch`` (:class:`bool`)
 450 | 
 451 |         Raises:
 452 |             IdentityError: If fingerprint generation or validation fails
```

**[Source: `stealth_engine/engine.py:784-798`](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/engine.py#L784-798)**

```python
 784 | 
 785 |         # Apply only Camoufox-supported keys from the generated proposal.
 786 |         # Camoufox itself draws the UA, viewport, screen, platform, memory,
 787 |         # color-scheme and touch properties; our separately generated values
 788 |         # cannot truthfully be claimed browser-visible without a live readback.
 789 |         # A user-requested hardware concurrency override wins over the draw.
 790 |         concurrency = (cfg.hardware_concurrency if cfg.hardware_concurrency is not None
 791 |                        else fp.get("hardware_concurrency"))
 792 |         if isinstance(concurrency, int) and not isinstance(concurrency, bool) and concurrency > 0:
 793 |             launch_config["navigator.hardwareConcurrency"] = concurrency
 794 |         if cfg.webgl_config is not None:
 795 |             kwargs["webgl_config"] = cfg.webgl_config
 796 |         if cfg.fonts is not None:
 797 |             kwargs["fonts"] = list(cfg.fonts)
 798 |             if cfg.custom_fonts_only:
```

**Target tests:** `P04FingerprintContractTests.test_f03_supported_generated_hardware_concurrency_is_forwarded` and `test_f03_explicit_hardware_config_wins_over_proposed_identity` ([test source](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/tests/test_forensic_regressions.py#L1299-1326)). Both pass with fake launch config. Real Camoufox fingerprint parity remains unverified and F-03 not release accepted.

## F-04 — Legacy seeds honor later explicit locale/timezone without rotating numeric seeds

**Observed code behavior:** `seeds.json` continues to store persistent `canvas`, `audio` and `fonts` integers. If a valid legacy seed file is loaded, explicit newly provided locale/timezone values replace saved values and persist via atomic `os.replace`, without changing numeric seeds. `auto` does **not** persist as a literal setting; corrupt metadata and write failures remain visible. Prior locale/timezone continues when config is not explicitly set. Linux filesystem tests verify behavior, Windows persistence and real browser locale remain unverified.

**[Source: `stealth_engine/identity.py:484-541`](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/identity.py#L484-541)**

```python
 484 |     def get_or_create_seeds(self) -> dict:
 485 |         """Load or create persistent per-profile fingerprint seeds.
 486 | 
 487 |         Numeric device seeds derive from ``config.seed``. Locale and timezone
 488 |         values prefer explicit config, then host detection, then fallback.
 489 |         """
 490 |         seeds_path = _profile_root(self._config) / "seeds.json"
 491 | 
 492 |         if seeds_path.exists():
 493 |             try:
 494 |                 loaded = json.loads(seeds_path.read_text(encoding="utf-8"))
 495 |             except (json.JSONDecodeError, OSError) as exc:
 496 |                 _log.warning(
 497 |                     "Corrupt seeds.json at {} — regenerating: {}",
 498 |                     seeds_path,
 499 |                     exc,
 500 |                 )
 501 |             else:
 502 |                 if _valid_seed_dict(loaded):
 503 |                     # Explicit locale/timezone take precedence over legacy saved
 504 |                     # metadata; numeric seeds remain byte-for-byte stable.
 505 |                     # The "auto" sentinel is deliberately resolved at launch.
 506 |                     updates = {}
 507 |                     for field, key, source in (
 508 |                         (self._config.locale, "locale", "locale_source"),
 509 |                         (self._config.timezone, "timezone_id", "timezone_source"),
 510 |                     ):
 511 |                         if isinstance(field, str) and field.strip() and field.strip().lower() != "auto":
 512 |                             if loaded[key] != field or loaded.get(source) != "config":
 513 |                                 updates[key] = field
 514 |                                 updates[source] = "config"
 515 |                     if updates:
 516 |                         revised = {**loaded, **updates}
 517 |                         tmp_path = seeds_path.with_suffix(".json.tmp")
 518 |                         try:
 519 |                             tmp_path.write_text(json.dumps(revised, indent=2, sort_keys=True), encoding="utf-8")
 520 |                             os.replace(tmp_path, seeds_path)
 521 |                         except OSError as exc:
 522 |                             try:
 523 |                                 tmp_path.unlink(missing_ok=True)
 524 |                             except OSError:
 525 |                                 pass
 526 |                             raise IdentityError(
 527 |                                 "Failed to persist updated locale/timezone seeds",
 528 |                                 details={"path": str(seeds_path), "reason": str(exc)},
 529 |                             ) from exc
 530 |                         return revised
 531 |                     return loaded
 532 |                 _log.warning(
 533 |                     "seeds.json at {} missing required keys or has wrong "
 534 |                     "types — regenerating",
 535 |                     seeds_path,
 536 |                 )
 537 | 
 538 |         base_rng = random.Random(
 539 |             self._config.seed
 540 |             if self._config.seed is not None
 541 |             else secrets.randbits(32)
```

**Target tests:** `P04SeedPrecedenceTests` (three cases), source [target tests](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/tests/test_forensic_regressions.py#L1329-1373).

## F-10 — Default JSON/YAML export redacts credentials (contract change)

**Observed code behavior:** default `.save_json()` and `.save_yaml()` remove embedded proxy username/password and explicit proxy auth, redact selected sensitive `extra_headers`, create exclusive local temporary file mode `0600` on POSIX, and atomically replace. Explicit `include_secrets=True` preserves legacy complete round-trip **only for private backups**. Redacted defaults intentionally require secrets re-entry before proxy auth works. Output file modes on Windows/NTFS ACLs **not verified**. Existing default round-trip tests are now obsolete, but out of P-04 test-file Scope Lock.

**[Source: `stealth_engine/config.py:259-324`](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/config.py#L259-324)**

```python
 259 |     def _export_data(self, include_secrets: bool) -> dict:
 260 |         """Prepare an export without altering this in-memory configuration.
 261 | 
 262 |         A default export omits proxy authentication and redacts sensitive
 263 |         headers. The loaded default export requires the user to provide
 264 |         secrets again; use include_secrets=True only for private backups.
 265 |         """
 266 |         data = self.model_dump(mode="json")
 267 |         if include_secrets:
 268 |             return data
 269 |         if data["proxy"] is not None:
 270 |             safe_server, _, _ = _split_proxy_credentials(data["proxy"]["server"])
 271 |             data["proxy"]["server"] = safe_server
 272 |             data["proxy"]["username"] = None
 273 |             data["proxy"]["password"] = None
 274 |         for name in list(data.get("extra_headers", {})):
 275 |             if name.lower() in {"authorization", "proxy-authorization", "cookie", "set-cookie", "x-api-key", "x-auth-token"}:
 276 |                 data["extra_headers"][name] = "***"
 277 |         return data
 278 | 
 279 |     @staticmethod
 280 |     def _write_private_export(path: str | Path, payload: str) -> None:
 281 |         """Write without exposing a world-readable intermediate file.
 282 | 
 283 |         Create an exclusive 0600 file beside the destination and replace it
 284 |         atomically. Windows NTFS ACL guarantees still require live validation.
 285 |         """
 286 |         import os
 287 |         import tempfile
 288 | 
 289 |         p = Path(path)
 290 |         tmp_path = None
 291 |         try:
 292 |             fd, name = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent))
 293 |             tmp_path = Path(name)
 294 |             try:
 295 |                 if hasattr(os, "fchmod"):
 296 |                     os.fchmod(fd, 0o600)
 297 |                 else:
 298 |                     os.chmod(tmp_path, 0o600)
 299 |                 with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
 300 |                     out.write(payload)
 301 |             except BaseException:
 302 |                 # fdopen owns fd if it was reached; avoid replacing a failed write.
 303 |                 try:
 304 |                     os.close(fd)
 305 |                 except OSError:
 306 |                     pass
 307 |                 raise
 308 |             os.replace(tmp_path, p)
 309 |         finally:
 310 |             if tmp_path is not None:
 311 |                 tmp_path.unlink(missing_ok=True)
 312 | 
 313 |     def save_json(self, path: str | Path, *, include_secrets: bool = False) -> None:
 314 |         """Atomically export JSON. Credentials are omitted by default.
 315 | 
 316 |         Pass include_secrets=True only for a private, access-controlled backup.
 317 |         On Windows, file ACL behavior must be verified separately.
 318 |         """
 319 |         data = self._export_data(include_secrets)
 320 |         self._write_private_export(path, json.dumps(data, indent=2, sort_keys=True) + "\n")
 321 | 
 322 |     @classmethod
 323 |     def load_json(cls, path: str | Path) -> "ProfileConfig":
 324 |         """Load and validate a :class:`ProfileConfig` from a JSON file.
```

**[Source: `stealth_engine/config.py:339-350`](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/config.py#L339-350)**

```python
 339 |     def save_yaml(self, path: str | Path, *, include_secrets: bool = False) -> None:
 340 |         """Atomically export YAML with proxy secrets redacted by default.
 341 | 
 342 |         Pass include_secrets=True only for a private, access-controlled backup.
 343 |         """
 344 |         import yaml
 345 | 
 346 |         self._write_private_export(
 347 |             path,
 348 |             yaml.safe_dump(self._export_data(include_secrets), sort_keys=True),
 349 |         )
 350 | 
```

**Target tests:** `P04ExportSafetyTests` (3 cases) — JSON/YAML safe defaults, opt-in secret backup, mode `0600` and failure atomicity; code refs [target tests](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/tests/test_forensic_regressions.py#L1375-1421). **Compatibility release blocker**: 2 legacy tests fail; `tests/test_feature_p_y.py` was left unchanged by strict approval. No encrypted backup feature was introduced.

## F-13 — Unsupported mobile preset removed from public selectable names

**Observed code behavior:** `ProfileConfig.os` only supports `windows`, `macos`, `linux`. The invalid `mobile-android` preset was removed rather than silently claiming a desktop fingerprint is Android. Remaining public presets validate; requesting the old name raises the existing typed `ConfigError`. **Breaking preset-name compatibility change documented**; native Android fingerprinting is not implemented.

**[Source: `stealth_engine/config.py:385-418`](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/config.py#L385-418)**

```python
 385 |         "headless": True,
 386 |     },
 387 |     "eu-desktop": {
 388 |         "os": "windows",
 389 |         "locale": "de-DE",
 390 |         "timezone": "Europe/Berlin",
 391 |         "headless": True,
 392 |     },
 393 |     # "mobile-android" deliberately removed: Camoufox ProfileConfig
 394 |     # supports only windows/macos/linux. Do not falsely label a desktop
 395 |     # fingerprint as Android; unknown name raises ConfigError below.
 396 | }
 397 | 
 398 | 
 399 | def preset_names() -> list[str]:
 400 |     """Return the names of all built-in profile presets (PH-18)."""
 401 |     return sorted(_PROFILE_PRESETS)
 402 | 
 403 | 
 404 | # Attach the classmethod without cluttering the class body.
 405 | def _preset_classmethod(cls: type, name: str, **overrides: Any) -> "ProfileConfig":
 406 |     """Build a ``ProfileConfig`` from a named preset merged with overrides."""
 407 |     if name not in _PROFILE_PRESETS:
 408 |         from .exceptions import ConfigError
 409 | 
 410 |         raise ConfigError(
 411 |             f"unknown profile preset: {name!r}",
 412 |             details={"stage": "preset", "preset": name, "available": preset_names()},
 413 |         )
 414 |     merged = {**_PROFILE_PRESETS[name], **overrides}
 415 |     return cls.model_validate(merged)
 416 | 
 417 | 
 418 | ProfileConfig.preset = classmethod(_preset_classmethod)  # type: ignore[attr-defined]
```

**Target test:** `P04PresetTests.test_f13_all_public_presets_validate_without_android_claim` (pass) and existing `PresetTests` (pass). No new OS spoofing implementation.

## F-19 — Per-profile engine logging (scoped, other module-global records unfiltered)

**Observed code behavior:** `ProfileLogger` wraps an independently bound loguru logger with local severity threshold, with profile tag and per-profile password scrub. `StealthEngine.__init__` creates one logger from `config.log_level`; `StealthEngine.alaunch` uses it for the launch-success record. **No global loguru handler is added/removed**, and unrelated profile levels do not mutate each other. Legacy module-level `_log` in emergency cleanup, session close, proxy, identity and other modules still uses existing global sinks and **is NOT fully controlled by `profile.log_level`**. Those sites were intentionally left untouched to preserve P-01/P-02/P-03 implementations. Hence F-19 is **partially addressed, not fully closed** under present Scope Lock.

**[Source: `stealth_engine/utils/logging.py:50-103`](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/utils/logging.py#L50-103)**

```python
  50 | 
  51 | 
  52 | # Profile-scoped records never alter the process-global loguru handlers.
  53 | # Engine-owned records can be filtered independently even when two profiles
  54 | # coexist in the same interpreter. Third-party and legacy module-level
  55 | # records are intentionally outside this scoped logger's control.
  56 | _PROFILE_LEVELS = {"TRACE": 5, "DEBUG": 10, "INFO": 20, "SUCCESS": 25,
  57 |                    "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
  58 | 
  59 | 
  60 | class ProfileLogger:
  61 |     """Local severity gate for records *emitted through this instance*."""
  62 | 
  63 |     def __init__(self, name: str, profile: str, level: str, secrets: tuple[str, ...] = ()) -> None:
  64 |         canonical = level.upper()
  65 |         if canonical not in _PROFILE_LEVELS:
  66 |             raise ValueError(f"unsupported profile log_level: {level!r}")
  67 |         self._limit = _PROFILE_LEVELS[canonical]
  68 |         self._bound = logger.bind(module=name, profile=profile)
  69 |         self._secrets = tuple(value for value in secrets if value and value != "***")
  70 | 
  71 |     def log(self, severity: str, message: str, *args, **kwargs) -> None:
  72 |         canonical = severity.upper()
  73 |         if _PROFILE_LEVELS[canonical] < self._limit:
  74 |             return
  75 |         # Only scrub *this* profile's values; do not globally mutate logs.
  76 |         for secret in self._secrets:
  77 |             message = message.replace(secret, "***")
  78 |         args = tuple(self._scrub(arg) for arg in args)
  79 |         kwargs = {key: self._scrub(value) for key, value in kwargs.items()}
  80 |         self._bound.log(canonical, message, *args, **kwargs)
  81 | 
  82 |     def _scrub(self, value):
  83 |         if isinstance(value, str):
  84 |             for secret in self._secrets:
  85 |                 value = value.replace(secret, "***")
  86 |         return value
  87 | 
  88 |     def debug(self, message: str, *args, **kwargs):
  89 |         self.log("DEBUG", message, *args, **kwargs)
  90 | 
  91 |     def info(self, message: str, *args, **kwargs):
  92 |         self.log("INFO", message, *args, **kwargs)
  93 | 
  94 |     def warning(self, message: str, *args, **kwargs):
  95 |         self.log("WARNING", message, *args, **kwargs)
  96 | 
  97 |     def error(self, message: str, *args, **kwargs):
  98 |         self.log("ERROR", message, *args, **kwargs)
  99 | 
 100 | 
 101 | def get_profile_logger(name: str, profile: str, level: str, *, secrets: tuple[str, ...] = ()) -> ProfileLogger:
 102 |     """Create a profile-local severity gate without reconfiguring loguru."""
 103 |     return ProfileLogger(name, profile, level, secrets)
```

**[Source: `stealth_engine/engine.py:202-218`](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/engine.py#L202-218)**

```python
 202 |                 :class:`~stealth_engine.identity.IdentityProvider`.
 203 |                 ``None`` uses the default browserforge-backed provider.
 204 |         """
 205 |         self._config: ProfileConfig = config
 206 |         # A profile-local severity gate affects only engine-owned log records;
 207 |         # it does not reconfigure global loguru handlers for other profiles.
 208 |         secret_values: list[str] = []
 209 |         if config.proxy is not None:
 210 |             from .config import _split_proxy_credentials
 211 |             _, embedded_user, embedded_password = _split_proxy_credentials(config.proxy.server)
 212 |             secret_values.extend(v for v in (embedded_password, config.proxy.password) if v)
 213 |         self._profile_log = get_profile_logger(
 214 |             __name__, config.profile_name, config.log_level, secrets=tuple(secret_values)
 215 |         )
 216 |         _base = self._derive_base_dir(config)
 217 |         self._session: SessionManager = SessionManager(
 218 |             config, base_dir=_base
```

**[Source: `stealth_engine/engine.py:457-471`](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/engine.py#L457-471)**

```python
 457 | 
 458 |             # B-011: mask any credentials embedded in the server URL before logging.
 459 |             _proxy_log: str | None = None
 460 |             if proxy_cfg is not None:
 461 |                 import re as _re
 462 |                 _proxy_log = _re.sub(r"//[^@]*@", "//***@", proxy_cfg.server)
 463 |             self._profile_log.info(
 464 |                 "stealth session launched",
 465 |                 profile=cfg.profile_name,
 466 |                 headless=cfg.headless,
 467 |                 proxy=_proxy_log,
 468 |                 fp_hash=self._identity.fingerprint_hash()[:12],
 469 |             )
 470 |             return session_obj
 471 | 
```

**Target tests:** `P04ProfileLoggingTests` verifies two scoped logger instances, independent thresholds, one engine-bound profile logger and password scrubbing. This is **not proof of global per-profile filtering**. Follow-up requires explicit scope revision before touching legacy P-01 lifecycle or unrelated module-level log statements.

## Patch forensic diff & current acceptance

- Before/after AST audit: `identity.py`: only `IdentityGenerator.generate` docstring and `get_or_create_seeds`; `config.py`: export helper + JSON/YAML exporters and `_PROFILE_PRESETS` entry; `utils/logging.py`: additive profile logger; `engine.py`: only `StealthEngine.__init__` logger setup, `alaunch` **one launch-log call**, and `StealthEngine._build_launch_kwargs` hardware-concurrency mapping; regression tests additive P-04 class methods. Existing P-01/P-02/P-03 lifecycle/lock/transport/GeoIP/WebRTC logic not changed.
- Full browser dependency installed? **NO** (`browserforge`, `camoufox` and `tzlocal` absent), fake import stubs used only for offline tests. Windows binary, Windows ACL behavior, persistent Playwright browser, Camoufox fingerprint readback, actual full per-profile log filtering **NOT RUN / NOT VERIFIED**.
- **Known failures:** 2 legacy Feature Y default-secret round-trip test cases; both reflect a deliberate breaking secure-export contract. Do not mark all tests green. `include_secrets=True` explicit backup tests pass.
- P-04 STATUS: **SOURCE PATCH APPLIED; 61/61 FOCUSED OFFLINE PASS; 2 LEGACY TEST FAILURES; F-03 live parity and F-19 other logger paths UNVERIFIED; FULL RELEASE GATE BLOCKED**. Frozen initial baseline remains intact.
- P-05 requires separate approval; F-16/F-17 remain untouched. U-02/U-03/U-06 conditional, U-05 conditional unchanged.
