# Module: session.py

**File:** `stealth_engine/session.py`  
**Status:** ✅ Implemented (v0.1.0)  
**Public names:** `SessionManager`

## Purpose
Manages per-profile browser session directories, PID lock files, and Playwright storage-state JSON.
No browser, no network — pure filesystem path and JSON management.

## Directory Layout (per profile)

```
<base_dir>/<profile_name>/
    user_data/              ← Playwright/camoufox user-data directory
    storage_state.json      ← exported Playwright storage state
    .lock                   ← JSON PID lock file
```

## Public API

### Properties (read-only)

| Property | Type | Description |
|----------|------|-------------|
| `user_data_dir` | str | Absolute path to the browser user-data directory |
| `storage_state_path` | str | Absolute path to the storage-state JSON file |
| `profile_dir` | str | Absolute path to the profile root (parent of `user_data`; PH-15 — hosts `behavior.json`) |

`export_state(storage_state, domains=None)` (PH-18, N8): optional domain allow-list filters cookies by `domain` and origins by `origin` host — for multi-account storage splitting.

`_pid_alive` (BF-01/B-02 fix): Windows uses `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)` via ctypes — `os.kill(pid,0)` would have called `TerminateProcess` and killed live lock-holders.

`export_state(domains=)` domain matching (BF-02/B-04 fix): dot-boundary suffix match (`host == d or host.endswith("."+d) or d.endswith("."+host)`) — `notexample.com` no longer leaks into `example.com` exports; empty-domain entries excluded; parent-domain cookies still export for subdomain filters.
| `lock_path` | str | Absolute path to the PID lock file |

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `ensure_dirs` | `() -> None` | Create profile directory tree; set 0o700 on profile root (best-effort) |
| `acquire_lock` | `() -> None` | Atomically create PID lock file; remove stale locks (dead PID or >24h old) |
| `release_lock` | `() -> None` | Remove lock file; idempotent |
| `force_reset` | `() -> None` | Release lock + delete entire profile directory recursively |
| `export_state` | `(storage_state: dict) -> None` | Validate and atomically write storage state JSON |
| `import_state` | `() -> dict | None` | Read storage state; None if missing; SessionError if malformed |
| `has_state` | `() -> bool` | True iff file exists, >2 bytes, valid JSON with "cookies" key |
| `state_metadata` | `() -> dict` | Returns exists, size_bytes, mtime_epoch, sha256 |
| `__enter__` | `() -> SessionManager` | ensure_dirs() + acquire_lock() |
| `__exit__` | `(exc_type, exc, tb) -> None` | release_lock() unconditionally; never suppresses exceptions |

## Behaviour Details

- **Lock atomicity**: `open(..., "x")` mode — atomic on POSIX and Windows NTFS.
- **Stale lock**: removed when recorded PID is dead (`_pid_alive` false — Windows uses `OpenProcess` query, POSIX `os.kill(pid,0)`) OR timestamp >24h old.
- **Atomic writes**: `export_state` writes to `.json.tmp` then `os.replace()`.
- **Path-traversal guard**: profile_name is rejected if it contains `/`, `\`, or `..`.
- **Concurrency**: per-class `asyncio.Lock` serialises lock-file operations across coroutines.
- **Secrets**: storage state JSON is stored as-is from Playwright; no proxy credentials are injected or logged.

## Does NOT
- Launch or import playwright/camoufox
- Parse or modify cookie contents
- Encrypt data on disk
- Make network calls
- Add retry loops

## Change History
| Version | Change |
|---------|--------|
| 0.1.0 | Initial implementation — Phase 3 |
