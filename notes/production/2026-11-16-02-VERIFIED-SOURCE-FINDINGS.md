# Production Source Forensic Audit — Verified Findings

- **Project:** `ivibtools/stealth-engine`
- **Audited immutable GitLab revision:** `6255383cac9f29d64bf9ee5957c77ee26ccd7993` (main at audit start)
- **Audit date:** 2026-11-16 UTC
- **Scope:** Python runtime / APIs / configuration / backend and observable deterministic behavior. No prior Markdown was used as audit evidence.
- **Counts:** **19 source-evidenced findings** — Critical 1, High 11, Medium 7. These are **not** a claim that all 19 were reproduced in a live Camoufox browser.
- **Confidence scheme:** `Source + probe` means direct source path and controlled local reproduction; `Source + analysis` means direct source path and a deterministic control-flow fact, with live effects explicitly unverified.
- **Boundary:** Real-browser, proxy-exit, WebRTC, anti-detection efficacy, external services and UI usability were **not** live-tested. See companion coverage and verification reports.

> Every snippet below was extracted mechanically from the audited `.py` source lines. Reference URLs pin the original source SHA; prior `README`, roadmap, feature-note and audit Markdown files were intentionally not used as evidence. Statements about consequences outside a local probe are labeled as limits, not as witnessed production outcomes.

## Findings register

| ID | Severity | Verified defect / control-path gap |
|---|---|---|
| F-01 | Critical | Sync launch returns after its event loop is closed |
| F-02 | High | Empty initial context stores an unawaited page coroutine |
| F-03 | High | Generated identity fields are not forwarded to browser launch |
| F-04 | High | Persisted seeds override subsequently changed locale/timezone config |
| F-05 | High | SOCKS proxy validation uses HTTP traffic, not a SOCKS handshake |
| F-06 | High | Launch failure cleanup omits proxy manager closure |
| F-07 | High | 24-hour age overrides live-process lock ownership |
| F-08 | High | A non-owner can release another manager's profile lock |
| F-09 | High | Force reset deletes an active profile without ownership check |
| F-10 | High | Config export exposes proxy credentials in default-created files |
| F-11 | High | Invalid proxy line exception can include raw credentials |
| F-12 | Medium | Proxy URL validator accepts scheme-only endpoint |
| F-13 | Medium | Built-in mobile-android preset cannot validate |
| F-14 | Medium | Geo auto settings are incorrectly reported inconsistent |
| F-15 | High | Direct WebRTC IP setting uses interface/private address, not internet public IP |
| F-16 | Medium | Experimental JS noise changes identical canvas readbacks |
| F-17 | Medium | Tracker blocking matches full URL substrings, not hostname |
| F-18 | Medium | Session age stops reflecting first launch after history cap |
| F-19 | Medium | Per-profile log_level configuration is not applied by engine |

---

### F-01 — Sync launch returns after its event loop is closed

**Classification:** Critical. **Source-grounded observation:** `launch()` returns the async Playwright/Camoufox session after `asyncio.run()` has closed the launch loop. The advertised synchronous workflow therefore does not preserve the event loop that created browser resources. Actual Camoufox behavior was not measured.

**Controlled evidence:** Controlled subclass probe: `loop_closed_before_session_use=true`. This is a verified lifecycle invariant, not a live-browser failure log.

**Exact source references:**

[`stealth_engine/engine.py:244-256`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L244-256)

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

[`stealth_engine/engine.py:950-975`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L950-975)

```python
 950 |         self._closed = True
 951 | 
 952 |         # Merge state save + camoufox teardown + proxy cleanup into ONE
 953 |         # asyncio.run() call so they share the same event loop and the
 954 |         # aiohttp session is closed on the loop it was created on.
 955 |         _proxy_mgr = self._proxy_manager
 956 | 
 957 |         async def _async_close() -> None:
 958 |             # BF-01: save state via the async storage_state() call.
 959 |             try:
 960 |                 await self.save_state_async()
 961 |             except Exception as exc:
 962 |                 _log.warning("close: save_state_async failed", reason=str(exc))
 963 |             try:
 964 |                 await self._ctx_handle.__aexit__(None, None, None)
 965 |             except Exception as exc:
 966 |                 _log.warning("close: ctx_handle.__aexit__ failed", reason=str(exc))
 967 |             finally:
 968 |                 if _proxy_mgr is not None:
 969 |                     try:
 970 |                         await _proxy_mgr.aclose()
 971 |                     except Exception as exc:
 972 |                         _log.warning("close: proxy_manager.aclose() failed", reason=str(exc))
 973 | 
 974 |         try:
 975 |             asyncio.run(_async_close())
```

