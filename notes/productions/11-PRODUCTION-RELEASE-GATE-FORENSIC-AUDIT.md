# Production Release Gate — Source Forensic Audit (RG-2026-11-16)

**Repository:** [`ivibtools/stealth-engine`](https://gitlab.com/ivibtools/stealth-engine)  
**Audited immutable GitLab commit:** `e3688ea6cab936b17b65f761fc2049bbeb50cad2` (`main` at audit start)  
**Audit date:** 2026-11-16 UTC  
**Permission / Scope:** read-only source analysis and isolated tests; **only `notes/productions/` audit Markdown may be committed**. No source change, bug fix, dependency installation, browser launch, external proxy, build, tag or release.  
**Provenance:** GitLab tree and source blob hash compared with isolated local checkout; 14 representative source/test/config blobs matched exactly. Line numbers below refer to the immutable SHA; prior P-01–P-05 evidence reports were inspected only as corroboration, never substituted for source.  


## Decision: **NO-GO / PRODUCTION ACCEPTANCE BLOCKED**

The five documented patch phases (P-01 to P-05) addressed 19 original source findings. **They did not establish live production verification.** This report makes no claim that the browser, proxy network, Windows profile locking, package installation or release work end-to-end.

### Evidence status (count different concepts separately)

| Signal | Observed fact | Interpretation |
|---|---|---|
| Code phases | P-01 to P-05 patches present; current engine/test blob hashes match GitLab | **5/5 code phases patched, 0/5 live production-accepted** |
| Syntax-only gate | 30 local Python source/test/example files AST-parsed successfully | Syntax success only; not runtime or install proof |
| Focused controlled tests | **71/71 PASS**, isolated Linux tests with dependency stubs | Patches behave under test doubles; not real Camoufox evidence |
| Full suite with stubs | **235 passed, 8 failed, 4 skipped, 32 subtests passed** | Exit nonzero; 8 distinct failed test cases reproduced |
| Full suite without stubs | **11 collection errors** due to missing `browserforge` | No unmocked full-suite result in this environment |
| Distribution/release | No GitLab pipelines, tags, releases; no tracked CI workflow or dependency lock | Packaging/release gate not demonstrated |
| Windows/live browser/external proxy | No verified run recorded in this audited environment | **NOT VERIFIED** — not a proven runtime pass or fail |

Refer to the separate [eight-failure inventory](12-RELEASE-GATE-TEST-FAILURE-INVENTORY.md) for individual failure IDs and reproductions; refer to the [acceptance matrix](13-RELEASE-GATE-ACCEPTANCE-MATRIX.md) for all unverified runtime gates.

## Source verification by phase (not a substitute for runtime acceptance)

### P-01 — Lifecycle, async page, emergency cleanup

Sync launch starts a dedicated loop rather than calling `asyncio.run()` and losing the browser loop; the initial page is awaited; launch exceptions enter cleanup. This is **source-implemented and fake-context-tested**, not real Camoufox certified.

**Source:** [`stealth_engine/engine.py:L272-L281`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L272-281)

```python
 272 |         # A live async browser cannot survive asyncio.run(): that helper
 273 |         # closes its loop before returning the session (F-01).  Keep one
 274 |         # owned loop running until BrowserSession.close()/aclose().
 275 |         import threading
 276 | 
 277 |         worker_loop = asyncio.new_event_loop()
 278 |         ready = threading.Event()
 279 | 
 280 |         def _loop_worker() -> None:
 281 |             asyncio.set_event_loop(worker_loop)
```

**Source:** [`stealth_engine/engine.py:L443-L459`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L443-459)

```python
 443 |             # k) Wrap in BrowserSession and ensure an actual first Page.
 444 |             # Empty persistent contexts require awaiting new_page() (F-02).
 445 |             stage = "wrap"
 446 |             session_obj = BrowserSession(
 447 |                 ctx=playwright_ctx,
 448 |                 ctx_handle=ctx_handle,
 449 |                 session=session,
 450 |                 proxy_manager=self._proxy_manager,
 451 |                 config=cfg,
 452 |             )
 453 |             stage = "initial_page"
 454 |             if session_obj.page is None:
 455 |                 await session_obj.new_page_async()
 456 | 
 457 |             # Fingerprint history is written only after a fully usable
 458 |             # session has been created; failed page setup is not a launch.
 459 |             self._record_fingerprint()
```

**Source:** [`stealth_engine/engine.py:L475-L489`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L475-489)

```python
 475 |         except asyncio.CancelledError:
 476 |             # Cancellation is BaseException on supported Python versions;
 477 |             # release browser/proxy resources before propagating it.
 478 |             await self._emergency_cleanup(ctx_handle, session, self._proxy_manager)
 479 |             raise
 480 |         except StealthEngineError:
 481 |             # Preserve typed sub-exceptions from sub-modules unchanged.
 482 |             await self._emergency_cleanup(ctx_handle, session, self._proxy_manager)
 483 |             raise
 484 |         except Exception as exc:
 485 |             await self._emergency_cleanup(ctx_handle, session, self._proxy_manager)
 486 |             raise LaunchError(
 487 |                 f"camoufox launch failed at stage={stage!r}: {exc}",
 488 |                 details={"stage": stage, "reason": str(exc)},
 489 |             ) from exc
```


**Release gate:** first launch, first page, close, cancellation/failure cleanup with actual Camoufox + Playwright on supported OS not executed. The synchronous API explicitly does not turn async page methods into sync helpers ([`stealth_engine/engine.py:L243-L251`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L243-251)).

### P-02 — Owner-only locks, force-reset, durable history age

A live PID blocks a takeover; instance-token ownership is checked on release; reset inspects owner under OS lock; first-seen is stored separately from capped history.

**Source:** [`stealth_engine/session.py:L300-L318`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/session.py#L300-318)

```python
 300 |             if self._lock_token is not None:
 301 |                 raise SessionError(
 302 |                     "this instance already owns the profile lock",
 303 |                     details={"stage": "acquire_lock"},
 304 |                 )
 305 |             if self._lock_path.exists():
 306 |                 owner = self._read_lock_owner()
 307 |                 if _pid_alive(owner["pid"]):
 308 |                     raise SessionError(
 309 |                         "profile is locked by a live process",
 310 |                         details={"stage": "acquire_lock", "lock": str(self._lock_path)},
 311 |                     )
 312 |                 # Only a dead PID is evidence of staleness. Guard eliminates
 313 |                 # the check/unlink/recreate race among current-version clients.
 314 |                 self._lock_path.unlink()
 315 |                 _log.warning("removed dead-owner profile lock", profile=self._config.profile_name)
 316 |             token = uuid.uuid4().hex
 317 |             payload = {"schema": 2, "pid": os.getpid(), "ts": time.time(), "owner_token": token}
 318 |             created = False
```

**Source:** [`stealth_engine/session.py:L340-L359`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/session.py#L340-359)

```python
 340 |     def release_lock(self) -> None:
 341 |         """Idempotent owner-only release; cannot unlink another instance's lock."""
 342 |         if self._lock_token is None:
 343 |             return
 344 |         with self._profile_lock_guard():
 345 |             if not self._lock_path.exists():
 346 |                 self._lock_token = None
 347 |                 self._lock_pid = None
 348 |                 return
 349 |             owner = self._read_lock_owner()
 350 |             if (
 351 |                 self._lock_pid != os.getpid()
 352 |                 or owner.get("pid") != self._lock_pid
 353 |                 or owner.get("owner_token") != self._lock_token
 354 |             ):
 355 |                 raise SessionError(
 356 |                     "profile lock ownership changed; refusing to release",
 357 |                     details={"stage": "release_lock", "lock": str(self._lock_path)},
 358 |                 )
 359 |             self._lock_path.unlink()
```

**Source:** [`stealth_engine/engine.py:L538-L550`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L538-550)

```python
 538 |                 path.parent.mkdir(parents=True, exist_ok=True)
 539 |                 if path.exists():
 540 |                     backup = path.with_name("fingerprint_history.legacy.json.bak")
 541 |                     if not backup.exists():
 542 |                         with open(backup, "xb") as handle:
 543 |                             handle.write(path.read_bytes())
 544 |                             handle.flush()
 545 |                             _os.fsync(handle.fileno())
 546 |                 metadata = {"schema_version": 1, "first_seen_ts": first_seen,
 547 |                             "origin": "legacy_oldest_known" if known else "first_record"}
 548 |                 meta_tmp = meta_path.with_suffix(".json.tmp")
 549 |                 meta_tmp.write_text(_json.dumps(metadata, indent=2), encoding="utf-8")
 550 |                 _os.replace(meta_tmp, meta_path)
```


**Release gate:** the Windows branch uses `msvcrt.locking` ([`stealth_engine/session.py:L239-L263`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/session.py#L239-263)), whereas tests were executed on Linux. No verified two-process Windows contention, crash recovery, corrupted profile or OS-permission acceptance is available. P-02 history logic works with controlled fingerprints, but the `test_meta.py` suite needs proper browserforge-backed test setup to adjudicate its three current failures.

### P-03 — SOCKS, safe errors, Geo `auto`, public WebRTC hint

SOCKS transports now use a protocol-specific route, proxy URLs require valid host/port, `auto` Geo values are resolved, and a private host interface address is excluded from manual WebRTC public IPv4 hints.

**Source:** [`stealth_engine/proxy.py:L324-L351`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/proxy.py#L324-351)

```python
 324 | 
 325 |         is_socks = proxy.server.startswith(("socks5://", "socks4://"))
 326 |         # aiohttp's proxy= argument speaks HTTP CONNECT, never SOCKS.
 327 |         session = None if is_socks else await self._get_session()
 328 |         proxy_url = self._build_proxy_url(proxy)
 329 |         proxy_auth = self._build_proxy_auth(proxy)
 330 |         timeout = aiohttp.ClientTimeout(total=self._timeout_s)
 331 |         masked = self.mask(proxy)
 332 | 
 333 |         data: dict[str, Any] | None = None
 334 |         last_exc: ProxyError | None = None
 335 |         for attempt in range(self._geo_retries + 1):
 336 |             try:
 337 |                 if is_socks:
 338 |                     # Native SOCKS4a/SOCKS5 handshake; TLS peer validation
 339 |                     # happens inside _fetch_geo_via_socks. No optional deps.
 340 |                     data = await asyncio.wait_for(
 341 |                         asyncio.to_thread(self._fetch_geo_via_socks, proxy),
 342 |                         timeout=self._timeout_s,
 343 |                     )
 344 |                     break
 345 |                 assert session is not None
 346 |                 async with session.get(
 347 |                     self._geo_endpoint,
 348 |                     proxy=proxy_url,
 349 |                     proxy_auth=proxy_auth,
 350 |                     timeout=timeout,
 351 |                 ) as resp:
```

**Source:** [`stealth_engine/config.py:L53-L72`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/config.py#L53-72)

```python
  53 |         accepted = ("http://", "https://", "socks5://", "socks5h://", "socks4://")
  54 |         if not v.startswith(accepted):
  55 |             raise ValueError("proxy server requires http(s):// or socks4/5://")
  56 |         try:
  57 |             parsed = urlsplit(v)
  58 |             hostname = parsed.hostname
  59 |             port = parsed.port  # raises on invalid/non-numeric/out-of-range ports
  60 |         except ValueError:
  61 |             raise ValueError("proxy server has invalid host or port") from None
  62 |         if (
  63 |             not hostname or port is None or port < 1
  64 |             or any(ch.isspace() for ch in v)
  65 |             or parsed.path or parsed.query or parsed.fragment
  66 |             or any(ch in hostname for ch in "/?#@")
  67 |         ):
  68 |             raise ValueError("proxy server requires a valid host and port without path/query")
  69 |         # Maintain the established socks5h alias contract for downstream engines.
  70 |         if parsed.scheme == "socks5h":
  71 |             return "socks5://" + v[len("socks5h://"):]
  72 |         return v
```

**Source:** [`stealth_engine/geo.py:L130-L148`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/geo.py#L130-148)

```python
 130 |     for field, geo_value, cfg_value in (
 131 |         ("locale", geo.locale, config.locale),
 132 |         ("timezone_id", geo.timezone_id, config.timezone),
 133 |     ):
 134 |         if cfg_value is None:
 135 |             checks[field] = {"status": "skipped", "reason": "config unset"}
 136 |             continue
 137 |         # 'auto' requests the resolved GeoIP value, not a literal persona.
 138 |         # Compare against the effective value rather than against 'auto'.
 139 |         effective = geo_value if isinstance(cfg_value, str) and cfg_value.strip().lower() == "auto" else cfg_value
 140 |         match = geo_value == effective
 141 |         checks[field] = {
 142 |             "status": "match" if match else "mismatch",
 143 |             "geo": geo_value,
 144 |             "config": cfg_value,
 145 |             "resolved": effective,
 146 |         }
 147 |         if not match:
 148 |             mismatches.append(field)
```

**Source:** [`stealth_engine/engine.py:L727-L744`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L727-744)

```python
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


**Release gate:** local simulated SOCKS4a/SOCKS5 tests exist ([`tests/test_forensic_regressions.py:L1135-L1218`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/tests/test_forensic_regressions.py#L1135-1218)), but actual third-party proxy egress, geolocation, remote DNS, TLS validation, NAT/public WebRTC IP and browser leak probes are **not verified**. Conditional API U-05 (pool-to-profile orchestration) was not promoted to a new feature.

### P-04 — Fingerprint mapping, seed, secure exports, preset, scoped logging

The engine forwards only selected fingerprint values via Camoufox launch config; generated persona equality with browser-visible properties cannot be inferred. JSON/YAML export now redacts proxy secrets by default, so old full-fidelity round-trip tests conflict with intentional security policy.

**Source:** [`stealth_engine/engine.py:L788-L796`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L788-796)

```python
 788 |         # Apply only Camoufox-supported keys from the generated proposal.
 789 |         # Camoufox itself draws the UA, viewport, screen, platform, memory,
 790 |         # color-scheme and touch properties; our separately generated values
 791 |         # cannot truthfully be claimed browser-visible without a live readback.
 792 |         # A user-requested hardware concurrency override wins over the draw.
 793 |         concurrency = (cfg.hardware_concurrency if cfg.hardware_concurrency is not None
 794 |                        else fp.get("hardware_concurrency"))
 795 |         if isinstance(concurrency, int) and not isinstance(concurrency, bool) and concurrency > 0:
 796 |             launch_config["navigator.hardwareConcurrency"] = concurrency
```

**Source:** [`stealth_engine/config.py:L259-L277`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/config.py#L259-277)

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
```

**Source:** [`stealth_engine/config.py:L313-L320`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/config.py#L313-320)

```python
 313 |     def save_json(self, path: str | Path, *, include_secrets: bool = False) -> None:
 314 |         """Atomically export JSON. Credentials are omitted by default.
 315 | 
 316 |         Pass include_secrets=True only for a private, access-controlled backup.
 317 |         On Windows, file ACL behavior must be verified separately.
 318 |         """
 319 |         data = self._export_data(include_secrets)
 320 |         self._write_private_export(path, json.dumps(data, indent=2, sort_keys=True) + "\n")
```


**Confirmed F-19 coverage gap — global module logging bypasses profile severity:**

**Source:** [`stealth_engine/utils/logging.py:L37-L49`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/utils/logging.py#L37-49)

```python
  37 | def get_logger(name: str) -> "logger.__class__":
  38 |     """Return a loguru logger bound with a module context field.
  39 | 
  40 |     Does not create a new logger instance; uses loguru's process-global
  41 |     logger with an additional ``module`` binding.
  42 | 
  43 |     Args:
  44 |         name: Logical module name attached to every log record as ``module``.
  45 | 
  46 |     Returns:
  47 |         A bound loguru logger that includes ``module=name`` in every record.
  48 |     """
  49 |     return logger.bind(module=name)
```

**Source:** [`stealth_engine/utils/logging.py:L71-L86`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/utils/logging.py#L71-86)

```python
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


Engine launch uses `self._profile_log.info(...)` ([`stealth_engine/engine.py:L461-L473`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L461-473)), but other engine and module records use global `_log` ([`stealth_engine/engine.py:L554-L568`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L554-568), [`stealth_engine/session.py:L315-L338`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/session.py#L315-338), [`stealth_engine/identity.py:L638-L647`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/identity.py#L638-647)). Reproduction with an ERROR-only profile: profile debug record suppressed; global module debug record still emitted. This proves **incomplete per-profile log isolation**, not proof that any private user credential was leaked in a live run.

**Confirmed redaction boundary:** `ProfileLogger._scrub()` only transforms direct strings; a nested dict in logging extras remains unchanged ([`stealth_engine/utils/logging.py:L71-L86`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/utils/logging.py#L71-86)). Controlled sink retained a synthetic secret in a nested dictionary. Treat as a **data-exposure path requiring security acceptance**, not an observed breach. In contrast, direct string replacement is implemented.

**Release gate:** live browser fingerprint readback parity, Windows export ACL semantics, acceptance of the redacted-default contract, and full logging isolation are not proven. Two legacy assertions fail ([`tests/test_feature_p_y.py:L115-L134`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/tests/test_feature_p_y.py#L115-134)); these are intentional-compatibility conflicts, not evidence that secrets should be made public again.

### P-05 — Seeded readbacks, tracker hostname routes

Noise initializes a local deterministic RNG at each readback. Tracker matching uses parsed destination host and dotted hostname boundary rather than searching the entire URL.

**Source:** [`stealth_engine/engine.py:L85-L102`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L85-102)

```python
  85 |     s = int(hashlib.sha256(f"jsn-{seed}".encode()).hexdigest()[:8], 16)
  86 |     return f"""
  87 | (() => {{
  88 |   const _seed = {s} | 0;
  89 |   const _perturb = (data, step) => {{
  90 |     // F-16: reset the seeded stream for each readback. Identical pixels
  91 |     // yield identical output even when other canvas/WebGL reads intervene.
  92 |     let state = _seed;
  93 |     const rnd = () => {{
  94 |       state = state + 0x6D2B79F5 | 0;
  95 |       let t = Math.imul(state ^ state >>> 15, 1 | state);
  96 |       t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
  97 |       return ((t ^ t >>> 14) >>> 0) / 4294967296;
  98 |     }};
  99 |     for (let i = 0; i < data.length; i += step * 4) {{
 100 |       const jitter = (rnd() < 0.5 ? -1 : 1) * (rnd() * 3 | 0);
 101 |       data[i] = Math.max(0, Math.min(255, data[i] + jitter));
 102 |     }}
```

**Source:** [`stealth_engine/engine.py:L1689-L1711`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L1689-1711)

```python
1689 |         from urllib.parse import urlsplit
1690 | 
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
1710 |         try:
1711 |             await self._ctx.route("**/*", _handler)
```


**Release gate:** offscreen test-double canvas/WebGL and route-handler tests pass, but genuine multi-page Camoufox/Firefox execution, JS detectability and live network interception are **NOT VERIFIED**. U-02/U-03/U-06 remain conditional or intentionally unsupported; no new support is asserted.

## Additional release observations backed by the current tree

### RG-PKG-01 — Build/release pipeline not established

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


- `pyproject.toml` states `0.3.0`, and `stealth_engine/__init__.py:12` also reports `0.3.0` ([`stealth_engine/__init__.py:L9-L13`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/__init__.py#L9-13)). This is **metadata consistency**, not package-install or wheel-build verification.
- None of the 8 runtime dependencies is exactly version-pinned in `[project].dependencies`; no dependency lock or build constraint file is present in the audited GitLab tree. Reproducible cross-version installs are **not demonstrated**.
- GitLab API returned **0 pipelines, 0 tags, 0 releases, and 0 commit statuses** for the audited head; tracked tree contains no `.gitlab-ci.yml` or workflow definition. Absence of CI data is not a CI pass.
- No wheel/sdist build, pip-install test, import test from a built distribution, Playwright/browser binary provisioning verification, package publish, release signing or artifact checks have been performed as part of this **read-only gate**.
- The test runner here is Python **3.13.5 on Linux**; `pyproject.toml` declares `>=3.10` but the package classifier lists 3.10–3.12. Multi-Python and Windows test matrix have not been established.

### RG-TEST-01 — Full suite is not green

The exact eight cases in [12](12-RELEASE-GATE-TEST-FAILURE-INVENTORY.md) divide into **2 intentional security-contract/test mismatches**, **3 dependency-stub/availability failures**, and **3 history tests blocked by fingerprint-provider setup**. Do **not** mislabel all eight as eight proven production bugs. However, none may be silently treated as passed or ignored for release acceptance.

### Security/operational distinctions

- **Confirmed source behavior gap:** module-level log messages do not respect a profile-specific threshold.
- **Confirmed possible secret exposure path:** nested values passed to `ProfileLogger` are not recursively redacted; a synthetic nested password survives into structured logging extras.
- **Unverified:** actual credential leakage, production account impact, browser privacy characteristics, target-site detection, Windows ACLs, proxy egress/TLS/DNS behavior and installer reliability. No evidence supports declaring these successful or broken.

## Release decision and scope declaration

**NO-GO.** A safe release requires failing test contracts resolved/explicitly reclassified, a dependency-complete clean full suite, F-19/security boundaries assessed, actual supported-browser/OS/network acceptance and installable package/CI artifact evidence. These are **acceptance conditions**, **not authorization or a new implementation roadmap**. No source code, tests, UI, config, build tooling, CI or runtime feature was modified during this audit. Existing P-01–P-05 source remains unchanged; the audit adds Markdown only.
