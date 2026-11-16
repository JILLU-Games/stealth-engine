# Production Source Forensic Audit — Runtime Limits & Unsupported Paths

**Project:** `ivibtools/stealth-engine`  
**Audited source SHA:** `6255383cac9f29d64bf9ee5957c77ee26ccd7993`  
**Date:** 2026-11-16 UTC  
**Evidence basis:** Actual source `.py`, Python build metadata, programmatically executed isolated probes. **Not** read from prior Markdown.

## Test execution ledger

| Check | Observed outcome | Meaning |
|---|---|---|
| GitLab HEAD/tree | SHA `6255383cac9f29d64bf9ee5957c77ee26ccd7993`; 154 tracked files | Exact code revision identified |
| ZIP vs GitLab source blobs | 31 of 31 executable/config file blob hashes identical | Source excerpts refer to checked-in code |
| Python syntax | `compileall` exit 0 | Parse/bytecode compile passes; does not mean runtime works |
| Standard test execution | `pytest -q --disable-warnings --maxfail=1` stopped **during collection**: `ModuleNotFoundError: No module named 'browserforge'` from `identity.py:14` | **No pytest pass result**, no fabricated pass count |
| Dependencies in isolated audit environment | `camoufox=false`, `browserforge=false`, `tzlocal=false`; `playwright`, `pydantic`, `aiohttp`, `loguru`, `yaml`, `pytest` importable | Environment lacks full runtime dependencies; this is not proof project packaging omits them |
| Real browser smoke | Not executed; `tests/test_smoke.py:10-25` requires `STEALTH_SMOKE=1` and installed browser | Production Camoufox run **NOT VERIFIED** |
| Fingerprint canary | Not executed; `STEALTH_CANARY=1` is required | Cannot claim real identity consistency |
| Live geo IP / HTTP proxies | No external requests | Real proxy exit and geo quality **NOT VERIFIED** |
| Local SOCKS wire format | Loopback simulated SOCKS server received `GET http://example.invalid/ HTTP/1.1` | Proves tested aiohttp request path speaks HTTP to SOCKS URL; not a real provider response |
| JavaScript canvas patch | Node canvas-shaped test double: repeated identical readback changed | Shows generated script state behavior; not a Firefox/Camoufox performance test |
| GitLab CI pipelines | GitLab project pipelines listing returned none at start | No CI success can be claimed |

## Explicit unsupported/deferred API surfaces (not added to 19 defects)

### U-01 — Sync session helper methods deliberately raise

`new_page()`, `save_state()`, `human_move()`, `human_type()`, `human_scroll()` and `human_dwell()` explicitly throw `AutomationError` directing users to async variants. **Evidence:**

[`stealth_engine/engine.py:862-879`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L862-879)

```python
 862 |     def new_page(self) -> PlaywrightPage:
 863 |         """Sync page creation — unsupported on async contexts.
 864 | 
 865 |         BF-04/B-24: ``context.new_page()`` is a coroutine; it cannot be
 866 |         awaited from sync code.  Use ``await session.new_page_async()``
 867 |         or the already-open :attr:`page`.
 868 | 
 869 |         Raises:
 870 |             AutomationError: Always — directs caller to the async API.
 871 |         """
 872 |         raise AutomationError(
 873 |             "new_page() cannot run synchronously on an async browser "
 874 |             "context; use 'await session.new_page_async()' or session.page",
 875 |             details={"stage": "new_page", "reason": "async context"},
 876 |         )
 877 | 
 878 |     # ------------------------------------------------------------------
 879 |     # State persistence
```

[`stealth_engine/engine.py:908-927`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L908-927)

```python
 908 |     def save_state(self) -> None:
 909 |         """Sync storage-state export — unsupported on async contexts.
 910 | 
 911 |         BF-01: the camoufox context is asynchronous, so
 912 |         ``context.storage_state()`` is a coroutine that cannot be awaited
 913 |         from sync code.  Use ``await session.save_state_async()`` or let
 914 |         :meth:`aclose`/:meth:`close` persist state automatically.
 915 | 
 916 |         Raises:
 917 |             AutomationError: Always — directs caller to the async API.
 918 |         """
 919 |         raise AutomationError(
 920 |             "save_state() cannot run synchronously on an async browser "
 921 |             "context; use 'await session.save_state_async()'",
 922 |             details={"stage": "save_state", "reason": "async context"},
 923 |         )
 924 | 
 925 |     # ------------------------------------------------------------------
 926 |     # Close / cleanup
 927 |     # ------------------------------------------------------------------
```