---

### F-02 — Empty initial context stores an unawaited page coroutine

**Classification:** High. **Source-grounded observation:** When `ctx.pages` is empty, `BrowserSession.__init__` stores `ctx.new_page()` without awaiting; under async Playwright this is a coroutine, not a Page.

**Controlled evidence:** Async fake context with no pages: `page_is_coroutine=true`. A live persistent context with zero pages was not exercised.

**Exact source references:**

[`stealth_engine/engine.py:805-811`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L805-811)

```python
 805 | 
 806 |         # Expose the initial page (persistent context opens with one page).
 807 |         try:
 808 |             pages = ctx.pages
 809 |             self._page: PlaywrightPage = pages[0] if pages else ctx.new_page()
 810 |         except Exception:
 811 |             self._page = None  # type: ignore[assignment]
```

[`stealth_engine/engine.py:839-855`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L839-855)

```python
 839 |     async def new_page_async(self) -> PlaywrightPage:
 840 |         """Open and return a new page in this session's context (async).
 841 | 
 842 |         BF-04/B-24: the underlying context is async — ``new_page()`` is a
 843 |         coroutine and must be awaited.  The initial page is available
 844 |         synchronously via :attr:`page`.
 845 | 
 846 |         Returns:
 847 |             A new Playwright ``Page`` object.
 848 | 
 849 |         Raises:
 850 |             AutomationError: If the context is closed or page creation fails.
 851 |         """
 852 |         try:
 853 |             page = await self._ctx.new_page()
 854 |             self._page = page
 855 |             return page
```

---

### F-03 — Generated identity fields are not forwarded to browser launch

**Classification:** High. **Source-grounded observation:** The generated fingerprint contains UA, viewport, screen, platform, device_memory and color_scheme, but `_build_launch_kwargs()` only forwards locale/timezone and separately configured Camoufox seed/options. No code maps those generated fields into browser launch settings. This is an identity-application/integration gap; Camoufox may still generate its own identity.

**Controlled evidence:** Controlled `_build_launch_kwargs` call: excluded fields `user_agent`, `viewport`, `screen`, `platform`, `device_memory`, `color_scheme`.

**Exact source references:**

[`stealth_engine/engine.py:613-632`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L613-632)

```python
 613 |         kwargs: dict[str, Any] = {
 614 |             "os": cfg.os,
 615 |             "headless": cfg.headless,
 616 |             "persistent_context": True,
 617 |             "user_data_dir": self._session.user_data_dir,
 618 |             "locale": fp.get("locale", "en-US"),
 619 |         }
 620 | 
 621 |         # PF-01/B-27: camoufox patch properties (seeds, webrtc IP,
 622 |         # hardwareConcurrency, timezone) are CONFIG-dict keys — they
 623 |         # must go inside ``config``, never as top-level kwargs (which
 624 |         # playwright's launch_persistent_context rejects with TypeError).
 625 |         # Verified against camoufox properties.json: canvas:seed,
 626 |         # audio:seed, fonts:spacing_seed, webrtc:ipv4, timezone and
 627 |         # navigator.hardwareConcurrency are all valid uint/str keys.
 628 |         launch_config: dict[str, Any] = {
 629 |             "canvas:seed": seeds["canvas"],
 630 |             "audio:seed": seeds["audio"],
 631 |             "fonts:spacing_seed": seeds["fonts"],
 632 |         }
```

[`stealth_engine/engine.py:689-695`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L689-695)

```python
 689 |         # PH-14: camoufox fingerprint-depth options.
 690 |         if cfg.hardware_concurrency is not None:
 691 |             launch_config["navigator.hardwareConcurrency"] = cfg.hardware_concurrency
 692 |         if cfg.webgl_config is not None:
 693 |             kwargs["webgl_config"] = cfg.webgl_config
 694 |         if cfg.fonts is not None:
 695 |             kwargs["fonts"] = list(cfg.fonts)
```

[`stealth_engine/engine.py:707-719`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L707-719)

