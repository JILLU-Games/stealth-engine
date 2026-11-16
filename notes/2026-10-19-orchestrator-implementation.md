# Plan: orchestrator.py Implementation

**Date:** 2026-10-19  
**Status:** In progress

## What is being changed and why

Implementing `stealth_engine/orchestrator.py` — Phase 6 of the roadmap.
BulkRunner: bounded-concurrency asyncio task queue with per-profile retry + backoff.

## Files affected

- `stealth_engine/orchestrator.py` (implement from skeleton)
- `project/modules/orchestrator.md` (update status)

## Key design decisions

- Semaphore and start-gap Lock created lazily inside run() to avoid
  asyncio "no running loop" errors at __init__ time
- Results list pre-allocated by index to guarantee input order
- Per-task asyncio.Task refs held in self._inflight: set[asyncio.Task]
  for cancellation in shutdown()
- Non-retryable exceptions: SessionError (lock held) + IdentityError
  → status = SKIPPED immediately, no further attempts
- Backoff: min(backoff_max_s, backoff_base_s * 2**(attempt-1)) * jitter(±20%)
- Jitter uses per-profile random.Random(profile.seed) if seed set, else fresh
- duration_ms measured from first-attempt start across all attempts

## Phase log

### Phase 1 — Read stable files ✅
- exceptions.py: IdentityError, SessionError, AutomationError confirmed
- engine.py: StealthEngine(config), alaunch() -> BrowserSession, aclose() confirmed

### Phase 2 — Write orchestrator.py
- In progress...

### Phase 2 — orchestrator.py written ✅

- `ProfileStatus` (str Enum): SUCCESS / FAILED / SKIPPED
- `ProfileResult` (dataclass): profile_name, status, attempts, duration_ms, error
- `BulkRunner.__init__`: 5 validated params; semaphore/lock = None (lazy); _inflight set; _shutting_down flag
- `run()`: creates semaphore + lock lazily; asyncio.gather on N tasks; pre-allocated results list for order preservation
- `_run_profile()`: acquires semaphore → enforces start gap → calls _attempt_profile
- `_attempt_profile()`: retry loop; per-profile isolated RNG; non-retryable exceptions → SKIPPED; CancelledError propagates; finally always calls session.aclose()
- `run_sync()`: raises AutomationError if running loop detected
- `shutdown()`: sets _shutting_down, cancels + awaits all _inflight tasks; idempotent
- `except _NON_RETRYABLE` tuple: (IdentityError, SessionError) — valid Python 3.10 syntax

### Phase 3 — project/modules/orchestrator.md updated ✅

Done. No issues.
