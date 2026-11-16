# Feature O: Orchestrator retries with backoff

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `orchestrator.py`

## Description

`BulkRunner` retries failed profile tasks with configurable exponential backoff (`backoff_base_s` × 2^(attempt-1), capped at `backoff_max_s`, ±20% per-profile-seeded jitter). `max_attempts` is configurable per `BulkRunner` instance. `SessionError`/`IdentityError` are non-retryable → `SKIPPED`.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — implemented since initial orchestrator phase |
