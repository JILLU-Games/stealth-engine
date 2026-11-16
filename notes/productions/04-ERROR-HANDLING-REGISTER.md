# 04 — Actual Error Handling Inventory & Future Safety Gates

> **Status: HISTORICAL BASELINE INVENTORY + P-01–P-05 VERIFIED PATCH DELTAS; all historical baseline handler counts retained as historical only.** Full suite 8 failures; production acceptance blocked.
> **Immutable source baseline:** [`a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`](https://gitlab.com/ivibtools/stealth-engine/-/commit/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5); prior source audit revision [`6255383cac9f29d64bf9ee5957c77ee26ccd7993`](https://gitlab.com/ivibtools/stealth-engine/-/commit/6255383cac9f29d64bf9ee5957c77ee26ccd7993). The 31 audited executable/config blob hashes match across these revisions.


## P-04 error-handling and compatibility delta — current source (2026-11-16)

| Error/contract category | Current code behavior and source | Proof and caveat |
|---|---|---|
| F-04 seed update failure | `IdentityGenerator.get_or_create_seeds` now atomically updates loaded valid seed metadata, catches `OSError`, removes temporary file if possible and raises `IdentityError`; numeric seeds unchanged | [https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/identity.py#L484-541](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/identity.py#L484-541); local fault-injection PASS, Windows unverified |
| F-10 default secret export | Sanitizes proxy credentials/header names; exclusive `mkstemp` private file, `os.replace`, finally temp cleanup; explicit `include_secrets=True` overrides redaction | [https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/config.py#L259-350](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/config.py#L259-350); 3 tests PASS; 2 legacy plaintext assertions FAIL, Windows ACL unverified |
| F-13 unsupported mobile preset | `preset_names()` excludes invalid `mobile-android`, request returns existing `ConfigError` | [https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/config.py#L388-418](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/config.py#L388-418); desktop presets PASS; compatibility change |
| F-19 profile logging | New per-instance severity gate refuses low-severity scoped records, scrubs known proxy passwords and binds profile metadata | [https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/utils/logging.py#L50-103](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/utils/logging.py#L50-103); 2-profile PASS, **legacy module-global logs remain unfiltered** |
| F-03 fingerprint mapping | `hardwareConcurrency` valid generated/explicit key reaches Camoufox config, other advisory values not forwarded; unsupported claims documented | [https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/engine.py#L784-798](https://gitlab.com/ivibtools/stealth-engine/-/blob/997e5dd5087d4e366dc573f561e2e9ac3a063520/stealth_engine/engine.py#L784-798); fake launch kwargs PASS; real parity NOT VERIFIED |

**Known blockers:** old default JSON/YAML round-trip expectations (`tests/test_feature_p_y.py`) intentionally fail; no off-scope test edit made. Camoufox/browserforge runtime, Windows, full profile-scope log filtering remain not verified. See [P-04 proof](09-P04-VERIFICATION-EVIDENCE.md). Historical baseline handler-count table below remains unchanged.

## P-03 source patch status overlay — 2026-11-16 (current, not baseline)

| Error category / finding | Implemented code behavior | Verification status | Current source |
|---|---|---|---|
| SOCKS handshake/transport F-05 | Correct SOCKS5 with RFC1929 user/pass, SOCKS4a remote-name TCP CONNECT; typed `ProxyError` for rejection, HTTP error/invalid response, bounded payload; HTTP proxy continues via aiohttp | Local in-process SOCKS peer PASS; HTTPS/real proxy/Windows **UNVERIFIED** | [`proxy.py:324-348`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/proxy.py#L324-348), [`proxy.py:568-678`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/proxy.py#L568-678) |
| Secret-bearing invalid proxy F-11 | Sanitized `ProxyError` with no `content`/raw credentials and `from None` for invalid `ProxyConfig`; Pydantic validation errors hide the raw value | Offline malicious input fixtures PASS; unknown downstream logging not certified | [`proxy.py:768-815`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/proxy.py#L768-815) |
| Missing authority/port F-12 | Validator rejects missing host, missing/zero/invalid port, path/query; error string avoids raw URL | Table-driven offline validation PASS | [`config.py:41-78`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/config.py#L41-78) |
| Geo `auto` F-14 | Compares resolved effective GeoInfo value, preserving explicit config mismatch detection | Offline Geo fixtures PASS | [`geo.py:130-150`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/geo.py#L130-150) |
| WebRTC public hint F-15 | Rejects private/invalid explicit target IP with `LaunchError`; omits locally guessed non-global hint, emits only globally routed IPv4 | Offline kwargs tests PASS; actual Camoufox WebRTC ICE candidates **UNVERIFIED** | [`engine.py:706-733`](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/engine.py#L706-733) |

See [08-P03-VERIFICATION-EVIDENCE.md](08-P03-VERIFICATION-EVIDENCE.md). Historical headings/blocks below remain snapshots of the immutable pre-fix baseline. Release remains blocked pending external egress, TLS, Windows, real-browser observations and pending P-01/P-02 gates. U-05 remains conditionally unsupported at engine integration level.

## P-02 current error-handling overlay (2026-11-16; historical baseline snippets below remain frozen)

- **New typed `SessionError` failure paths:** [`SessionManager._profile_lock_guard`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L232-264) returns a typed error if the interprocess guard cannot be acquired; [`_read_lock_owner`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L265-288) fails closed on invalid lock JSON/PID/token; [`acquire_lock`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L289-339) rejects another live owner and unsafe re-entry; [`release_lock`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L340-366) refuses PID/token mismatch; [`force_reset`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L368-407) forbids active/unknown owner and surfaces filesystem reset failure.
- **Age metadata handling:** [`StealthEngine._record_fingerprint`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/engine.py#L485-551) keeps the existing warn-and-return-false behavior on JSON/disk errors, now refuses corrupt legacy lists or invalid sidecar instead of overwriting; first migration writes a one-time backup and atomic sidecar. [`BrowserSession.session_age_days`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/engine.py#L1674-1705) returns `None` for invalid sidecar rather than an unproven age.
- **P-02 exception contract:** malformed `.lock`/unknown PID -> do not delete; live lock -> `SessionError`, no data loss; non-owner release -> no-op; token mismatch -> `SessionError`; idle `force_reset` -> directory removed, guard file remains. Exact test code references in [07](07-P02-VERIFICATION-EVIDENCE.md).
- **Limitations:** Linux offline filesystem/process safety only, Windows guard and mixed-version clients not executed. On-disk guard files persist, and already-truncated legacy histories cannot recover missing first launch time. Original baseline AST handler counts below describe the baseline **only**, not the post-P02 counts.

## Evidence methodology

All tracked `stealth_engine/**/*.py` files were parsed directly using Python AST at baseline. Counts are **syntactic statement/handler counts**, not number of unique functional errors or proof that they trigger. Representative exact source blocks below show the active policies. Any *recommended* handling is a future acceptance requirement, **not current functionality**.

| Runtime module | `except` handlers | Explicit `raise` statements | `try ... finally` blocks |
|---|---:|---:|---:|
| [`stealth_engine/__init__.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/__init__.py) | 0 | 1 | 0 |
| [`stealth_engine/behavior.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/behavior.py) | 3 | 0 | 0 |
| [`stealth_engine/config.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py) | 0 | 6 | 0 |
| [`stealth_engine/engine.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py) | 39 | 34 | 2 |
| [`stealth_engine/exceptions.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/exceptions.py) | 0 | 0 | 0 |
| [`stealth_engine/geo.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/geo.py) | 9 | 8 | 0 |
| [`stealth_engine/identity.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/identity.py) | 12 | 12 | 0 |
| [`stealth_engine/orchestrator.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/orchestrator.py) | 5 | 11 | 2 |
| [`stealth_engine/proxy.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/proxy.py) | 12 | 22 | 0 |
| [`stealth_engine/risk.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/risk.py) | 0 | 0 | 0 |
| [`stealth_engine/session.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/session.py) | 17 | 13 | 1 |
| [`stealth_engine/utils/__init__.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/utils/__init__.py) | 0 | 0 | 0 |
| [`stealth_engine/utils/logging.py`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/utils/logging.py) | 0 | 0 | 0 |
| **Total** | **97** | **107** | **5** |

## Existing typed error model — current source proof

**[Source: `stealth_engine/exceptions.py:6-27`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/exceptions.py#L6-27)**

```python
   6 | class StealthEngineError(Exception):
   7 |     """Base exception for all stealth_engine errors.
   8 | 
   9 |     Args:
  10 |         message: Human-readable description of the error.
  11 |         details: Optional mapping of additional diagnostic context.
  12 |     """
  13 | 
  14 |     def __init__(
  15 |         self,
  16 |         message: str = "An unexpected stealth engine error occurred.",
  17 |         details: dict | None = None,
  18 |     ) -> None:
  19 |         super().__init__(message)
  20 |         self.message: str = message
  21 |         self.details: dict | None = details
  22 | 
  23 |     def __str__(self) -> str:
  24 |         """Return message with compact details repr when present."""
  25 |         if self.details:
  26 |             return f"{self.message} | details={self.details!r}"
  27 |         return self.message
```
**[Source: `stealth_engine/exceptions.py:29-71`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/exceptions.py#L29-71)**

```python
  29 | 
  30 | class ConfigError(StealthEngineError):
  31 |     """Raised when profile or proxy configuration is invalid.
  32 | 
  33 |     Args:
  34 |         message: Human-readable description of the configuration error.
  35 |         details: Optional mapping of additional diagnostic context.
  36 |     """
  37 | 
  38 | 
  39 | class IdentityError(StealthEngineError):
  40 |     """Raised when fingerprint or identity generation fails.
  41 | 
  42 |     Args:
  43 |         message: Human-readable description of the identity error.
  44 |         details: Optional mapping of additional diagnostic context.
  45 |     """
  46 | 
  47 | 
  48 | class ProxyError(StealthEngineError):
  49 |     """Raised when proxy validation, health check, or rotation fails.
  50 | 
  51 |     Args:
  52 |         message: Human-readable description of the proxy error.
  53 |         details: Optional mapping of additional diagnostic context.
  54 |     """
  55 | 
  56 | 
  57 | class SessionError(StealthEngineError):
  58 |     """Raised when session creation, restoration, or export fails.
  59 | 
  60 |     Args:
  61 |         message: Human-readable description of the session error.
  62 |         details: Optional mapping of additional diagnostic context.
  63 |     """
  64 | 
  65 | 
  66 | class LaunchError(StealthEngineError):
  67 |     """Raised when the browser engine fails to launch or initialize.
  68 | 
  69 |     Args:
  70 |         message: Human-readable description of the launch error.
  71 |         details: Optional mapping of additional diagnostic context.
```
The actual typed exceptions are `StealthEngineError`, `ConfigError`, `IdentityError`, `ProxyError`, `SessionError`, `LaunchError`, `AutomationError`; Pydantic validation and standard OS/asyncio errors also occur. `StealthEngineError.__str__` includes **details**, so adding raw credentials to `details` can expose them (F-11).

## Existing operational handling paths (confirmed source branches)

### Config validation: reject unknown proxy scheme / invalid profile

**Current gap / follow-up:** F-12: host/authority not validated.

**[Source: `stealth_engine/config.py:38-62`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L38-62)**

```python
  38 |     @field_validator("server")
  39 |     @classmethod
  40 |     def _validate_server(cls, v: str) -> str:
  41 |         """Ensure server URL uses an accepted scheme.
  42 | 
  43 |         Args:
  44 |             v: Raw server string.
  45 | 
  46 |         Returns:
  47 |             Validated server string.
  48 | 
  49 |         Raises:
  50 |             ValueError: If the scheme is not one of the accepted proxy schemes.
  51 |         """
  52 |         accepted = ("http://", "https://", "socks5://", "socks5h://", "socks4://")
  53 |         if not any(v.startswith(scheme) for scheme in accepted):
  54 |             raise ValueError(
  55 |                 f"proxy server must start with one of {accepted}; got {v!r}"
  56 |             )
  57 |         # socks5h is a curl-style alias meaning "DNS through the proxy".
  58 |         # Playwright/aiohttp only understand socks5:// — normalise so
  59 |         # downstream consumers never see the alias.
  60 |         if v.startswith("socks5h://"):
  61 |             return "socks5://" + v[len("socks5h://"):]
  62 |         return v
```

### Identity provider failure mapped to typed IdentityError

**Current gap / follow-up:** P-04: preserve typed failure and safe cause.

**[Source: `stealth_engine/identity.py:183-199`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/identity.py#L183-199)**

```python
 183 |         try:
 184 |             gen = FingerprintGenerator(os=os_name)
 185 |             raw = gen.generate(os=os_name)
 186 |         except Exception as exc:
 187 |             raise IdentityError(
 188 |                 "browserforge fingerprint generation failed",
 189 |                 details={"stage": "generate", "reason": str(exc)},
 190 |             ) from exc
 191 | 
 192 |         try:
 193 |             return self._extract(raw, os_name, rng)
 194 |         except IdentityError:
 195 |             raise
 196 |         except Exception as exc:
 197 |             raise IdentityError(
 198 |                 "fingerprint extraction failed",
 199 |                 details={"stage": "extract", "reason": str(exc)},
```

### Persisted seeds: unreadable JSON recovered with warning

**Current gap / follow-up:** F-04: persisted valid-but-stale locale precedence.

**[Source: `stealth_engine/identity.py:486-503`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/identity.py#L486-503)**

```python
 486 |         seeds_path = _profile_root(self._config) / "seeds.json"
 487 | 
 488 |         if seeds_path.exists():
 489 |             try:
 490 |                 loaded = json.loads(seeds_path.read_text(encoding="utf-8"))
 491 |             except (json.JSONDecodeError, OSError) as exc:
 492 |                 _log.warning(
 493 |                     "Corrupt seeds.json at {} — regenerating: {}",
 494 |                     seeds_path,
 495 |                     exc,
 496 |                 )
 497 |             else:
 498 |                 if _valid_seed_dict(loaded):
 499 |                     return loaded
 500 |                 _log.warning(
 501 |                     "seeds.json at {} missing required keys or has wrong "
 502 |                     "types — regenerating",
 503 |                     seeds_path,
```

### Launch: preserve typed errors, wrap other stage errors

**Current gap / follow-up:** F-06: proxy cleanup path incomplete; message may contain raw upstream exception.

**[Source: `stealth_engine/engine.py:415-424`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L415-424)**

```python
 415 |         except StealthEngineError:
 416 |             # Preserve typed sub-exceptions from sub-modules unchanged.
 417 |             await self._emergency_cleanup(ctx_handle, session)
 418 |             raise
 419 |         except Exception as exc:
 420 |             await self._emergency_cleanup(ctx_handle, session)
 421 |             raise LaunchError(
 422 |                 f"camoufox launch failed at stage={stage!r}: {exc}",
 423 |                 details={"stage": stage, "reason": str(exc)},
 424 |             ) from exc
```

### Emergency cleanup: best effort context + lock

**Current gap / follow-up:** F-06: proxy manager not closed.

**[Source: `stealth_engine/engine.py:738-746`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L738-746)**

```python
 738 |         if ctx_handle is not None:
 739 |             try:
 740 |                 await ctx_handle.__aexit__(None, None, None)
 741 |             except Exception as exc:
 742 |                 _log.warning("emergency cleanup: camoufox close failed", reason=str(exc))
 743 |         try:
 744 |             session.release_lock()
 745 |         except Exception as exc:
 746 |             _log.warning("emergency cleanup: release_lock failed", reason=str(exc))
```

### Session: concurrent owner lock handling

**Current gap / follow-up:** F-07: live PID lock can be stolen after timeout.

**[Source: `stealth_engine/session.py:275-305`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/session.py#L275-305)**

```python
 275 |         # Lock file exists — inspect for staleness.
 276 |         stale = False
 277 |         try:
 278 |             existing = json.loads(lock.read_text(encoding="utf-8"))
 279 |             pid: int = int(existing.get("pid", -1))
 280 |             ts: float = float(existing.get("ts", 0.0))
 281 |             age = time.time() - ts
 282 |             if not _pid_alive(pid) or age > _LOCK_MAX_AGE_S:
 283 |                 stale = True
 284 |         except (OSError, ValueError, KeyError):
 285 |             # Unreadable / malformed lock → treat as stale.
 286 |             stale = True
 287 | 
 288 |         if not stale:
 289 |             raise SessionError(
 290 |                 "profile is locked by another process",
 291 |                 details={"stage": "acquire_lock", "lock": str(lock)},
 292 |             )
 293 | 
 294 |         _log.warning(
 295 |             "removing stale lock",
 296 |             profile=self._config.profile_name,
 297 |             lock=str(lock),
 298 |         )
 299 |         try:
 300 |             lock.unlink(missing_ok=True)
 301 |         except OSError:
 302 |             pass
 303 | 
 304 |         # --- Single non-recursive retry (retry=False prevents further looping) ---
 305 |         self._try_acquire_lock(retry=False)
```

### Session: best-effort lock release / reset

**Current gap / follow-up:** F-08/F-09: ownership and safe deletion missing.

**[Source: `stealth_engine/session.py:307-336`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/session.py#L307-336)**

```python
 307 |     def release_lock(self) -> None:
 308 |         """Remove the PID lock file if it exists.
 309 | 
 310 |         Idempotent — does not raise if the lock file is already gone.
 311 |         """
 312 |         try:
 313 |             self._lock_path.unlink(missing_ok=True)
 314 |             _log.debug("lock released", profile=self._config.profile_name)
 315 |         except OSError:
 316 |             # Best-effort; swallow errors silently.
 317 |             pass
 318 | 
 319 |     # ------------------------------------------------------------------
 320 |     # Profile reset
 321 |     # ------------------------------------------------------------------
 322 | 
 323 |     def force_reset(self) -> None:
 324 |         """Delete the entire profile directory after releasing the lock.
 325 | 
 326 |         Logs a ``WARNING`` before deletion.  Does not raise if the
 327 |         directory does not exist.
 328 |         """
 329 |         self.release_lock()
 330 |         if self._profile_dir.exists():
 331 |             _log.warning(
 332 |                 "force_reset: deleting profile directory",
 333 |                 profile=self._config.profile_name,
 334 |                 path=str(self._profile_dir),
 335 |             )
 336 |             shutil.rmtree(self._profile_dir, ignore_errors=True)
```

### Proxy: health check via aiohttp and retries

**Current gap / follow-up:** F-05: SOCKS transport not proven / wrong wire protocol.

**[Source: `stealth_engine/proxy.py:326-337`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/proxy.py#L326-337)**

```python
 326 |         data: dict[str, Any] | None = None
 327 |         last_exc: ProxyError | None = None
 328 |         for attempt in range(self._geo_retries + 1):
 329 |             try:
 330 |                 async with session.get(
 331 |                     self._geo_endpoint,
 332 |                     proxy=proxy_url,
 333 |                     proxy_auth=proxy_auth,
 334 |                     timeout=timeout,
 335 |                 ) as resp:
 336 |                     if resp.status != 200:
 337 |                         raise ProxyError(
```

### Proxy parser: detailed error generation

**Current gap / follow-up:** F-11: raw input in error details.

**[Source: `stealth_engine/proxy.py:643-655`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/proxy.py#L643-655)**

```python
 643 |     def _err(msg: str) -> ProxyError:
 644 |         return ProxyError(
 645 |             f"proxy file line {lineno}: {msg}",
 646 |             details={"stage": "load_proxies", "line": lineno, "content": line[:80]},
 647 |         )
 648 | 
 649 |     line = line.strip()
 650 |     if "://" in line:
 651 |         # scheme://[user:pass@]host:port
 652 |         try:
 653 |             return ProxyConfig(server=line)
 654 |         except Exception as exc:
 655 |             raise _err(f"invalid URL proxy: {exc}") from exc
```

### Geo resolver: retry after provider failures

**Current gap / follow-up:** External API behavior not live-tested.

**[Source: `stealth_engine/geo.py:411-432`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/geo.py#L411-432)**

```python
 411 |             except ProxyError as exc:
 412 |                 last_exc = exc
 413 |                 errors.append({"url": url, "error": str(exc)})
 414 |                 _log.debug("geo endpoint failed, trying next", url=url, error=str(exc))
 415 |             except asyncio.TimeoutError:
 416 |                 last_exc = ProxyError(
 417 |                     "geo endpoint timed out",
 418 |                     details={"stage": stage, "url": url},
 419 |                 )
 420 |                 errors.append({"url": url, "error": "timeout"})
 421 |             except aiohttp.ClientError as exc:
 422 |                 last_exc = ProxyError(
 423 |                     "geo endpoint connection error",
 424 |                     details={"stage": stage, "url": url, "reason": str(exc)},
 425 |                 )
 426 |                 errors.append({"url": url, "error": str(exc)})
 427 | 
 428 |         assert last_exc is not None
 429 |         last_exc.details["attempts"] = errors
 430 |         if masked:
 431 |             last_exc.details.update(masked)
 432 |         raise last_exc
```

### Orchestrator: non-retryable failure / cancellation / retries

**Current gap / follow-up:** U-06: timeout does not include launch/teardown.

**[Source: `stealth_engine/orchestrator.py:404-443`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/orchestrator.py#L404-443)**

```python
 404 |             except _NON_RETRYABLE as exc:
 405 |                 # SessionError (locked) or IdentityError — not worth retrying.
 406 |                 duration_ms = round((time.perf_counter() - wall_start) * 1000.0, 2)
 407 |                 _log.warning(
 408 |                     "profile skipped (non-retryable)",
 409 |                     profile=profile.profile_name,
 410 |                     reason=str(exc),
 411 |                 )
 412 |                 return ProfileResult(
 413 |                     profile_name=profile.profile_name,
 414 |                     status=ProfileStatus.SKIPPED,
 415 |                     attempts=attempts,
 416 |                     duration_ms=duration_ms,
 417 |                     error=str(exc),
 418 |                 )
 419 | 
 420 |             except asyncio.CancelledError:
 421 |                 # Propagate cancellation immediately — do not swallow.
 422 |                 raise
 423 | 
 424 |             except Exception as exc:
 425 |                 last_error = str(exc) or type(exc).__name__
 426 |                 _log.warning(
 427 |                     "profile attempt failed",
 428 |                     profile=profile.profile_name,
 429 |                     attempt=attempt,
 430 |                     max_attempts=self._max_attempts,
 431 |                     error=last_error,
 432 |                 )
 433 | 
 434 |             finally:
 435 |                 if session is not None:
 436 |                     try:
 437 |                         await session.aclose()
 438 |                     except Exception as close_exc:
 439 |                         _log.warning(
 440 |                             "session.aclose() failed during cleanup",
 441 |                             profile=profile.profile_name,
 442 |                             reason=str(close_exc),
 443 |                         )
```

### BrowserSession: close failures logged with warnings

**Current gap / follow-up:** Close failure is not rethrown; requires release gate cleanup observation.

**[Source: `stealth_engine/engine.py:993-1016`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L993-1016)**

```python
 993 |         try:
 994 |             await self.save_state_async()
 995 |         except Exception as exc:
 996 |             _log.warning("aclose: save_state_async failed", reason=str(exc))
 997 | 
 998 |         try:
 999 |             await self._ctx.close()
1000 |         except Exception as exc:
1001 |             _log.warning("aclose: context.close() failed", reason=str(exc))
1002 | 
1003 |         try:
1004 |             await self._ctx_handle.__aexit__(None, None, None)
1005 |         except Exception as exc:
1006 |             _log.warning("aclose: ctx_handle.__aexit__ failed", reason=str(exc))
1007 | 
1008 |         self._session.release_lock()
1009 | 
1010 |         if self._proxy_manager is not None:
1011 |             try:
1012 |                 await self._proxy_manager.aclose()
1013 |             except Exception as exc:
1014 |                 _log.warning("aclose: proxy_manager.aclose() failed", reason=str(exc))
1015 | 
1016 |         _log.info("session closed", profile=self._config.profile_name)
```

### Unsupported video recording proactively rejected

**Current gap / follow-up:** U-02: not working video feature, intentional.

**[Source: `stealth_engine/engine.py:676-687`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L676-687)**

```python
 676 |         if cfg.record_har_content:
 677 |             kwargs["record_har_content"] = cfg.record_har_content
 678 |         if cfg.record_video_dir:
 679 |             raise AutomationError(
 680 |                 "record_video_dir is unsupported on camoufox/Firefox "
 681 |                 "(Playwright video recording is Chromium-only); use "
 682 |                 "record_har_path for session capture",
 683 |                 details={
 684 |                     "stage": "launch_options",
 685 |                     "reason": "video recording unsupported on Firefox",
 686 |                 },
 687 |             )
```

## Proposed error-handling additions (NOT IMPLEMENTED)

| Future work | Finding / phase | Required guard & acceptance |
|---|---|---|
| Async loop lifecycle mismatch | F-01 / P-01 | Typed actionable error before allocation or managed loop, no loop-closed resources |
| Initial empty context coroutine | F-02 / P-01 | Await page; surface typed error on failure, no coroutine retained |
| Failed-launch proxy cleanup | F-06 / P-01 | `finally` / best-effort teardown with original exception preserved; exact resource-close assertions |
| Ownership-sensitive lock/reset | F-07/08/09 / P-02 | PATCH APPLIED, Linux 35/35 focused PASS; Windows/multi-version pending — owner token/PID liveness, fail-closed `SessionError` |
| First-seen timestamp corruption | F-18 / P-02 | PATCH APPLIED, Linux offline PASS; immutable first_seen + legacy backup and invalid-meta warning |
| SOCKS validation & transport failure | F-05 / P-03 | Scheme-aware typed `ProxyError`, no false classification of healthy SOCKS |
| Credentials in exceptions | F-11/12 / P-03 | Redact input in all nested exception/details/HTTP logs; validate required authority |
| Geo resolver ambiguous sentinel | F-14 / P-03 | Deterministic validation for `auto` with safe handling of absent GeoInfo |
| WebRTC IP unavailable/private | F-15 / P-03 | No private IP claimed public; policy-specific fail-closed path / controlled test |
| Config export secrets / permissions | F-10 / P-04 | Safe default export, explicit user consent for sensitive export, restrictive temporary+final file handling |
| Invalid preset | F-13 / P-04 | Fast typed validation with valid alternatives; no invalid built-in presets |
| Fingerprint integration unsupported | F-03/04 / P-04 | Typed explicit unsupported-field behavior and stable identity precedence |
| Per-profile logger behavior | F-19 / P-04 | Predictable filtering, secure/redacted structured logs, no unrelated profile mutation |
| Canvas noise and route matcher | F-16/17 / P-05 | Deterministic behavior; parse host safely; error handling for malformed URLs |
| Unsupported API / bulk timeout | U-01..U-06 / owned phases | Deliberate `AutomationError` with truthful reason; no silent fallback or unsupported success claims |

## Universal error-policy acceptance (future)

1. On any failure, preserve `from exc` traceback internally while keeping diagnostic strings free from secrets and raw credentials.
2. Preserve `asyncio.CancelledError` propagation and reliable cleanup without retrying non-retryable profile lock and identity failures.
3. Make destructive operations ownership-safe, idempotent, and observable; no blanket `ignore_errors=True` on active-session destruction.
4. Distinguish `VALIDATION`, `DEPENDENCY MISSING`, `TRANSIENT NETWORK`, `AUTH/PROXY`, `SESSION OWNERSHIP`, `BROWSER UNSUPPORTED`, `TIMEOUT`, `CANCELLED` and `CLEANUP FAILURE` in tests; do not assert such categories are implemented yet.
5. Test no raw passwords/secrets in errors, audit records or UI (there is no UI implementation in this repo).

**Release warning:** AST counts do not establish correct error handling; 19 code findings remain OPEN until phases are verified. 

## P-01 error handling delta — code commit `9638c789` (2026-11-16)

- `StealthEngine.alaunch` now handles `asyncio.CancelledError` and routes it through emergency cleanup while re-raising; original `StealthEngineError` types are still preserved. Ordinary unexpected exceptions still become typed `LaunchError`.
- `_emergency_cleanup` now tries Camoufox handle exit, proxy manager `aclose`, then session lock release **independently**. Failure of proxy close logs a warning and does not replace the original `AutomationError` from initial page setup.
- `launch` no longer uses `asyncio.run(self.alaunch())`; it creates a live worker loop. `close` and external `aclose` dispatch cleanup to that owner, then stop/join the worker.
- **Actual evidence:** P-01 isolated tests: cancellation cleanup, initial-page failure, proxy close failure with preserved typed exception, sync loop stop, adjacent close save-state: **15 passed/0 failed** (Python 3.13, fake backend), commit [`9638c789c7b06def4b51a54583bd728ee42e746b`](https://gitlab.com/ivibtools/stealth-engine/-/commit/9638c789c7b06def4b51a54583bd728ee42e746b).
- **Boundary:** Real Camoufox, exception timing under real network IO, shutdown on Windows, concurrent cancellation and actual proxy sessions **NOT VERIFIED**. Baseline AST counts above intentionally not recalculated or misrepresented as post-patch counts.

**[Verified post-patch source: `stealth_engine/engine.py:461-475`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/stealth_engine/engine.py#L461-475)**

```python
 461 |         except asyncio.CancelledError:
 462 |             # Cancellation is BaseException on supported Python versions;
 463 |             # release browser/proxy resources before propagating it.
 464 |             await self._emergency_cleanup(ctx_handle, session, self._proxy_manager)
 465 |             raise
 466 |         except StealthEngineError:
 467 |             # Preserve typed sub-exceptions from sub-modules unchanged.
 468 |             await self._emergency_cleanup(ctx_handle, session, self._proxy_manager)
 469 |             raise
 470 |         except Exception as exc:
 471 |             await self._emergency_cleanup(ctx_handle, session, self._proxy_manager)
 472 |             raise LaunchError(
 473 |                 f"camoufox launch failed at stage={stage!r}: {exc}",
 474 |                 details={"stage": stage, "reason": str(exc)},
 475 |             ) from exc
```

**[Verified post-patch source: `stealth_engine/engine.py:791-804`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/stealth_engine/engine.py#L791-804)**

```python
 791 |         if ctx_handle is not None:
 792 |             try:
 793 |                 await ctx_handle.__aexit__(None, None, None)
 794 |             except Exception as exc:
 795 |                 _log.warning("emergency cleanup: camoufox close failed", reason=str(exc))
 796 |         if proxy_manager is not None:
 797 |             try:
 798 |                 await proxy_manager.aclose()
 799 |             except Exception as exc:
 800 |                 _log.warning("emergency cleanup: proxy close failed", reason=str(exc))
 801 |         try:
 802 |             session.release_lock()
 803 |         except Exception as exc:
 804 |             _log.warning("emergency cleanup: release_lock failed", reason=str(exc))
```


## P-05 exception/route-handling delta — current code

| Path / case | After P-05 behavior | Exact source/test reference | Current status |
|---|---|---|---|
| F-16 repeated canvas/WebGL readback | `_perturb` uses a fresh local PRNG seeded from `_seed` for each call. Existing `try`/fallback no-exception paths remain unchanged; no mutation to source canvas in `toDataURL` path. | [engine.py 87–129](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L87-129), [Node/mock tests](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/tests/test_forensic_regressions.py#L1462-1534) | PASS offline, **real Camoufox NOT VERIFIED**; experimental JS remains detectable |
| F-17 URL authority parsing | `urlsplit`/`.hostname` parse failure (`ValueError`) yields empty host and `route.continue_()`, preventing accidental tracker false positives. Hostname boundary matching uses exact host or subdomain only. | [engine.py 1689–1708](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L1689-1708), [mock route tests](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/tests/test_forensic_regressions.py#L1537-1584) | PASS offline; malformed URLs fail-open by design, not universal request validation |
| F-17 registration error | `self._ctx.route` errors still wrapped in existing `AutomationError`, stage `block_trackers`, with original error in details. | [engine.py 1710–1716](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L1710-1716) | PASS isolated failure injection |
| U-02/U-03/U-06 | Existing video option rejection, unsupported CDP mapping, and task-only timeout are unchanged, verified via 3 mock/source-contract tests. | [engine.py video](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L777-786), [CDP](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L1825-1857), [conditional tests](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/tests/test_forensic_regressions.py#L1587-1619) | Conditional/unsupported; not fixed or promoted to supported |

**Open blockers remain:** `tests/test_feature_p_y.py` 2 insecure-export legacy expectation failures, `tests/test_meta.py` 3 drift/history tests, missing `browserforge`/`camoufox` 3 stub failures, P-04 module-global log filtering, P-01–P-05 real browser/Windows/proxy, packaging. No out-of-scope code changes. See [10-P05-VERIFICATION-EVIDENCE.md](10-P05-VERIFICATION-EVIDENCE.md).
