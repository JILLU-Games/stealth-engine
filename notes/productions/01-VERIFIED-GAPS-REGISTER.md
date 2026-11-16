# 01 — Verified Production Gaps Register (Source-Referenced)

> **Status (current): P-01–P-05 code patches applied (19/19 targets code-addressed); P-05 71/71 focused offline PASS; full suite 235 PASS / 8 FAIL / 4 SKIP; production acceptance 0/5.** P-04 legacy conflicts, three fingerprint-history tests, unavailable Camoufox/browserforge and live/Windows gates remain open. Baseline findings below are historical and retained as evidence.
> **Immutable source baseline:** [`a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`](https://gitlab.com/ivibtools/stealth-engine/-/commit/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5); prior source audit revision [`6255383cac9f29d64bf9ee5957c77ee26ccd7993`](https://gitlab.com/ivibtools/stealth-engine/-/commit/6255383cac9f29d64bf9ee5957c77ee26ccd7993). The 31 audited executable/config blob hashes match across these revisions.


## Meaning of counts

**19 source-supported findings:** Critical 1, High 11, Medium 7. They are findings about real code pathways; **not** 19 independently witnessed browser-production failures. Isolated offline reproduction outcomes quoted below were recorded in the previously committed audit. This planning document independently extracts its code snippets from the unchanged baseline source SHA.

| Finding | Severity | Phase | Specific observed code issue |
|---|---|---|---|
| [F-01](#f-01) | Critical | P-01 | Sync session loop lifecycle |
| [F-02](#f-02) | High | P-01 | Initial page coroutine instead of Playwright Page |
| [F-03](#f-03) | High | P-04 | Generated fingerprint vs launch application contract |
| [F-04](#f-04) | High | P-04 | Persisted locale/timezone seeds override changed profile config |
| [F-05](#f-05) | High | P-03 | SOCKS probe uses HTTP request path |
| [F-06](#f-06) | High | P-01 | Emergency launch cleanup omits proxy manager |
| [F-07](#f-07) | High | P-02 | Old timestamp preempts live PID lock |
| [F-08](#f-08) | High | P-02 | Nonowner deletes owner lock |
| [F-09](#f-09) | High | P-02 | force_reset erases active profile |
| [F-10](#f-10) | High | P-04 | Proxy secrets in default config exports |
| [F-11](#f-11) | High | P-03 | Proxy parse error includes credential-bearing input |
| [F-12](#f-12) | Medium | P-03 | Scheme-only proxy URL passes validator |
| [F-13](#f-13) | Medium | P-04 | mobile-android preset cannot validate |
| [F-14](#f-14) | Medium | P-03 | Geo `auto` locale/timezone falsely flagged inconsistent |
| [F-15](#f-15) | High | P-03 | WebRTC candidate address is private interface IP |
| [F-16](#f-16) | Medium | P-05 | Experimental JS canvas noise unstable repeated reads |
| [F-17](#f-17) | Medium | P-05 | Tracker filter matches URL string, not target hostname |
| [F-18](#f-18) | Medium | P-02 | Session age loses original first launch after history cap |
| [F-19](#f-19) | Medium | P-04 | Profile log_level not wired into engine |

## All findings, exact source blocks and acceptance contracts

<a id="f-01"></a>
### F-01 — Sync launch returns after its event loop is closed

- **Severity:** `Critical`; **assigned phase:** `P-01`; **status:** `PATCH APPLIED at 9638c789; OFFLINE PASS / LIVE NOT VERIFIED`.
- **Earlier controlled verification:** Controlled subclass probe: `loop_closed_before_session_use=true`. This is a verified lifecycle invariant, not a live-browser failure log.
- **Source-grounded issue:** Sync session loop lifecycle.
- **Proposed change (not implemented):** Sync facade must own a live event-loop context until session close, or explicitly reject sync launch before allocating resources; choose documented compatibility-preserving contract.
- **Evidence needed to close:** Sync session operation and close on actual backend with no closed-loop error; running-loop calls retain clear error.

**[Source: `stealth_engine/engine.py:244-256`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L244-256)**

```python
 244 |         try:
 245 |             loop = asyncio.get_running_loop()
 246 |         except RuntimeError:
 247 |             loop = None
 248 | 
 249 |         if loop is not None and loop.is_running():
 250 |             raise LaunchError(
 251 |                 "Cannot call launch() from a running event loop. "
 252 |                 "Use 'await engine.alaunch()' instead.",
 253 |                 details={"stage": "launch", "reason": "running event loop detected"},
 254 |             )
 255 | 
 256 |         return asyncio.run(self.alaunch())
```

**[Source: `stealth_engine/engine.py:974-977`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L974-977)**

```python
 974 |         try:
 975 |             asyncio.run(_async_close())
 976 |         except Exception as exc:
 977 |             _log.warning("close: async cleanup failed", reason=str(exc))
```

<a id="f-02"></a>
### F-02 — Empty initial context stores an unawaited page coroutine

- **Severity:** `High`; **assigned phase:** `P-01`; **status:** `PATCH APPLIED at 9638c789; OFFLINE PASS / LIVE NOT VERIFIED`.
- **Earlier controlled verification:** Async fake context with no pages: `page_is_coroutine=true`. A live persistent context with zero pages was not exercised.
- **Source-grounded issue:** Initial page coroutine instead of Playwright Page.
- **Proposed change (not implemented):** Initialize initial page asynchronously; no unawaited coroutine retained.
- **Evidence needed to close:** Empty-page async fake + real persistent context have a usable Page and no unawaited coroutine warning.

**[Source: `stealth_engine/engine.py:805-811`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L805-811)**

```python
 805 | 
 806 |         # Expose the initial page (persistent context opens with one page).
 807 |         try:
 808 |             pages = ctx.pages
 809 |             self._page: PlaywrightPage = pages[0] if pages else ctx.new_page()
 810 |         except Exception:
 811 |             self._page = None  # type: ignore[assignment]
```

<a id="f-03"></a>
### F-03 — Generated identity fields are not forwarded to browser launch

- **Current P-04 code status (post-patch, overrides historical OPEN baseline):** OFFLINE MAPPING PATCHED, live/browser parity unverified; non-applied generated fields explicitly documented (09). [Code commit](https://gitlab.com/ivibtools/stealth-engine/-/commit/997e5dd5087d4e366dc573f561e2e9ac3a063520), [post-patch evidence](09-P04-VERIFICATION-EVIDENCE.md).

- **Severity:** `High`; **assigned phase:** `P-04`; **status:** `OPEN — baseline`.
- **Earlier controlled verification:** Controlled `_build_launch_kwargs` call: excluded fields `user_agent`, `viewport`, `screen`, `platform`, `device_memory`, `color_scheme`.
- **Source-grounded issue:** Generated fingerprint vs launch application contract.
- **Proposed change (not implemented):** Explicitly map supported generated fields to valid backend options or remove/relabel unsupported identity claims; preserve coherent browser-produced identity.
- **Evidence needed to close:** Backend-supported identity fields match resolved fingerprint evidence; unsupported fields documented without misleading claims.

**[Source: `stealth_engine/identity.py:429-438`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/identity.py#L429-438)**

```python
 429 | 
 430 |         Returns:
 431 |             A dict with the following keys, all populated with non-empty
 432 |             values:
 433 | 
 434 |             - ``user_agent`` (:class:`str`)
 435 |             - ``viewport`` (:class:`dict` with ``width`` / ``height``)
 436 |             - ``screen`` (:class:`dict` with ``width`` / ``height``)
 437 |             - ``locale`` (:class:`str`)
 438 |             - ``timezone_id`` (:class:`str`)
```

**[Source: `stealth_engine/engine.py:613-619`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L613-619)**

```python
 613 |         kwargs: dict[str, Any] = {
 614 |             "os": cfg.os,
 615 |             "headless": cfg.headless,
 616 |             "persistent_context": True,
 617 |             "user_data_dir": self._session.user_data_dir,
 618 |             "locale": fp.get("locale", "en-US"),
 619 |         }
```

<a id="f-04"></a>
### F-04 — Persisted seeds override subsequently changed locale/timezone config

- **Current P-04 code status (post-patch, overrides historical OPEN baseline):** OFFLINE PATCHED: explicit locale/timezone precedence over valid persisted seed metadata; numeric seeds retained (09). [Code commit](https://gitlab.com/ivibtools/stealth-engine/-/commit/997e5dd5087d4e366dc573f561e2e9ac3a063520), [post-patch evidence](09-P04-VERIFICATION-EVIDENCE.md).

- **Severity:** `High`; **assigned phase:** `P-04`; **status:** `OPEN — baseline`.
- **Earlier controlled verification:** Same profile seeded `en-US`/`UTC`, then configured `fr-FR`/`Europe/Paris`: reused seeds remain `en-US`/`UTC`.
- **Source-grounded issue:** Persisted locale/timezone seeds override changed profile config.
- **Proposed change (not implemented):** Keep stable numeric seeds while honoring explicit updated locale/timezone according to a documented precedence policy.
- **Evidence needed to close:** Config change + persisted-seed regression maintains intended locality and deterministic seed continuity.

**[Source: `stealth_engine/identity.py:486-500`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/identity.py#L486-500)**

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
```

**[Source: `stealth_engine/engine.py:326-333`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L326-333)**

```python
 326 |             # g) GeoIP overrides (PH-04)
 327 |             if geo is not None and cfg.geoip:
 328 |                 fp["timezone_id"] = geo.timezone_id
 329 |                 fp["locale"] = geo.locale
 330 |             else:
 331 |                 # Mode A: use seeds for locale/timezone (PH-03)
 332 |                 fp["timezone_id"] = seeds["timezone_id"]
 333 |                 fp["locale"] = seeds["locale"]
```

<a id="f-05"></a>
### F-05 — SOCKS proxy validation uses HTTP traffic, not a SOCKS handshake

- **Severity:** `High`; **assigned phase:** `P-03`; **status:** `OPEN — baseline`.
- **P-03 current status:** `PATCH APPLIED / LINUX OFFLINE 59/59 PASS / LIVE+WINDOWS UNVERIFIED`. Native SOCKS5 (including username/password) and SOCKS4a TCP tunnels are used for GeoIP health requests; local wire-level mock handshakes pass, HTTP aiohttp path unchanged. [Current code stealth_engine/proxy.py:324-348](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/proxy.py#L324-348). [Exact code and tests](08-P03-VERIFICATION-EVIDENCE.md). Baseline excerpt below is historical and intentionally unchanged.
- **Earlier controlled verification:** Local loopback server captured first request bytes: `GET http://example.invalid/ HTTP/1.1`, not SOCKS5 greeting.
- **Source-grounded issue:** SOCKS probe uses HTTP request path.
- **Proposed change (not implemented):** Use an appropriate SOCKS-capable health/Geo transport or fail explicitly when unavailable; do not misclassify healthy SOCKS proxies as dead.
- **Evidence needed to close:** Loopback SOCKS wire probe shows correct SOCKS greeting; genuine HTTP proxy behavior unchanged.

**[Source: `stealth_engine/proxy.py:320-335`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/proxy.py#L320-335)**

```python
 320 |         session = await self._get_session()
 321 |         proxy_url = self._build_proxy_url(proxy)
 322 |         proxy_auth = self._build_proxy_auth(proxy)
 323 |         timeout = aiohttp.ClientTimeout(total=self._timeout_s)
 324 |         masked = self.mask(proxy)
 325 | 
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
```

<a id="f-06"></a>
### F-06 — Launch failure cleanup omits proxy manager closure

- **Severity:** `High`; **assigned phase:** `P-01`; **status:** `PATCH APPLIED at 9638c789; OFFLINE PASS / LIVE NOT VERIFIED`.
- **Earlier controlled verification:** Injected proxy manager + failed launch: `proxy_close_called_after_exception=false`, lock released. No external network used.
- **Source-grounded issue:** Emergency launch cleanup omits proxy manager.
- **Proposed change (not implemented):** Close context/proxy manager and release lock with correct ownership even if startup fails.
- **Evidence needed to close:** Injected failures at each launch stage leave no live proxy session or owned lock; original typed exception preserved.

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

<a id="f-07"></a>
### F-07 — 24-hour age overrides live-process lock ownership

- **Severity:** `High`; **assigned phase:** `P-02`; **status:** `OPEN — baseline`.
- **P-02 current status:** `PATCH APPLIED / 35/35 OFFLINE TESTS PASS / LIVE & WINDOWS NOT VERIFIED`. Live PID locks are no longer timed out; dead-PID reclamation serialized with a persistent OS-level guard. Current code: [stealth_engine/session.py:289-339](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L289-339). Full exact source excerpt and tests: [07-P02-VERIFICATION-EVIDENCE.md](07-P02-VERIFICATION-EVIDENCE.md). Historical source block below intentionally remains frozen. 
- **Earlier controlled verification:** Temp lock with live current PID and timestamp older than 24 hours: second manager reacquired lock successfully.
- **Source-grounded issue:** Old timestamp preempts live PID lock.
- **Proposed change (not implemented):** Treat demonstrably live lock owner as authoritative; time threshold alone must not steal ownership.
- **Evidence needed to close:** Live-PID old lock remains protected; truly stale lock can be recovered safely.

**[Source: `stealth_engine/session.py:275-292`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/session.py#L275-292)**

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
```

<a id="f-08"></a>
### F-08 — A non-owner can release another manager's profile lock

- **Severity:** `High`; **assigned phase:** `P-02`; **status:** `OPEN — baseline`.
- **P-02 current status:** `PATCH APPLIED / 35/35 OFFLINE TESTS PASS / LIVE & WINDOWS NOT VERIFIED`. Each instance has a UUID owner token; non-owner release is a no-op; mismatched token raises `SessionError`. Current code: [stealth_engine/session.py:340-366](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L340-366). Full exact source excerpt and tests: [07-P02-VERIFICATION-EVIDENCE.md](07-P02-VERIFICATION-EVIDENCE.md). Historical source block below intentionally remains frozen. 
- **Earlier controlled verification:** Two SessionManager instances for same profile; the second never acquired a lock but `release_lock()` deleted the first instance’s lock.
- **Source-grounded issue:** Nonowner deletes owner lock.
- **Proposed change (not implemented):** Store per-acquisition ownership token and release only matching own lock.
- **Evidence needed to close:** Second manager cannot remove first manager lock; repeated owner release idempotent.

**[Source: `stealth_engine/session.py:307-317`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/session.py#L307-317)**

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
```

<a id="f-09"></a>
### F-09 — Force reset deletes an active profile without ownership check

- **Severity:** `High`; **assigned phase:** `P-02`; **status:** `OPEN — baseline`.
- **P-02 current status:** `PATCH APPLIED / 35/35 OFFLINE TESTS PASS / LIVE & WINDOWS NOT VERIFIED`. `force_reset()` refuses live/unknown locks and own active token; an idle profile can reset with typed filesystem errors. Current code: [stealth_engine/session.py:368-407](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L368-407). Full exact source excerpt and tests: [07-P02-VERIFICATION-EVIDENCE.md](07-P02-VERIFICATION-EVIDENCE.md). Historical source block below intentionally remains frozen. 
- **Earlier controlled verification:** One SessionManager held lock; second instance called `force_reset()` and active profile directory disappeared.
- **Source-grounded issue:** force_reset erases active profile.
- **Proposed change (not implemented):** Explicitly reject reset when another live owner holds profile; never delete without enforceable ownership.
- **Evidence needed to close:** Concurrent-owner reset raises typed error and leaves state intact; controlled idle reset works.

**[Source: `stealth_engine/session.py:323-336`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/session.py#L323-336)**

```python
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

<a id="f-10"></a>
### F-10 — Config export exposes proxy credentials in default-created files

- **Current P-04 code status (post-patch, overrides historical OPEN baseline):** OFFLINE PATCHED: redacted JSON/YAML defaults, opt-in private secret backup; two legacy default-roundtrip tests FAIL (09). [Code commit](https://gitlab.com/ivibtools/stealth-engine/-/commit/997e5dd5087d4e366dc573f561e2e9ac3a063520), [post-patch evidence](09-P04-VERIFICATION-EVIDENCE.md).

- **Severity:** `High`; **assigned phase:** `P-04`; **status:** `OPEN — baseline`.
- **Earlier controlled verification:** Linux temp directory under default umask: JSON file mode `0644`, password present in plaintext. This result is environment-specific.
- **Source-grounded issue:** Proxy secrets in default config exports.
- **Proposed change (not implemented):** Use secure export contract (redacted default or explicit secret-export opt-in), restrictive permissions, and safe atomic handling across supported systems.
- **Evidence needed to close:** Default exported data contains no proxy password; explicit secure path is tested and Windows/Linux permission semantics documented.

**[Source: `stealth_engine/config.py:260-269`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L260-269)**

```python
 260 |         p = Path(path)
 261 |         tmp = p.with_suffix(p.suffix + ".tmp")
 262 |         tmp.write_text(
 263 |             json.dumps(
 264 |                 self.model_dump(mode="json"), indent=2, sort_keys=True
 265 |             )
 266 |             + "\n",
 267 |             encoding="utf-8",
 268 |         )
 269 |         os.replace(tmp, p)
```

**[Source: `stealth_engine/config.py:300-308`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L300-308)**

```python
 300 |         import yaml
 301 | 
 302 |         p = Path(path)
 303 |         tmp = p.with_suffix(p.suffix + ".tmp")
 304 |         tmp.write_text(
 305 |             yaml.safe_dump(
 306 |                 self.model_dump(mode="json"), sort_keys=True
 307 |             ),
 308 |             encoding="utf-8",
```

<a id="f-11"></a>
### F-11 — Invalid proxy line exception can include raw credentials

- **Severity:** `High`; **assigned phase:** `P-03`; **status:** `OPEN — baseline`.
- **P-03 current status:** `PATCH APPLIED / LINUX OFFLINE 59/59 PASS / LIVE+WINDOWS UNVERIFIED`. Proxy file parse errors no longer include raw credential-bearing lines or chained validation exception; ProxyConfig masks input in validation error strings. [Current code stealth_engine/proxy.py:768-815](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/proxy.py#L768-815). [Exact code and tests](08-P03-VERIFICATION-EVIDENCE.md). Baseline excerpt below is historical and intentionally unchanged.
- **Earlier controlled verification:** `_parse_proxy_line("secret-user:secret-pass@",1)` raised ProxyError whose string contains `secret-pass`.
- **Source-grounded issue:** Proxy parse error includes credential-bearing input.
- **Proposed change (not implemented):** Ensure exception text/details/log messages never contain raw URL credentials or proxy password.
- **Evidence needed to close:** Malformed username/password proxy lines produce safe error messages and diagnostics.

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

**[Source: `stealth_engine/proxy.py:657-668`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/proxy.py#L657-668)**

```python
 657 |     if "@" in line:
 658 |         # user:pass@host:port — embed credentials into a URL.
 659 |         creds, _, hostport = line.partition("@")
 660 |         user, _, pw = creds.partition(":")
 661 |         if not user or not hostport:
 662 |             raise _err("malformed credentials@host:port")
 663 |         from urllib.parse import quote
 664 |         server = f"http://{quote(user, safe='')}:{quote(pw, safe='')}@{hostport}"
 665 |         try:
 666 |             return ProxyConfig(server=server)
 667 |         except Exception as exc:
 668 |             raise _err(f"invalid credentialed proxy: {exc}") from exc
```

<a id="f-12"></a>
### F-12 — Proxy URL validator accepts scheme-only endpoint

- **Severity:** `Medium`; **assigned phase:** `P-03`; **status:** `OPEN — baseline`.
- **P-03 current status:** `PATCH APPLIED / LINUX OFFLINE 59/59 PASS / LIVE+WINDOWS UNVERIFIED`. ProxyConfig requires a valid URL authority (host and port 1–65535) with no path/query/fragment; socks5h remains normalized. [Current code stealth_engine/config.py:41-78](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/config.py#L41-78). [Exact code and tests](08-P03-VERIFICATION-EVIDENCE.md). Baseline excerpt below is historical and intentionally unchanged.
- **Earlier controlled verification:** `ProxyConfig(server="http://")` succeeded in a local pure-Python probe.
- **Source-grounded issue:** Scheme-only proxy URL passes validator.
- **Proposed change (not implemented):** Validate parsed host, port and allowable schemes with safe error rendering.
- **Evidence needed to close:** `http://`/`socks5://` rejected; valid URLs and IPv6 supported per public contract.

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

<a id="f-13"></a>
### F-13 — Built-in mobile-android preset cannot validate

- **Current P-04 code status (post-patch, overrides historical OPEN baseline):** OFFLINE PATCHED: invalid mobile-android name removed; public presets validated, compatibility break (09). [Code commit](https://gitlab.com/ivibtools/stealth-engine/-/commit/997e5dd5087d4e366dc573f561e2e9ac3a063520), [post-patch evidence](09-P04-VERIFICATION-EVIDENCE.md).

- **Severity:** `Medium`; **assigned phase:** `P-04`; **status:** `OPEN — baseline`.
- **Earlier controlled verification:** `ProfileConfig.preset("mobile-android", profile_name="probe", user_data_dir="/tmp/probe")` raised pydantic ValidationError for `os`.
- **Source-grounded issue:** mobile-android preset cannot validate.
- **Proposed change (not implemented):** Align preset OS choice with backend-supported `ProfileConfig.os` types; no invalid advertised built-in preset.
- **Evidence needed to close:** Every `preset_names()` choice validates or is explicitly removed with compatibility note.

**[Source: `stealth_engine/config.py:354-359`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L354-359)**

```python
 354 |     "mobile-android": {
 355 |         "os": "android",
 356 |         "locale": "en-US",
 357 |         "timezone": "America/Los_Angeles",
 358 |         "headless": True,
 359 |     },
```

**[Source: `stealth_engine/config.py:368-379`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L368-379)**

```python
 368 | # Attach the classmethod without cluttering the class body.
 369 | def _preset_classmethod(cls: type, name: str, **overrides: Any) -> "ProfileConfig":
 370 |     """Build a ``ProfileConfig`` from a named preset merged with overrides."""
 371 |     if name not in _PROFILE_PRESETS:
 372 |         from .exceptions import ConfigError
 373 | 
 374 |         raise ConfigError(
 375 |             f"unknown profile preset: {name!r}",
 376 |             details={"stage": "preset", "preset": name, "available": preset_names()},
 377 |         )
 378 |     merged = {**_PROFILE_PRESETS[name], **overrides}
 379 |     return cls.model_validate(merged)
```

<a id="f-14"></a>
### F-14 — Geo auto settings are incorrectly reported inconsistent

- **Severity:** `Medium`; **assigned phase:** `P-03`; **status:** `OPEN — baseline`.
- **P-03 current status:** `PATCH APPLIED / LINUX OFFLINE 59/59 PASS / LIVE+WINDOWS UNVERIFIED`. Geo `auto` becomes the resolved GeoInfo value before comparison; explicit conflicts remain mismatches. [Current code stealth_engine/geo.py:130-150](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/geo.py#L130-150). [Exact code and tests](08-P03-VERIFICATION-EVIDENCE.md). Baseline excerpt below is historical and intentionally unchanged.
- **Earlier controlled verification:** US GeoInfo with `locale=en-US`, `timezone_id=America/New_York` + config `locale=auto`, `timezone=auto` returned `consistent=false`, both mismatches.
- **Source-grounded issue:** Geo `auto` locale/timezone falsely flagged inconsistent.
- **Proposed change (not implemented):** Resolve auto sentinels against observed Geo data before comparing; preserve mismatch for truly explicit conflicting values.
- **Evidence needed to close:** `auto/auto` with valid GeoInfo consistent; explicit mismatches still detected.

**[Source: `stealth_engine/geo.py:130-144`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/geo.py#L130-144)**

```python
 130 |     for field, geo_value, cfg_value in (
 131 |         ("locale", geo.locale, config.locale),
 132 |         ("timezone_id", geo.timezone_id, config.timezone),
 133 |     ):
 134 |         if cfg_value is None:
 135 |             checks[field] = {"status": "skipped", "reason": "config unset"}
 136 |             continue
 137 |         match = geo_value == cfg_value
 138 |         checks[field] = {
 139 |             "status": "match" if match else "mismatch",
 140 |             "geo": geo_value,
 141 |             "config": cfg_value,
 142 |         }
 143 |         if not match:
 144 |             mismatches.append(field)
```

<a id="f-15"></a>
### F-15 — Direct WebRTC IP setting uses interface/private address, not internet public IP

- **Severity:** `High`; **assigned phase:** `P-03`; **status:** `OPEN — baseline`.
- **P-03 current status:** `PATCH APPLIED / LINUX OFFLINE 59/59 PASS / LIVE+WINDOWS UNVERIFIED`. Launch configuration forwards only globally routed IPv4 WebRTC hints; rejects explicit invalid/private addresses and omits unknown/private guessed host hints. [Current code stealth_engine/engine.py:706-733](https://gitlab.com/ivibtools/stealth-engine/-/blob/b2d1884a8e7534d28f492d9f3274eb17c5551b3a/stealth_engine/engine.py#L706-733). [Exact code and tests](08-P03-VERIFICATION-EVIDENCE.md). Baseline excerpt below is historical and intentionally unchanged.
- **Earlier controlled verification:** On isolated audit host: method returned `172.26.39.156`, Python `ipaddress.is_global=false`.
- **Source-grounded issue:** WebRTC candidate address is private interface IP.
- **Proposed change (not implemented):** Never label/use interface IP as internet public; use provably appropriate policy or conservative backend-supported leak protection.
- **Evidence needed to close:** Private/interface address not substituted for public egress IP; controlled WebRTC checks with permission and proxy context.

**[Source: `stealth_engine/engine.py:499-525`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L499-525)**

```python
 499 |         try:
 500 |             # UDP connection to a public DNS server — no data sent, just routing.
 501 |             with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
 502 |                 s.settimeout(5)
 503 |                 s.connect(("8.8.8.8", 53))
 504 |                 host_ip = s.getsockname()[0]
 505 |             if host_ip:
 506 |                 return host_ip
 507 |         except OSError:
 508 |             pass
 509 |         # BF-02/B-05: best-effort fallbacks — never kill the launch just
 510 |         # because the WebRTC IP hint couldn't be resolved.
 511 |         try:
 512 |             host_ip = socket.gethostbyname(socket.gethostname())
 513 |             if host_ip and host_ip != "127.0.0.1":
 514 |                 _log.warning(
 515 |                     "host IP via UDP probe failed; using hostname resolution",
 516 |                     host_ip=host_ip,
 517 |                 )
 518 |                 return host_ip
 519 |         except OSError:
 520 |             pass
 521 |         _log.warning(
 522 |             "could not resolve host IP for WebRTC; using 0.0.0.0 "
 523 |             "(launch continues — camoufox may ignore the hint)"
 524 |         )
 525 |         return "0.0.0.0"
```

**[Source: `stealth_engine/engine.py:640-645`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L640-645)**

```python
 640 |             kwargs["geoip"] = False
 641 |             # Mode A: WebRTC advertises host IP (PH-03)
 642 |             if cfg.target_ip:
 643 |                 launch_config["webrtc:ipv4"] = cfg.target_ip
 644 |             else:
 645 |                 launch_config["webrtc:ipv4"] = self._resolve_host_ip()
```

<a id="f-16"></a>
### F-16 — Experimental JS noise changes identical canvas readbacks

- **Severity:** `Medium`; **assigned phase:** `P-05`; **status:** `OPEN at baseline; P-05 code-patched / offline tests pass; real-browser acceptance pending`.
- **Earlier controlled verification:** Executed generated init script against a Node.js canvas-shaped test double: `first_and_second_equal=false` on identical input. Not validated in Camoufox.
- **Source-grounded issue:** Experimental JS canvas noise unstable repeated reads.
- **Proposed change (not implemented):** Make opt-in noise deterministic for repeated identical input or disable unsupported behavior; avoid oscillating same-canvas readback.
- **Evidence needed to close:** Node probe repeated identical readbacks stable; real Camoufox canary only when environment available.

**[Source: `stealth_engine/engine.py:84-99`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L84-99)**

```python
  84 |     s = int(hashlib.sha256(f"jsn-{seed}".encode()).hexdigest()[:8], 16)
  85 |     return f"""
  86 | (() => {{
  87 |   let _s = {s} | 0;
  88 |   const _rnd = () => {{
  89 |     _s = _s + 0x6D2B79F5 | 0;
  90 |     let t = Math.imul(_s ^ _s >>> 15, 1 | _s);
  91 |     t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
  92 |     return ((t ^ t >>> 14) >>> 0) / 4294967296;
  93 |   }};
  94 |   const _jit = () => (_rnd() < 0.5 ? -1 : 1) * (_rnd() * 3 | 0);
  95 |   const _perturb = (data, step) => {{
  96 |     for (let i = 0; i < data.length; i += step * 4) {{
  97 |       data[i] = Math.max(0, Math.min(255, data[i] + _jit()));
  98 |     }}
  99 |   }};
```

**[Source: `stealth_engine/engine.py:100-116`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L100-116)**

```python
 100 |   try {{
 101 |     const _td = HTMLCanvasElement.prototype.toDataURL;
 102 |     HTMLCanvasElement.prototype.toDataURL = function (...a) {{
 103 |       try {{
 104 |         const cx = this.getContext('2d');
 105 |         if (cx && this.width * this.height < 4000000) {{
 106 |           // BF-02/B-06: render to an OFFSCREEN clone — never mutate the
 107 |           // live canvas (putImageData would alter real pixels).
 108 |           const tmp = document.createElement('canvas');
 109 |           tmp.width = this.width; tmp.height = this.height;
 110 |           const tctx = tmp.getContext('2d');
 111 |           tctx.drawImage(this, 0, 0);
 112 |           const d = tctx.getImageData(0, 0, tmp.width, tmp.height);
 113 |           _perturb(d.data, 7);
 114 |           tctx.putImageData(d, 0, 0);
 115 |           return _td.apply(tmp, a);
 116 |         }}
```

<a id="f-17"></a>
### F-17 — Tracker blocking matches full URL substrings, not hostname

- **Severity:** `Medium`; **assigned phase:** `P-05`; **status:** `OPEN at baseline; P-05 code-patched / offline tests pass; real-browser acceptance pending`.
- **Earlier controlled verification:** Fake route on `https://good.example.org/article?next=https://google-analytics.com/` was aborted.
- **Source-grounded issue:** Tracker filter matches URL string, not target hostname.
- **Proposed change (not implemented):** Match normalized parsed destination host and explicit rule semantics; do not inspect unrelated query string as destination.
- **Evidence needed to close:** Benign host query containing tracker token allowed; actual blocked host blocked.

**[Source: `stealth_engine/engine.py:1544-1559`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L1544-1559)**

```python
1544 |         domains = list(_TRACKER_DOMAINS) + list(extra_domains or [])
1545 | 
1546 |         async def _handler(route: Any, request: Any) -> None:
1547 |             url = request.url.lower()
1548 |             if any(d in url for d in domains):
1549 |                 await route.abort()
1550 |             else:
1551 |                 await route.continue_()
1552 | 
1553 |         try:
1554 |             await self._ctx.route("**/*", _handler)
1555 |         except Exception as exc:
1556 |             raise AutomationError(
1557 |                 "block_trackers failed",
1558 |                 details={"stage": "block_trackers", "reason": str(exc)},
1559 |             ) from exc
```

<a id="f-18"></a>
### F-18 — Session age stops reflecting first launch after history cap

- **Severity:** `Medium`; **assigned phase:** `P-02`; **status:** `OPEN — baseline`.
- **P-02 current status:** `PATCH APPLIED / 35/35 OFFLINE TESTS PASS / LIVE & WINDOWS NOT VERIFIED`. Versioned `first_seen_ts` sidecar is independent of the capped 50-entry list; legacy backup is retained on migration. Current code: [stealth_engine/engine.py:485-551](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/engine.py#L485-551). Full exact source excerpt and tests: [07-P02-VERIFICATION-EVIDENCE.md](07-P02-VERIFICATION-EVIDENCE.md). Historical source block below intentionally remains frozen. 
- **Earlier controlled verification:** Synthetic 51-entry history with oldest launch 80 days prior and retained oldest 49 days prior: reported age `49.0` instead of `80`.
- **Source-grounded issue:** Session age loses original first launch after history cap.
- **Proposed change (not implemented):** Persist durable first-seen timestamp separately from capped history; migrate old data conservatively.
- **Evidence needed to close:** After >50 launches, true earliest known age stays stable; corrupt/empty history safe.

**[Source: `stealth_engine/engine.py:465-476`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L465-476)**

```python
 465 |                     current=fp_hash[:12],
 466 |                 )
 467 |             history.append(
 468 |                 {
 469 |                     "ts": round(_time.time(), 3),
 470 |                     "hash": fp_hash,
 471 |                     "diversity": self._config.fingerprint_diversity,
 472 |                 }
 473 |             )
 474 |             history = history[-self._FP_HISTORY_MAX :]
 475 |             path.parent.mkdir(parents=True, exist_ok=True)
 476 |             tmp = path.with_suffix(".json.tmp")
```

**[Source: `stealth_engine/engine.py:1572-1585`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L1572-1585)**

```python
1572 |         import json as _json
1573 | 
1574 |         path = Path(self._session.profile_dir) / "fingerprint_history.json"
1575 |         try:
1576 |             if not path.exists():
1577 |                 return None
1578 |             data = _json.loads(path.read_text(encoding="utf-8"))
1579 |             if not data:
1580 |                 return None
1581 |             first_ts = float(data[0].get("ts", 0))
1582 |             if first_ts <= 0:
1583 |                 return None
1584 |             return round((time.time() - first_ts) / 86400.0, 3)
1585 |         except Exception:
```

<a id="f-19"></a>
### F-19 — Per-profile log_level configuration is not applied by engine

- **Current P-04 code status (post-patch, overrides historical OPEN baseline):** PARTIAL: per-profile engine launch event gating added, module-level legacy logs not covered; full isolation pending (09). [Code commit](https://gitlab.com/ivibtools/stealth-engine/-/commit/997e5dd5087d4e366dc573f561e2e9ac3a063520), [post-patch evidence](09-P04-VERIFICATION-EVIDENCE.md).

- **Severity:** `Medium`; **assigned phase:** `P-04`; **status:** `OPEN — baseline`.
- **Earlier controlled verification:** Source-wide reference scan: `log_level` occurs only in ProfileConfig definition/docstring; `configure_logging` only declared in utils/logging.py, not called in engine modules.
- **Source-grounded issue:** Profile log_level not wired into engine.
- **Proposed change (not implemented):** Define and implement per-profile log filtering semantics without changing unrelated profiles or global handlers unexpectedly.
- **Evidence needed to close:** Two profiles with different levels produce isolated expected output; duplicate handler prevention and secrets redaction.

**[Source: `stealth_engine/config.py:143-149`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L143-149)**

```python
 143 |     record_har_path: str | None = None
 144 |     record_har_content: str | None = None
 145 |     record_video_dir: str | None = None
 146 |     js_noise: bool = False
 147 |     extra_headers: dict[str, str] = Field(default_factory=dict)
 148 |     log_level: str = "INFO"
 149 |     schema_version: str = "1"
```

**[Source: `stealth_engine/utils/logging.py:13-34`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/utils/logging.py#L13-34)**

```python
  13 | def configure_logging(level: str = "INFO", json_mode: bool = False) -> None:
  14 |     """Configure the loguru logger for stealth_engine.
  15 | 
  16 |     Removes loguru's default handler and registers a single stderr handler.
  17 |     Calling this function more than once is a no-op after the first call.
  18 | 
  19 |     Args:
  20 |         level: Minimum log level to emit (e.g. "DEBUG", "INFO", "WARNING").
  21 |         json_mode: When True, emit structured JSON lines via loguru serialisation.
  22 |     """
  23 |     global _configured  # noqa: PLW0603
  24 |     if _configured:
  25 |         return
  26 | 
  27 |     logger.remove()
  28 |     logger.add(
  29 |         sys.stderr,
  30 |         level=level.upper(),
  31 |         serialize=json_mode,
  32 |         enqueue=False,
  33 |     )
  34 |     _configured = True
```

## Unsupported and conditional behaviors (tracked, not inflated into defect count)

Source code indicates six capabilities are deliberately unsupported, conditional or not integrated; they must not be marked implemented simply because the public API exists.

| ID | Current source-confirmed condition | Phase decision | Exact source |
|---|---|---|---|
| U-01 | Sync session helper methods raise `AutomationError`; async variants are provided | P-01: preserve clear contract, only add support with approved scope | [`stealth_engine/engine.py:862-875`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L862-875), [`stealth_engine/engine.py:908-922`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L908-922) |
| U-02 | Video recording option is accepted in config but rejected for Firefox | P-05: keep unsupported with explicit acceptance test; no speculative implementation | [`stealth_engine/engine.py:666-687`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L666-687) |
| U-03 | CDP requested via `new_cdp_session`, wrapped as `AutomationError` on backend failure | P-05: real backend capability decision; unsupported until proven | [`stealth_engine/engine.py:1684-1695`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L1684-1695) |
| U-04 | Additional context requires `ctx.browser` present | P-01: test / document conditional behavior; avoid promise | [`stealth_engine/engine.py:1719-1730`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L1719-1730) |
| U-05 | Engine constructs one-proxy pool from `ProfileConfig.proxy`; standalone manager accepts multiples | P-03: document separate APIs; integration extension needs approval | [`stealth_engine/engine.py:216-223`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L216-223) |
| U-06 | Runner timeout only wraps `task_fn`, not launch or cleanup | P-05: decide if public contract should remain task-only; end-to-end timeout not promised | [`stealth_engine/orchestrator.py:384-395`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/orchestrator.py#L384-395), [`stealth_engine/orchestrator.py:434-443`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/orchestrator.py#L434-443) |

## Evidence vs release restrictions

- A source excerpt demonstrates an executable branch, but does **not** establish a successful production Camoufox session.
- A simulated proxy, fake context or Node canvas double is evidence only for the stated controlled path.
- Current source has **no tracked user/admin GUI implementation** to test. Count of code-evidenced UI-specific failures = 0; this is **not** a UI pass certification.
- Any proposed change must enter only its designated `P-0x` scope and be accepted by tests + independent diff review; unproven or disputed claims remain `UNVERIFIED`.


## 2026-11-16 P-01 source patch verification (append-only update)

- **Patch commit:** [`9638c789c7b06def4b51a54583bd728ee42e746b`](https://gitlab.com/ivibtools/stealth-engine/-/commit/9638c789c7b06def4b51a54583bd728ee42e746b); source baseline remains `a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`.
- **F-01, F-02, F-06:** `PATCH APPLIED + ISOLATED OFFLINE REGRESSIONS PASS`; **real Camoufox/browser acceptance NOT VERIFIED**. Not certified production-fixed.
- **U-01:** `BrowserSession.new_page()` and `.save_state()` still reject sync use; asynchronous variants remain the contract. **No new public sync helper introduced.**
- **U-04:** `new_context()` remains conditional on `ctx.browser` existing; the missing-browser error path was tested. Success on a real Camoufox persistent context is **NOT VERIFIED**.
- **Focused run:** Python 3.13; `PYTHONPATH=/mnt/data/stealth_audit_workspace python /mnt/data/stealth_phase01_test_shim/run_tests.py`; `15 tests / 15 passed`, exit `0` (including 9 new P-01 scenarios and 6 adjacent regressions). Test runner injected a **test-only browserforge import stub** because browserforge was unavailable; Camoufox used local fake async contexts. No external browser, network, real proxy, production session or integration test was executed.
- **Reproduction boundary:** The assertions demonstrate owned worker loop alive until close, awaited first page, cancellation/emergency cleanup, preserved typed error after proxy cleanup failure, lock removal, and U-01/U-04 negative paths. They **do not** prove a real backend's stability, actual anti-detection behavior or cross-loop Playwright Page usage.
- **Source diff verification:** Only `stealth_engine/engine.py` lifecycle/initial-page/emergency-cleanup functions plus targeted `tests/test_forensic_regressions.py` changed; original `tests/test_bugfix.py` and other runtime modules remained unchanged. CRLF file line endings preserved. See phase log `03`.

**[Verified post-patch source: `stealth_engine/engine.py:258-298`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/stealth_engine/engine.py#L258-298)**

```python
 258 |         # A live async browser cannot survive asyncio.run(): that helper
 259 |         # closes its loop before returning the session (F-01).  Keep one
 260 |         # owned loop running until BrowserSession.close()/aclose().
 261 |         import threading
 262 | 
 263 |         worker_loop = asyncio.new_event_loop()
 264 |         ready = threading.Event()
 265 | 
 266 |         def _loop_worker() -> None:
 267 |             asyncio.set_event_loop(worker_loop)
 268 |             ready.set()
 269 |             try:
 270 |                 worker_loop.run_forever()
 271 |             finally:
 272 |                 try:
 273 |                     worker_loop.run_until_complete(worker_loop.shutdown_asyncgens())
 274 |                     worker_loop.run_until_complete(worker_loop.shutdown_default_executor())
 275 |                 finally:
 276 |                     worker_loop.close()
 277 |                     asyncio.set_event_loop(None)
 278 | 
 279 |         worker = threading.Thread(
 280 |             target=_loop_worker,
 281 |             name="stealth-engine-sync-session",
 282 |             daemon=True,
 283 |         )
 284 |         try:
 285 |             worker.start()
 286 |             ready.wait()
 287 |             result = asyncio.run_coroutine_threadsafe(self.alaunch(), worker_loop).result()
 288 |         except BaseException:
 289 |             if worker.is_alive():
 290 |                 worker_loop.call_soon_threadsafe(worker_loop.stop)
 291 |                 worker.join()
 292 |             else:
 293 |                 worker_loop.close()
 294 |             raise
 295 | 
 296 |         result._sync_loop = worker_loop
 297 |         result._sync_thread = worker
 298 |         return result
```

**[Verified post-patch source: `stealth_engine/engine.py:429-445`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/stealth_engine/engine.py#L429-445)**

```python
 429 |             # k) Wrap in BrowserSession and ensure an actual first Page.
 430 |             # Empty persistent contexts require awaiting new_page() (F-02).
 431 |             stage = "wrap"
 432 |             session_obj = BrowserSession(
 433 |                 ctx=playwright_ctx,
 434 |                 ctx_handle=ctx_handle,
 435 |                 session=session,
 436 |                 proxy_manager=self._proxy_manager,
 437 |                 config=cfg,
 438 |             )
 439 |             stage = "initial_page"
 440 |             if session_obj.page is None:
 441 |                 await session_obj.new_page_async()
 442 | 
 443 |             # Fingerprint history is written only after a fully usable
 444 |             # session has been created; failed page setup is not a launch.
 445 |             self._record_fingerprint()
```

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

**[Verified post-patch source: `stealth_engine/engine.py:1009-1020`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/stealth_engine/engine.py#L1009-1020)**

```python
1009 |                 details={"stage": "close", "reason": "running event loop detected"},
1010 |             )
1011 | 
1012 |         if self._sync_loop is not None:
1013 |             # Dispatch teardown onto the SAME loop that launched Camoufox.
1014 |             try:
1015 |                 future = asyncio.run_coroutine_threadsafe(self.aclose(), self._sync_loop)
1016 |                 future.result()
1017 |             finally:
1018 |                 self._stop_sync_loop()
1019 |             return
1020 | 
```

**[Verified post-patch source: `stealth_engine/engine.py:1065-1081`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/stealth_engine/engine.py#L1065-1081)**

```python
1065 |     async def aclose(self) -> None:
1066 |         """Close the browser session asynchronously.
1067 | 
1068 |         Async counterpart to :meth:`close`.  Idempotent.  Sessions started
1069 |         via sync ``launch()`` are closed on their owning worker loop.
1070 |         """
1071 |         if self._sync_loop is not None and asyncio.get_running_loop() is not self._sync_loop:
1072 |             try:
1073 |                 await asyncio.wrap_future(
1074 |                     asyncio.run_coroutine_threadsafe(self.aclose(), self._sync_loop)
1075 |                 )
1076 |             finally:
1077 |                 await asyncio.to_thread(self._stop_sync_loop)
1078 |             return
1079 |         if self._closed:
1080 |             return
1081 |         self._closed = True
```


**Phase closure:** `P-01 = CODE PATCH APPLIED, OFFLINE CHECKS PASS, LIVE ACCEPTANCE BLOCKED`. 16 other audit findings remain untouched; 4 future phase code patches are not started. Do not move P-01 to fully accepted without an authorized real-browser test with installed pinned dependencies.

## P-02 aggregate update (2026-11-16)

- Current post-patch source: [e4c60c11](https://gitlab.com/ivibtools/stealth-engine/-/commit/e4c60c11c62d4fcef0f8892ae484014f4324659f). Initial source patch: [`cb06b63b`](https://gitlab.com/ivibtools/stealth-engine/-/commit/cb06b63b10130e99c28747a95837ab901ae42dfc); second P-02 commit restores the original CRLF line endings without changing program AST.
- **F-07/F-08/F-09/F-18:** P-02 offline reproduced/fixed; 18 new scoped negative/regression tests and 17 adjacent P-01/age/save-state tests = **35/35 pass** on Linux Python 3.13 with browserforge/Camoufox test-only import doubles. No real browser, Windows or multi-version simultaneous client test.
- Project-wide: **7/19 findings patch-applied offline; 12 unpatched** (P-03..05). Full production acceptance = **0/5 phases**; patches applied = **2/5**.
- Baseline `OPEN` findings and source code blocks above are historical evidence, not statements about the post-P02 source.

## P-03 aggregate patch record (2026-11-16)

- Source patch commit: [`b2d1884a`](https://gitlab.com/ivibtools/stealth-engine/-/commit/b2d1884a8e7534d28f492d9f3274eb17c5551b3a), pre-P03 head: `c490501d175fd1a3bd164ecf855594c0573279a1`; original immutable baseline: `a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`.
- F-05, F-11, F-12, F-14, F-15: offline code patch + local SOCKS5 and SOCKS4a wire-level mock verified; **59/59 focused/adjacent tests PASS** Python 3.13 Linux. No external SOCKS or HTTPS-tunneled production GeoIP test, real Camoufox, WebRTC browser readback or Windows test.
- Status: **12/19 findings code-patched and offline-verified; 7 unpatched** in P-04 (5) + P-05 (2). **3/5 phases code patched; 0/5 fully production-accepted.**
- **U-05:** Standalone ProxyManager pool and the engine's single-proxy profile contract remain unchanged; optional integration extension NOT approved/implemented.
- See [08-P03-VERIFICATION-EVIDENCE.md](08-P03-VERIFICATION-EVIDENCE.md) for post-patch source excerpts, reproducible local tests and limitations. Historical `OPEN` labels and code snippets in this document describe frozen pre-fix source only.

## P-04 historical-status overlay (2026-11-16, before P-05)

- **Current source commit:** [`997e5dd5`](https://gitlab.com/ivibtools/stealth-engine/-/commit/997e5dd5087d4e366dc573f561e2e9ac3a063520), parent/pre-P04 HEAD: `639f3a461973524155f39b645193e20b09416153`.
- **F-03/F-04/F-10/F-13/F-19:** five finding targets have in-scope source patch changes. F-03 browser-visible matching unverified; F-19 applies only to new scoped engine logs, not existing global logging statements. **Do not count as fully production-closed.**
- **Verification:** 61/61 focused offline tests PASS; 6 existing Feature Y config tests run separately, 4 pass / **2 fail** because default saved secrets no longer roundtrip. These failures are unresolved until an approved contract test update; leaving default exports plaintext is not acceptable.
- **Status counts:** 17/19 findings code-addressed in P-01..P-04 (two require further acceptance); P-05 F-16/F-17 are unpatched; 4/5 phases code-patched, **0/5 production accepted**.
- **Exact code proof, test lines, compatibility breaks, blockers:** [09-P04-VERIFICATION-EVIDENCE.md](09-P04-VERIFICATION-EVIDENCE.md).


## P-05 verified source delta — 2026-11-16 (current)

- **Code commit:** [`38b44068`](https://gitlab.com/ivibtools/stealth-engine/-/commit/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd); parent / phase-start head `4a1512ff7c95eafba1d951eb73eb194c66d74977`; immutable original source baseline unchanged.
- **F-16 (Medium):** `_js_noise_init_script` resets per-readback seeded PRNG state inside `_perturb`; identical source pixels are stable across repeated canvas `toDataURL`, `getImageData`, WebGL1/2 mock readbacks. **Opt-in experimental JS noise remains detectable; real browser readback NOT VERIFIED.** [Current proof](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L85-129).
- **F-17 (Medium):** `block_trackers` extracts `urlsplit(request.url).hostname`, normalizes case/trailing dot and uses exact-host or `'.'+domain` suffix. Benign query/path/lookalike does not trigger abort; actual tracker host/subdomain does. Malformed URL authority continues, registration failure remains `AutomationError`. `extra_domains` now interpreted as domain names (`*.domain` accepted), not arbitrary URL substrings. [Current proof](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L1670-1717).
- **Focused offline tests:** **71/71 PASS**, including **10 new P-05 tests** and 61 adjacent prior tests; Python 3.13 / Node 22 / Linux, with browserforge/Camoufox import-only stubs. [New tests](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/tests/test_forensic_regressions.py#L1460-1619).
- **Full suite with import stubs:** **235 passed, 8 failed, 4 skipped, 32 subtests passed**. Two old plaintext-secret JSON/YAML expectations conflict with P-04 secure default. Three failures stem from absent real fingerprint/browser dependency stubs (`browserforge` x2, `camoufox.fingerprints.Screen` x1); three `tests/test_meta.py::DriftDetectionTests` failures concern fingerprint-history path/cap and require separate root-cause/contract review. **These 8 failures remain unresolved; NOT production-ready.**
- **Conditional U-02/U-03/U-06:** current video rejection, CDP error mapping and `BulkRunner` task-only timeout retained. Mock/offline contract tests pass; no feature support claimed. **U-05 remains conditional, unchanged.**
- **Scope check:** only `stealth_engine/engine.py` (`_js_noise_init_script`, `BrowserSession.block_trackers`) and additive `tests/test_forensic_regressions.py`; all P-01–P-04 function ASTs and other tracked source modules unchanged. Full details [10-P05-VERIFICATION-EVIDENCE.md](10-P05-VERIFICATION-EVIDENCE.md).
- **Counters:** 5/5 code-phase patches applied; 19/19 finding targets addressed in source; **0/5 fully production accepted**. The 19/19 figure is NOT an assertion that 19/19 live features work.