[`stealth_engine/engine.py:1083-1090`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L1083-1090)

```python
1083 |             AutomationError: Always — directs caller to the async API.
1084 |         """
1085 |         raise AutomationError(
1086 |             "human_move() cannot run synchronously on an async browser "
1087 |             "context; use 'await session.ahuman_move(page, x, y)'",
1088 |             details={"stage": "human_move", "reason": "async context"},
1089 |         )
1090 | 
```

[`stealth_engine/engine.py:1099-1108`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L1099-1108)

```python
1099 |         Raises:
1100 |             AutomationError: Always — directs caller to the async API.
1101 |         """
1102 |         raise AutomationError(
1103 |             "human_type() cannot run synchronously on an async browser "
1104 |             "context; use 'await session.ahuman_type(page, selector, text)'",
1105 |             details={"stage": "human_type", "reason": "async context"},
1106 |         )
1107 | 
1108 |     def human_scroll(self, page: PlaywrightPage, dy: int) -> None:
```

[`stealth_engine/engine.py:1115-1126`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L1115-1126)

```python
1115 |             AutomationError: Always — directs caller to the async API.
1116 |         """
1117 |         raise AutomationError(
1118 |             "human_scroll() cannot run synchronously on an async browser "
1119 |             "context; use 'await session.ahuman_scroll(page, dy)'",
1120 |             details={"stage": "human_scroll", "reason": "async context"},
1121 |         )
1122 | 
1123 |     # ------------------------------------------------------------------
1124 |     # Async human-like interaction hooks (PH-11)
1125 |     # ------------------------------------------------------------------
1126 | 
```

[`stealth_engine/engine.py:1223-1240`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L1223-1240)

```python
1223 |     def human_dwell(
1224 |         self, page: PlaywrightPage, min_s: float = 1.5, max_s: float = 6.0
1225 |     ) -> None:
1226 |         """Sync dwell — unsupported on async contexts.
1227 | 
1228 |         PF-02/B-25: jiggle moves are coroutines on the async context.
1229 |         Use ``await session.adwell(page, min_s, max_s)``.
1230 | 
1231 |         Raises:
1232 |             AutomationError: Always — directs caller to the async API.
1233 |         """
1234 |         raise AutomationError(
1235 |             "human_dwell() cannot run synchronously on an async browser "
1236 |             "context; use 'await session.adwell(page, min_s, max_s)'",
1237 |             details={"stage": "human_dwell", "reason": "async context"},
1238 |         )
1239 | 
1240 |     async def adwell(
```

### U-02 — Video recording configurable but intentionally rejected

`ProfileConfig.record_video_dir` exists, but `_build_launch_kwargs` throws `AutomationError` if it is provided; this is verified by local call. **Evidence:**

[`stealth_engine/engine.py:666-687`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L666-687)

