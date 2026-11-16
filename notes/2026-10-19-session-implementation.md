# Plan: session.py Implementation

**Date:** 2026-10-19  
**Status:** In progress

## What is being changed and why

Implementing `stealth_engine/session.py` — Phase 3 of the roadmap.
Manages per-profile directories, lock files, and storage state JSON.
No browser, no network — pure filesystem + path logic.

## Files affected

- `stealth_engine/session.py` (implement from skeleton)
- `project/modules/session.md` (update status)

## Expected outcome

`SessionManager` class with 11 public members:
- 3 read-only properties: `user_data_dir`, `storage_state_path`, `lock_path`
- 8 methods: `ensure_dirs`, `acquire_lock`, `release_lock`, `force_reset`,
  `export_state`, `import_state`, `has_state`, `state_metadata`
- Context manager: `__enter__` / `__exit__`

## Key design decisions

- Lock uses open("x") for atomicity on POSIX and Windows
- Stale lock: pid not alive OR ts older than 24h → remove and retry once
- Writes are atomic: write to .tmp then os.replace()
- Per-class asyncio.Lock (not global) for asyncio safety
- profile_name path-traversal check: reject "/" "\" ".."

## Phase log

### Phase 1 — Read existing stable files ✅
- config.py: ProfileConfig shape confirmed
- exceptions.py: SessionError confirmed
- utils/logging.py: get_logger confirmed

### Phase 2 — Write session.py
- In progress...

### Phase 2 — session.py written ✅

- `SessionManager` with 3 properties + 8 methods + context manager
- `open("x")` lock atomicity; stale detection via pid_alive + age check
- `asyncio.Lock` on class (not global) for coroutine safety
- Atomic writes: `.json.tmp` → `os.replace()`
- path-traversal guard: rejects `/`, `\`, `..` in profile_name
- `shutil.rmtree` for force_reset; `missing_ok=True` for idempotent unlink
- No secrets in logs (only size_bytes, sha256)

### Phase 3 — project/modules/session.md updated ✅

Done. No issues.
