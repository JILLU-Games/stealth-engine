# Production Acceptance Matrix — Actual vs Unverified (2026-11-16)

**Repository:** [`ivibtools/stealth-engine`](https://gitlab.com/ivibtools/stealth-engine)  
**Audited immutable GitLab commit:** `e3688ea6cab936b17b65f761fc2049bbeb50cad2` (`main` at audit start)  
**Audit date:** 2026-11-16 UTC  
**Permission / Scope:** read-only source analysis and isolated tests; **only `notes/productions/` audit Markdown may be committed**. No source change, bug fix, dependency installation, browser launch, external proxy, build, tag or release.  
**Provenance:** GitLab tree and source blob hash compared with isolated local checkout; 14 representative source/test/config blobs matched exactly. Line numbers below refer to the immutable SHA; prior P-01–P-05 evidence reports were inspected only as corroboration, never substituted for source.  


## Legend

- **SOURCE VERIFIED**: exact GitLab blob/line and code behavior inspected; not a real-browser pass.
- **OFFLINE PASS**: controlled tests or isolated probes ran without real Camoufox/Windows production setup.
- **BLOCKED**: the required evidence is absent or the gate is currently failing.
- **NOT APPLICABLE**: intentionally unsupported API; do not call it a working feature.

| Gate | Verified source/offline evidence | Remaining acceptance evidence | Status |
|---|---|---|---|
| G-01 P-01 lifecycle | Managed sync loop, await page, cleanup code; fake-context regression | Actual Camoufox/Playwright launch, close, crash cleanup | BLOCKED |
| G-02 P-02 profile ownership | owner token, live PID & guard, Linux tests | Windows msvcrt contention, crash/recovery, ACL and migration tests | BLOCKED |
| G-03 P-03 proxy | Local mock SOCKS4a/SOCKS5 wire tests, HTTP regression, safe parse | External authorized proxy egress, auth, TLS, DNS resolution and timeout behavior | BLOCKED |
| G-04 P-03 Geo/WebRTC | `auto` comparison and non-global IPv4 guard tests | Browser-visible public egress, DNS/WebRTC leak test behind NAT/proxy | BLOCKED |
| G-05 P-04 fingerprint | Supported launch kwarg mapping tests | Real browserforge & Camoufox fingerprint readback parity | BLOCKED |
| G-06 P-04 config | Redacted export + private permissions on Linux | 2 stale compatibility assertions, Windows NTFS ACL and documented restore behavior | BLOCKED |
| G-07 P-04 logging | Direct profile logger levels work; nested/global bypass reproduced | Complete per-profile log semantics and safe nested payload handling | BLOCKED |
| G-08 P-05 JS/tracker | 71 focused suite passes incl. Node-based JS readback tests | Live Firefox canvas/WebGL and request routing, JS-detection risk evidence | BLOCKED |
| G-09 Full suite | 235 pass, 8 fail, 4 skip with stub; 11 no-stub import errors | Green dependency-complete full suite, documented skips | BLOCKED |
| G-10 Python/Windows compatibility | AST source valid; tested Linux Python 3.13.5 | Declared Python matrix and Windows tests/install/lock/ACL semantics | BLOCKED |
| G-11 Packaging/build | Version parity: 0.3.0 in module + pyproject | Clean sdist/wheel build, isolated install/import, bundled browser prerequisites | BLOCKED |
| G-12 GitLab CI/release | Repo/file tree inspected; CI/tag/release/status API lists all empty | Automated test/build gates, artifacts, release provenance | BLOCKED |

## Core source-evidenced interfaces and conditions

### P-01: real browser absent

**Source:** [`stealth_engine/engine.py:L418-L428`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L418-428)

```python
 418 |             # Launch camoufox asynchronously.
 419 |             try:
 420 |                 from camoufox.async_api import AsyncCamoufox  # type: ignore[import]
 421 |             except ImportError as exc:
 422 |                 raise LaunchError(
 423 |                     "camoufox is not installed; run: pip install 'camoufox[geoip]'",
 424 |                     details={"stage": stage, "reason": str(exc)},
 425 |                 ) from exc
 426 | 
 427 |             ctx_handle = AsyncCamoufox(**launch_kwargs)
 428 |             playwright_ctx: PlaywrightBrowserContext = await ctx_handle.__aenter__()
```

No live test of the actual `AsyncCamoufox` context manager is recorded here. A controlled fake backend is not equivalent to Firefox launch.

### P-02: Windows behavior source-present, evidence missing

**Source:** [`stealth_engine/session.py:L239-L263`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/session.py#L239-263)

```python
 239 |         try:
 240 |             self._lock_guard_path.parent.mkdir(parents=True, exist_ok=True)
 241 |             fd = os.open(str(self._lock_guard_path), os.O_CREAT | os.O_RDWR, 0o600)
 242 |             with os.fdopen(fd, "r+b") as guard:
 243 |                 if guard.seek(0, os.SEEK_END) == 0:
 244 |                     guard.write(b"\0")
 245 |                     guard.flush()
 246 |                 guard.seek(0)
 247 |                 if os.name == "nt":
 248 |                     import msvcrt
 249 | 
 250 |                     msvcrt.locking(guard.fileno(), msvcrt.LK_LOCK, 1)
 251 |                 else:
 252 |                     import fcntl
 253 | 
 254 |                     fcntl.flock(guard.fileno(), fcntl.LOCK_EX)
 255 |                 try:
 256 |                     yield
 257 |                 finally:
 258 |                     if os.name == "nt":
 259 |                         guard.seek(0)
 260 |                         msvcrt.locking(guard.fileno(), msvcrt.LK_UNLCK, 1)
 261 |                     else:
 262 |                         fcntl.flock(guard.fileno(), fcntl.LOCK_UN)
 263 |         except OSError as exc:
```

No Windows-specific test executed in this audit. `os.name == 'nt'` is a source branch, not evidence it passed under NTFS or Windows concurrency.

### P-03: direct vs proxy WebRTC

**Source:** [`stealth_engine/engine.py:L720-L744`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L720-744)

```python
 720 |         # Proxy + GeoIP.
 721 |         if proxy_cfg is not None and self._proxy_manager is not None:
 722 |             kwargs["proxy"] = self._proxy_manager.to_playwright(proxy_cfg)
 723 |             kwargs["geoip"] = cfg.geoip
 724 |             # Mode B: WebRTC advertises proxy IP via geoip=True
 725 |         else:
 726 |             kwargs["geoip"] = False
 727 |             # Mode A: never advertise an interface/LAN address as the
 728 |             # external WebRTC egress. An explicit target must be public IPv4;
 729 |             # the best-effort local host lookup is used only if globally routed.
 730 |             candidate = cfg.target_ip if cfg.target_ip else self._resolve_host_ip()
 731 |             try:
 732 |                 public_ip = ipaddress.ip_address(candidate)
 733 |                 valid_public_v4 = public_ip.version == 4 and public_ip.is_global
 734 |             except ValueError:
 735 |                 valid_public_v4 = False
 736 |             if cfg.target_ip and not valid_public_v4:
 737 |                 raise LaunchError(
 738 |                     "target_ip must be a globally routable IPv4 address for WebRTC",
 739 |                     details={"stage": "launch_options", "reason": "invalid_public_target_ip"},
 740 |                 )
 741 |             if valid_public_v4:
 742 |                 launch_config["webrtc:ipv4"] = str(public_ip)
 743 |             else:
 744 |                 _log.warning("WebRTC public egress IP unverified; omitting manual IPv4 hint")
```

The direct host address resolution can return local/private interface addresses; source now refuses to advertise a non-global IPv4 hint. It **does not verify** that the actual network uses the user-specified public IPv4 or that a browser leaks no candidate IP. External network verification remains pending.

### P-04: scoped versus module-level logging

**Source:** [`stealth_engine/utils/logging.py:L60-L86`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/utils/logging.py#L60-86)

```python
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
```

Isolated proof: `ProfileLogger(level='ERROR').debug('...')` did **not** emit, but `get_logger('module').debug('...')` still emitted to an installed DEBUG sink. A synthetic secret in an extra nested dict persisted unsanitized. This is a **confirmed implementation boundary**, not a completed security acceptance.

### P-05: tracker and JS-only caveat

**Source:** [`stealth_engine/engine.py:L1691-L1709`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L1691-1709)

```python
1691 |         domains = list(_TRACKER_DOMAINS) + list(extra_domains or [])
1692 |         # F-17: normalize domain rules once; use label boundaries, not URL
1693 |         # substring matching (which also matches queries and lookalikes).
1694 |         blocked_hosts = tuple(
1695 |             domain.strip().lower().removeprefix("*.").strip(".")
1696 |             for domain in domains
1697 |             if isinstance(domain, str) and domain.strip(".* ")
1698 |         )
1699 | 
1700 |         async def _handler(route: Any, request: Any) -> None:
1701 |             try:
1702 |                 host = (urlsplit(request.url).hostname or "").lower().rstrip(".")
1703 |             except ValueError:  # Invalid URL authority must not become a tracker match.
1704 |                 host = ""
1705 |             if host and any(host == d or host.endswith("." + d) for d in blocked_hosts):
1706 |                 await route.abort()
1707 |             else:
1708 |                 await route.continue_()
1709 | 
```

No real URL routing against a live server/browser is evidenced; the tests exercise fake async route contexts. Source-level hostname-boundary logic is present.

## Conditional API decisions (unchanged by audit)

| Contract | Source / prior code evidence | State |
|---|---|---|
| U-01 Sync helper methods | `launch()` still documents asynchronous page operations ([`stealth_engine/engine.py:L243-L251`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L243-251)) | CONDITIONAL/UNSUPPORTED; not newly implemented |
| U-02 Video recording on Firefox | rejects unsupported `record_video_dir` ([`stealth_engine/engine.py:L765-L786`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L765-786)) | Explicitly unsupported |
| U-03 CDP-only interfaces | P-05 controlled test protects existing unsupported contract ([`tests/test_forensic_regressions.py:L1613-L1619`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/tests/test_forensic_regressions.py#L1613-1619)) | Unsupported on tested backend path |
| U-04 Additional browser context | preserved P-01 regression ([`tests/test_forensic_regressions.py:L706-L728`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/tests/test_forensic_regressions.py#L706-728)) | Conditional/unsupported |
| U-05 Proxy-pool orchestration | `StealthEngine` constructs manager from a single config proxy ([`stealth_engine/engine.py:L233-L237`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L233-237)) | Conditional; no full pool integration claimed |
| U-06 Timeout semantics | controlled test verifies task-only timeout ([`tests/test_forensic_regressions.py:L1601-L1612`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/tests/test_forensic_regressions.py#L1601-1612)) | Conditional; no guarantee for all external code |

## Packaging and pipeline provenance

**Source:** [`pyproject.toml:L1-L12`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/pyproject.toml#L1-12)

```toml
   1 | [build-system]
   2 | requires = ["setuptools>=68", "wheel"]
   3 | build-backend = "setuptools.build_meta"
   4 | 
   5 | [project]
   6 | name = "stealth_engine"
   7 | version = "0.3.0"
   8 | description = "Reusable browser-automation engine on Camoufox + Playwright: consistent identities, GeoIP-aware proxies, session isolation, and bulk orchestration."
   9 | readme = "README.md"
  10 | requires-python = ">=3.10"
  11 | authors = [
  12 |     { name = "Md Nurnobi", email = "hello@vibtools.io" },
```

**Source:** [`pyproject.toml:L29-L42`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/pyproject.toml#L29-42)

```toml
  29 | ]
  30 | dependencies = [
  31 |     "camoufox",
  32 |     "playwright",
  33 |     "browserforge",
  34 |     "pydantic",
  35 |     "aiohttp",
  36 |     "loguru",
  37 |     "tzlocal>=5.0",
  38 |     "pyyaml>=6.0",
  39 | ]
  40 | 
  41 | [tool.setuptools.packages.find]
  42 | include = ["stealth_engine*"]
```


No tracked CI workflow; no GitLab pipeline, tag, release or commit status for audited head; no proven installation/build artifact. Importing the lightweight `stealth_engine` namespace alone can work with lazy exports; successfully importing the full browser engine and launching it requires real browser dependencies ([`stealth_engine/__init__.py:L28-L53`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/__init__.py#L28-53), [`stealth_engine/__init__.py:L74-L85`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/__init__.py#L74-85)). A package classifier is not a tested-platform guarantee.

## Explicit release-gate conclusion

**Production release not authorized by this evidence.** These are the verified acceptance gaps and deliberate unsupported interfaces, **not a new implementation phase plan**. No code, test, pipeline, dependency, UI or release artifact was created or changed for this audit.