```python
 666 |         # PH-19 M3: HAR recording passthrough — relative paths resolve
 667 |         # under the profile directory.  PF-03/B-33: video recording is
 668 |         # Chromium-only in Playwright — on camoufox/Firefox it crashes
 669 |         # the driver during launch, so reject it up-front with a clear
 670 |         # error instead of a confusing connection failure.
 671 |         if cfg.record_har_path:
 672 |             hp = Path(cfg.record_har_path)
 673 |             kwargs["record_har_path"] = str(
 674 |                 hp if hp.is_absolute() else Path(self._session.profile_dir) / hp
 675 |             )
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

### U-03 — CDP is not a confirmed working Firefox/Camoufox feature

The method attempts `context.new_cdp_session` and explicitly wraps unsupported errors. Code comments identify the backend as Firefox/Juggler, but no live call was made. Treat this as unsupported/externally unverified, **not** a working CDP feature. **Evidence:**

[`stealth_engine/engine.py:1673-1695`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L1673-1695)

```python
1673 | 
1674 |         Args:
1675 |             page: Playwright page to attach the session to.
1676 | 
1677 |         Returns:
1678 |             The Playwright ``CDPSession`` object.
1679 | 
1680 |         Raises:
1681 |             AutomationError: If the context is closed, page invalid, or
1682 |                 CDP is unsupported by the browser backend.
1683 |         """
1684 |         if self._closed:
1685 |             raise AutomationError(
1686 |                 "cdp_session on closed session",
1687 |                 details={"stage": "cdp_session", "reason": "session closed"},
1688 |             )
1689 |         try:
1690 |             return await self._ctx.new_cdp_session(page)
1691 |         except Exception as exc:
1692 |             raise AutomationError(
1693 |                 "cdp_session failed (CDP may be unsupported on Firefox/Juggler)",
1694 |                 details={"stage": "cdp_session", "reason": str(exc)},
1695 |             ) from exc
```

### U-04 — Additional context creation has a browser-handle prerequisite

`new_context` only proceeds if `getattr(self._ctx, 'browser', None)` is non-null, otherwise raises `AutomationError`. Since the default launch requests a persistent context, production availability remains unverified until tested against the actual browser backend. **Evidence:**

[`stealth_engine/engine.py:1710-1731`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L1710-1731)

```python
1710 |         options.
1711 | 
1712 |         Returns:
1713 |             A Playwright ``BrowserContext``.
1714 | 
1715 |         Raises:
1716 |             AutomationError: If the browser object is unreachable or
1717 |                 context creation fails.
1718 |         """
1719 |         if self._closed:
1720 |             raise AutomationError(
1721 |                 "new_context on closed session",
1722 |                 details={"stage": "new_context", "reason": "session closed"},
1723 |             )
1724 |         browser = getattr(self._ctx, "browser", None)
1725 |         if browser is None:
1726 |             raise AutomationError(
1727 |                 "new_context unavailable: persistent context exposes no "
1728 |                 "browser object",
1729 |                 details={"stage": "new_context", "reason": "no browser"},
1730 |             )
1731 |         try:
```

### U-05 — Proxy pooling is a standalone manager, not a profile-level pool

`ProxyManager` can accept multiple proxies, but `StealthEngine.__init__` constructs `ProxyManager([config.proxy])` using one configured proxy. Thus **integrated per-profile automatic rotation via ProfileConfig is not in the current engine API**, without claiming the standalone pool is fake. **Evidence:**

[`stealth_engine/engine.py:213-225`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py#L213-225)

```python
 213 | 
 214 |             launch_salt = uuid.uuid4().hex
 215 |         self._launch_salt: str | None = launch_salt
 216 |         self._identity: IdentityGenerator = IdentityGenerator(
 217 |             config, provider=identity_provider, launch_salt=launch_salt
 218 |         )
 219 |         self._proxy_manager: ProxyManager | None = (
 220 |             ProxyManager([config.proxy], seed=config.seed)
 221 |             if config.proxy is not None
 222 |             else None
 223 |         )
 224 | 
 225 |     # ------------------------------------------------------------------
```

### U-06 — BulkRunner task timeout does not include launch/cleanup

`asyncio.wait_for` wraps `task_fn(session)` only. Its `await engine.alaunch()` and cleanup are outside this timeout; any broader end-to-end timeout behavior is unverified. **Evidence:**

[`stealth_engine/orchestrator.py:384-395`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/orchestrator.py#L384-395)

```python
 384 |             try:
 385 |                 engine = StealthEngine(
 386 |                     profile, identity_provider=self._identity_provider
 387 |                 )
 388 |                 session = await engine.alaunch()
 389 |                 if self._task_timeout_s is not None:
 390 |                     await asyncio.wait_for(
 391 |                         task_fn(session), timeout=self._task_timeout_s
 392 |                     )
 393 |                 else:
 394 |                     await task_fn(session)
 395 | 
```

[`stealth_engine/orchestrator.py:434-443`](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/orchestrator.py#L434-443)

```python
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

## Verification boundary and acceptance language

- **Verified offline**: only the exact deterministic operations listed in the test ledger. No live anti-detection effectiveness, blocklist evasion, account safety, proxy-country correctness, WebRTC leak freedom, browser persistence or scaling is certified.
- **Source-confirmed defects:** 19 in the findings report, including some with mocked/controlled reproductions. These findings do not imply all other features pass real production testing.
- **Explicitly unsupported or conditional:** U-01 through U-06, excluded from defect count so it is not inflated.
- **User/admin UI:** no web/desktop UI or auth/role control implementation exists within the audited repo tree. No UI failure count can be inferred.
- **Release verdict:** **NOT PRODUCTION-VERIFIED**. This is a verification status, not an assertion that every untested feature fails.

## Audit change boundary

No production code was edited, no implementation plan or change recommendations were written here, and no real external browser/proxy/account workload was executed. This file records only observations, controlled results and known unknowns.
