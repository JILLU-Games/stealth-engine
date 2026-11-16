# Fix Batch F1 — CRITICAL asyncio.Lock bugs

**Date:** 2026-10-19  
**Status:** Done

## B-001 — session.py: class-level asyncio.Lock removed

- Lines 69–70 (before): `_class_lock: asyncio.Lock = asyncio.Lock()` at class body scope
- After: lines deleted entirely
- _class_lock was declared but never referenced in any method body
  (acquire_lock() is sync and never awaited it), so removal has zero
  behavioral impact — it was purely a crash-at-import bomb on Python 3.12.

## B-002 — proxy.py: instance asyncio.Lock made lazy

- Line 149 (before): `self._lock: asyncio.Lock = asyncio.Lock()`
- Line 149 (after): `self._lock: asyncio.Lock | None = None`
- Added private `_get_lock() -> asyncio.Lock` helper at line 156
  that creates the lock on first call (always inside an async context)
- `pick_healthy()`: `async with self._lock:` → `async with self._get_lock():`
- All other semantics identical.

## Fix Batch F2 — B-003 (engine.py only)

**Date:** 2026-10-19  
**Chosen option:** B (fix in engine.py)

### Changes

1. Added `import os` to engine.py imports.
2. `StealthEngine.__init__`: replaced `SessionManager(config, base_dir=config.user_data_dir ...)` with `_base = self._derive_base_dir(config)` then `SessionManager(config, base_dir=_base)`.
3. Added private `_derive_base_dir(config) -> str | None`:
   - `None` when `user_data_dir` is unset → SessionManager defaults to `./profiles`
   - `ConfigError` when strips to empty string
   - `os.path.dirname(udd)` when `basename(udd) == profile_name` (normal case)
   - `udd` as-is with WARNING when basename does not match (legacy/base-dir interpretation)

### Resulting layout (documented)

    <config.user_data_dir>/user_data          ← camoufox browser data
    <config.user_data_dir>/storage_state.json
    <config.user_data_dir>/.lock

### session.py: NOT touched
### config.py: NOT touched

## Fix Batch F3 — B-004/005/006/007/008

**Date:** 2026-10-19

### B-004 proxy.py
- `_build_proxy_url` now returns clean server URL, no credentials embedded
- New `_build_proxy_auth` returns `aiohttp.BasicAuth(u, p)` or None
- `resolve_geo` passes `proxy_auth=proxy_auth` to `session.get()`
- `to_playwright()` UNCHANGED

### B-005 session.py
- `_try_acquire_lock` is now non-recursive
- On `FileExistsError` with `retry=False`: raises `SessionError` immediately
- On `FileExistsError` with `retry=True`: checks staleness, unlinks if stale, calls `_try_acquire_lock(retry=False)` once — no further recursion possible

### B-006/B-007 engine.py
- `BrowserSession.close()`: added `asyncio.get_running_loop()` guard — raises `AutomationError` if called from inside a running loop
- Both async cleanups (`ctx_handle.__aexit__` + `proxy_manager.aclose`) merged into single `asyncio.run(_async_close())` — one loop, one session lifetime
- `self._session.release_lock()` moved to after the single `asyncio.run()` call

### B-008 orchestrator.py
- After `asyncio.gather`, iterate all slots; fill `None` with `ProfileResult(status=FAILED, attempts=0, error="cancelled by shutdown")`
- `len(results) == len(profiles)` is now guaranteed

## Fix Batch F4 — B-009/010/011/013/014/015

**Date:** 2026-10-19

### B-009 proxy.py — shuffle moved inside lock
- `self._rng.shuffle(self._proxies)` now inside `async with self._get_lock()`
- Copy of shuffled list taken inside same lock block
- No shuffle after lock release — rng never accessed concurrently

### B-010 session.py — export_state wrote-flag
- `wrote = False` before try; set `True` after `os.replace`
- finally: `if not wrote: tmp.unlink(...)` — only on failure path

### B-011 engine.py — proxy server URL masked in log
- `re.sub(r"//[^@]*@", "//***@", proxy_cfg.server)` before logging
- `proxy=_proxy_log` (masked str or None) — raw server URL never logged

### B-013 session.py — mkdir wrapped in OSError → SessionError
- Both `mkdir` calls inside `try/except OSError` → `SessionError(stage="ensure_dirs")`
- `chmod` PermissionError: log WARNING, no raise
- Other `chmod` OSError: silently ignored (best-effort)

### B-014 proxy.py — unused ValidationError import removed
- No Pydantic model construction in proxy.py __init__; import was dead code
- `from pydantic import BaseModel, ValidationError` → `from pydantic import BaseModel`

### B-015 identity.py — generate() returns deep copy
- `import copy` added
- Both return paths use `copy.deepcopy(self._cached_fingerprint)`
- Cache is internal-only; callers get isolated copies

## Fix Batch F5 — B-017/018

**Date:** 2026-10-19

### B-017 orchestrator.py — defensive copy of profiles list
- `self._profiles = profiles` → `self._profiles = list(profiles)`
- Caller cannot append/remove from internal list after construction

### B-018 session.py — resolved-path prefix check (additional defence)
- After existing string guards, added `(resolved_base / name).resolve()` check
- If resolved prof path does not start with `str(resolved_base) + os.sep` → `SessionError`
- `OSError` / `RuntimeError` from `resolve()` → WARNING logged, fallback to string guards
- Existing string guards NOT removed
