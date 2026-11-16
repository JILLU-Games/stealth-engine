# Module: orchestrator.py

**File:** `stealth_engine/orchestrator.py`  
**Status:** ✅ Implemented (v0.1.0)  
**Public names:** `ProfileStatus`, `ProfileResult`, `BulkRunner`

## Purpose
Bounded-concurrency bulk task execution across multiple profiles. Wraps `StealthEngine` per profile, applies retry with exponential backoff, and returns ordered results.

## Public API

### ProfileStatus (str, Enum)

| Value | Meaning |
|-------|---------|
| `"success"` | Task function completed without error |
| `"failed"` | All retry attempts exhausted with errors |
| `"skipped"` | Non-retryable condition (lock held / identity seed conflict); no retry |

### ProfileResult (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `profile_name` | str | From `ProfileConfig.profile_name` |
| `status` | ProfileStatus | Final outcome |
| `attempts` | int | Total attempts made (0 if skipped before launch) |
| `duration_ms` | float | Wall-clock ms from first attempt start to completion |
| `error` | str \| None | Last error message, or None on success |

### BulkRunner

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(profiles, *, concurrency, max_attempts, backoff_base_s, backoff_max_s, min_start_gap_s, identity_provider, task_timeout_s)` | Validate params; store config; no I/O. `identity_provider` is an optional shared `IdentityProvider` forwarded to every `StealthEngine` (PH-06, Feature P). `task_timeout_s` (PH-11) wraps `task_fn` in `asyncio.wait_for`; timeout → retryable failure |
| `run` | `async (task_fn) -> list[ProfileResult]` | Run task_fn against all profiles; return results in input order |
| `run_sync` | `(task_fn) -> list[ProfileResult]` | Sync wrapper via asyncio.run(); raises AutomationError if loop running |
| `shutdown` | `async () -> None` | Cancel in-flight tasks; set _shutting_down=True; idempotent |

## Behaviour Details

- **Concurrency**: `asyncio.Semaphore(concurrency)` — max N simultaneous browser sessions.
- **Start gap**: `asyncio.Lock` serialises starts; sleeps remainder of `min_start_gap_s` if needed.
- **Retry**: exponential backoff `min(backoff_max_s, backoff_base_s * 2^(attempt-1))` × ±20% jitter (per-profile `random.Random(seed)`).
- **Non-retryable**: `SessionError` (profile locked by another process) and `IdentityError` → `SKIPPED` immediately; no further attempts.
- **Results order**: pre-allocated `list[ProfileResult | None]` indexed by input position; filled by each task.
- **Cancellation**: `asyncio.CancelledError` is not caught — it propagates immediately so `shutdown()` can cancel tasks cleanly.
- **Semaphore/Lock**: created lazily inside `run()` (event loop guaranteed there); stored as `None` in `__init__`.
- **In-flight tracking**: `self._inflight: set[asyncio.Task]` — tasks register/deregister via `add_done_callback`.

## Does NOT
- Schedule, queue, or persist results
- Rotate proxies (ProxyManager handles that)
- Import identity/proxy/session directly
- Add CLI or `__main__`

## Change History
| Version | Change |
|---------|--------|
| 0.1.0 | Initial implementation — Phase 6 |
| PH-06 | Added optional `identity_provider` kwarg shared across profiles (Feature P) |
| PH-11 | Added `task_timeout_s` per-task timeout via `asyncio.wait_for`; empty-exception errors now record the exception type name |

BF-03: `run()` re-entry guard — concurrent calls raise `AutomationError` (fresh semaphore would have silently doubled the concurrency limit); `_run_active` flag reset in `finally`.