```python
 707 |         # PH-11: when Camoufox geoip is disabled (Mode A always; Mode B with
 708 |         # geoip=False), pass the resolved timezone via the `config` dict so
 709 |         # the browser timezone matches fp["timezone_id"] instead of silently
 710 |         # falling back to the host OS timezone.  When geoip=True Camoufox
 711 |         # derives timezone from the exit IP itself — do NOT override it.
 712 |         if kwargs.get("geoip") is False and fp.get("timezone_id"):
 713 |             launch_config["timezone"] = fp["timezone_id"]
 714 |             # PF-04: the manual timezone config is intentional (Mode A has
 715 |             # no geoip source) — silence camoufox's LeakWarning for this
 716 |             # launch via its designed escape hatch.
 717 |             kwargs["i_know_what_im_doing"] = True
 718 |         if launch_config:
 719 |             kwargs["config"] = launch_config
```

[`stealth_engine/identity.py:429-445`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/identity.py#L429-445)

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
 439 |             - ``platform`` (:class:`str`)
 440 |             - ``hardware_concurrency`` (:class:`int`)
 441 |             - ``device_memory`` (:class:`int`)
 442 |             - ``color_scheme`` (:class:`str`)
 443 |             - ``reduced_motion`` (:class:`str`)
 444 |             - ``is_mobile`` (:class:`bool`)
 445 |             - ``has_touch`` (:class:`bool`)
```

---

### F-04 — Persisted seeds override subsequently changed locale/timezone config

**Classification:** High. **Source-grounded observation:** Existing valid `seeds.json` is returned as-is. During launch, when no proxy GeoInfo is available, locale/timezone values are taken from those persisted seeds, overwriting newly configured values.

**Controlled evidence:** Same profile seeded `en-US`/`UTC`, then configured `fr-FR`/`Europe/Paris`: reused seeds remain `en-US`/`UTC`.

**Exact source references:**

[`stealth_engine/identity.py:486-505`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/identity.py#L486-505)

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
 504 |                 )
 505 | 
```

[`stealth_engine/engine.py:326-333`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L326-333)

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

---

### F-05 — SOCKS proxy validation uses HTTP traffic, not a SOCKS handshake

**Classification:** High. **Source-grounded observation:** ProxyManager uses aiohttp ClientSession `get(..., proxy=proxy_url)` for GeoIP. With tested aiohttp, a `socks5://` proxy listener received an HTTP GET request rather than a SOCKS5 greeting. Browser-side proxy operation was not tested.

**Controlled evidence:** Local loopback server captured first request bytes: `GET http://example.invalid/ HTTP/1.1`, not SOCKS5 greeting.

**Exact source references:**

[`stealth_engine/proxy.py:320-335`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/proxy.py#L320-335)

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

[`stealth_engine/proxy.py:563-578`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/proxy.py#L563-578)

```python
 563 |     def _build_proxy_url(proxy: ProxyConfig) -> str:
 564 |         """Return the proxy server URL with NO credentials embedded.
 565 | 
 566 |         Credentials are passed separately via :meth:`_build_proxy_auth` to
 567 |         prevent the password appearing in any URL string that aiohttp might
 568 |         log on connection errors.
 569 | 
 570 |         Args:
 571 |             proxy: Source proxy configuration.
 572 | 
 573 |         Returns:
 574 |             Credential-free proxy URL string.
 575 |         """
 576 |         return ProxyManager._proxy_parts(proxy)[0]
 577 | 
 578 |     @staticmethod
```

[`stealth_engine/config.py:39-64`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/config.py#L39-64)

```python
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
  63 | 
  64 | 
```

---

### F-06 — Launch failure cleanup omits proxy manager closure

**Classification:** High. **Source-grounded observation:** `alaunch()` failure handlers call `_emergency_cleanup(ctx_handle, session)`; that helper closes context and releases lock but has no proxy-manager close call, even though `pick_healthy()` can have created an aiohttp session.

**Controlled evidence:** Injected proxy manager + failed launch: `proxy_close_called_after_exception=false`, lock released. No external network used.

**Exact source references:**

[`stealth_engine/engine.py:414-424`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L414-424)

```python
 414 | 
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

[`stealth_engine/engine.py:723-746`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L723-746)

```python
 723 |     @staticmethod
 724 |     async def _emergency_cleanup(
 725 |         ctx_handle: Any | None,
 726 |         session: SessionManager,
 727 |     ) -> None:
 728 |         """Best-effort cleanup after a failed launch.
 729 | 
 730 |         Closes the camoufox context handle and releases the session lock.
 731 |         Errors during cleanup are logged but never re-raised.
 732 | 
 733 |         Args:
 734 |             ctx_handle: The camoufox async context manager handle, or
 735 |                 ``None`` if launch failed before it was created.
 736 |             session: The :class:`SessionManager` whose lock must be freed.
 737 |         """
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

---

### F-07 — 24-hour age overrides live-process lock ownership

**Classification:** High. **Source-grounded observation:** A lock is treated as stale when its age exceeds 24 hours, even when `_pid_alive(pid)` is true. A long-running live session can therefore have its lock removed and replaced.

**Controlled evidence:** Temp lock with live current PID and timestamp older than 24 hours: second manager reacquired lock successfully.

**Exact source references:**

[`stealth_engine/session.py:275-305`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/session.py#L275-305)

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

---

### F-08 — A non-owner can release another manager's profile lock

**Classification:** High. **Source-grounded observation:** `release_lock()` unlinks `.lock` unconditionally, without ownership token/PID check.

**Controlled evidence:** Two SessionManager instances for same profile; the second never acquired a lock but `release_lock()` deleted the first instance’s lock.

**Exact source references:**

[`stealth_engine/session.py:307-317`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/session.py#L307-317)

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

---

### F-09 — Force reset deletes an active profile without ownership check

**Classification:** High. **Source-grounded observation:** `force_reset()` calls the unguarded release and removes the entire profile directory regardless of a live owner. This is a destructive control-path risk; deletion is explicit behavior but has no live-session safety guard.

**Controlled evidence:** One SessionManager held lock; second instance called `force_reset()` and active profile directory disappeared.

**Exact source references:**

[`stealth_engine/session.py:323-336`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/session.py#L323-336)

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

---

### F-10 — Config export exposes proxy credentials in default-created files

**Classification:** High. **Source-grounded observation:** `save_json()` and `save_yaml()` serialize full `model_dump` (including proxy secret values) without explicitly restricting file permissions. Permissions depend on filesystem/umask.

**Controlled evidence:** Linux temp directory under default umask: JSON file mode `0644`, password present in plaintext. This result is environment-specific.

**Exact source references:**

[`stealth_engine/config.py:249-268`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/config.py#L249-268)

```python
 249 |     def save_json(self, path: str | Path) -> None:
 250 |         """Write this config to ``path`` as pretty-printed JSON.
 251 | 
 252 |         Uses ``model_dump(mode="json")`` so the output is plain JSON types.
 253 |         The file is written atomically (``.tmp`` then ``os.replace``).
 254 | 
 255 |         Args:
 256 |             path: Destination file path.
 257 |         """
 258 |         import os
 259 | 
 260 |         p = Path(path)
 261 |         tmp = p.with_suffix(p.suffix + ".tmp")
 262 |         tmp.write_text(
 263 |             json.dumps(
 264 |                 self.model_dump(mode="json"), indent=2, sort_keys=True
 265 |             )
 266 |             + "\n",
 267 |             encoding="utf-8",
 268 |         )
```

[`stealth_engine/config.py:288-307`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/config.py#L288-307)

```python
 288 |     def save_yaml(self, path: str | Path) -> None:
 289 |         """Write this config to ``path`` as YAML.
 290 | 
 291 |         PyYAML is imported lazily so ``import stealth_engine`` does not
 292 |         require it.  The dump uses ``yaml.safe_dump`` (no Python-specific
 293 |         tags) and sorted keys for deterministic output.
 294 | 
 295 |         Args:
 296 |             path: Destination file path.
 297 |         """
 298 |         import os
 299 | 
 300 |         import yaml
 301 | 
 302 |         p = Path(path)
 303 |         tmp = p.with_suffix(p.suffix + ".tmp")
 304 |         tmp.write_text(
 305 |             yaml.safe_dump(
 306 |                 self.model_dump(mode="json"), sort_keys=True
 307 |             ),
```

[`stealth_engine/config.py:212-247`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/config.py#L212-247)

```python
 212 | 
 213 |     def to_public_dict(self) -> dict:
 214 |         """Return a serialisable representation with proxy secrets redacted.
 215 | 
 216 |         Excludes the raw proxy block and replaces username/password with
 217 |         ``"***"`` to prevent accidental secret exposure in logs or exports.
 218 | 
 219 |         Returns:
 220 |             Dict containing all fields except a raw proxy; proxy credentials
 221 |             are replaced with ``"***"`` if a proxy is configured.
 222 |         """
 223 |         base = self.model_dump(exclude={"proxy"})
 224 |         if self.proxy is not None:
 225 |             server, embedded_username, embedded_password = _split_proxy_credentials(
 226 |                 self.proxy.server
 227 |             )
 228 |             base["proxy"] = {
 229 |                 "server": server,
 230 |                 "username": (
 231 |                     "***"
 232 |                     if self.proxy.username is not None or embedded_username is not None
 233 |                     else None
 234 |                 ),
 235 |                 "password": (
 236 |                     "***"
 237 |                     if self.proxy.password is not None or embedded_password is not None
 238 |                     else None
 239 |                 ),
 240 |             }
 241 |         else:
 242 |             base["proxy"] = None
 243 |         return base
 244 | 
 245 |     # ------------------------------------------------------------------
 246 |     # File serialisation (Feature Y: JSON/YAML import-export)
 247 |     # ------------------------------------------------------------------
```

---

### F-11 — Invalid proxy line exception can include raw credentials

**Classification:** High. **Source-grounded observation:** `_parse_proxy_line` stores the first 80 characters of the original line in `ProxyError.details`; `StealthEngineError.__str__` includes the details.

**Controlled evidence:** `_parse_proxy_line("secret-user:secret-pass@",1)` raised ProxyError whose string contains `secret-pass`.

**Exact source references:**

[`stealth_engine/proxy.py:643-668`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/proxy.py#L643-668)

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
 656 | 
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

[`stealth_engine/exceptions.py:20-27`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/exceptions.py#L20-27)

```python
  20 |         self.message: str = message
  21 |         self.details: dict | None = details
  22 | 
  23 |     def __str__(self) -> str:
  24 |         """Return message with compact details repr when present."""
  25 |         if self.details:
  26 |             return f"{self.message} | details={self.details!r}"
  27 |         return self.message
```

---

### F-12 — Proxy URL validator accepts scheme-only endpoint

**Classification:** Medium. **Source-grounded observation:** `ProxyConfig._validate_server()` checks URL prefix only, not hostname or port syntax; clearly invalid `http://` passes config validation and fails later in transport.

**Controlled evidence:** `ProxyConfig(server="http://")` succeeded in a local pure-Python probe.

**Exact source references:**

[`stealth_engine/config.py:39-63`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/config.py#L39-63)

```python
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
  63 | 
```

---

### F-13 — Built-in mobile-android preset cannot validate

**Classification:** Medium. **Source-grounded observation:** `mobile-android` preset sets `os="android"` while `ProfileConfig.os` only accepts `windows`, `macos`, `linux`.

**Controlled evidence:** `ProfileConfig.preset("mobile-android", profile_name="probe", user_data_dir="/tmp/probe")` raised pydantic ValidationError for `os`.

**Exact source references:**

[`stealth_engine/config.py:124-126`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/config.py#L124-126)

```python
 124 |     profile_name: str
 125 |     os: Literal["windows", "macos", "linux"] = "windows"
 126 |     user_data_dir: str
```

[`stealth_engine/config.py:354-359`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/config.py#L354-359)

```python
 354 |     "mobile-android": {
 355 |         "os": "android",
 356 |         "locale": "en-US",
 357 |         "timezone": "America/Los_Angeles",
 358 |         "headless": True,
 359 |     },
```

[`stealth_engine/config.py:368-380`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/config.py#L368-380)

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
 380 | 
```

---

### F-14 — Geo auto settings are incorrectly reported inconsistent

**Classification:** Medium. **Source-grounded observation:** `validate_geo_consistency()` compares resolved locale/timezone directly to literal config values; `auto` sentinel is not treated as deferred and always mismatches normal resolved values.

**Controlled evidence:** US GeoInfo with `locale=en-US`, `timezone_id=America/New_York` + config `locale=auto`, `timezone=auto` returned `consistent=false`, both mismatches.

**Exact source references:**

[`stealth_engine/geo.py:130-144`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/geo.py#L130-144)

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

---

### F-15 — Direct WebRTC IP setting uses interface/private address, not internet public IP

**Classification:** High. **Source-grounded observation:** `_resolve_host_ip()` uses the UDP socket’s local `getsockname()[0]` or host DNS fallback. It is used as `webrtc:ipv4`, despite comments describing public host IP. The actual live browser WebRTC output was not measured.

**Controlled evidence:** On isolated audit host: method returned `172.26.39.156`, Python `ipaddress.is_global=false`.

**Exact source references:**

[`stealth_engine/engine.py:499-525`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L499-525)

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

[`stealth_engine/engine.py:640-645`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L640-645)

```python
 640 |             kwargs["geoip"] = False
 641 |             # Mode A: WebRTC advertises host IP (PH-03)
 642 |             if cfg.target_ip:
 643 |                 launch_config["webrtc:ipv4"] = cfg.target_ip
 644 |             else:
 645 |                 launch_config["webrtc:ipv4"] = self._resolve_host_ip()
```

[`stealth_engine/engine.py:484-496`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L484-496)

```python
 484 |     @staticmethod
 485 |     def _resolve_host_ip() -> str:
 486 |         """Resolve the actual host IP address for WebRTC in Mode A.
 487 | 
 488 |         Uses a best-effort UDP socket connection to a public DNS server
 489 |         (8.8.8.8:53) to determine the local IP that would be used for
 490 |         outbound connections. This matches the IP visible to remote
 491 |         servers without actually sending application data.
 492 | 
 493 |         Returns:
 494 |             The host IP address as a string (e.g. "203.0.113.10").
 495 | 
 496 |         Raises:
```

---

### F-16 — Experimental JS noise changes identical canvas readbacks

**Classification:** Medium. **Source-grounded observation:** The injected JS uses a mutable PRNG state advanced on every readback; identical canvases do not produce a stable readback within one page. This is an experimental opt-in feature (`js_noise=False` by default).

**Controlled evidence:** Executed generated init script against a Node.js canvas-shaped test double: `first_and_second_equal=false` on identical input. Not validated in Camoufox.

**Exact source references:**

[`stealth_engine/engine.py:84-99`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L84-99)

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

[`stealth_engine/engine.py:100-116`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L100-116)

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

---

### F-17 — Tracker blocking matches full URL substrings, not hostname

**Classification:** Medium. **Source-grounded observation:** Route compares `domain in request.url.lower()` on the entire URL, so a benign host can be blocked because its URL path/query mentions a tracker domain.

**Controlled evidence:** Fake route on `https://good.example.org/article?next=https://google-analytics.com/` was aborted.

**Exact source references:**

[`stealth_engine/engine.py:1544-1559`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L1544-1559)

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

---

### F-18 — Session age stops reflecting first launch after history cap

**Classification:** Medium. **Source-grounded observation:** Fingerprint history is truncated to most recent 50 entries, but `session_age_days()` uses the first retained entry as the original creation time.

**Controlled evidence:** Synthetic 51-entry history with oldest launch 80 days prior and retained oldest 49 days prior: reported age `49.0` instead of `80`.

**Exact source references:**

[`stealth_engine/engine.py:465-476`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L465-476)

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

[`stealth_engine/engine.py:1572-1585`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L1572-1585)

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

---

### F-19 — Per-profile log_level configuration is not applied by engine

**Classification:** Medium. **Source-grounded observation:** `ProfileConfig.log_level` is defined, but runtime source does not read it when constructing engine/session. `configure_logging` is a separate function with a global idempotency flag and is not called by the runtime path.

**Controlled evidence:** Source-wide reference scan: `log_level` occurs only in ProfileConfig definition/docstring; `configure_logging` only declared in utils/logging.py, not called in engine modules.

**Exact source references:**

[`stealth_engine/config.py:143-149`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/config.py#L143-149)

```python
 143 |     record_har_path: str | None = None
 144 |     record_har_content: str | None = None
 145 |     record_video_dir: str | None = None
 146 |     js_noise: bool = False
 147 |     extra_headers: dict[str, str] = Field(default_factory=dict)
 148 |     log_level: str = "INFO"
 149 |     schema_version: str = "1"
```

[`stealth_engine/utils/logging.py:13-34`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/utils/logging.py#L13-34)

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

## Important interpretation

- These 19 entries are distinct source-observable defects, safety/control risks or contract mismatches. The counts do **not** include unsupported-by-design API methods, deployment/CI verification gaps, or speculative external bypass/ban claims.
- Finding reproducibility describes the *tested branch or invariant*, not a claim of zero bugs elsewhere or complete production coverage.
- No source edits, infrastructure writes, live browser launches, customer/account actions, live proxy requests or external-site stealth tests were performed in this audit. Only the audit Markdown files are intended to be committed.
