# 04 — ERROR HANDLING INVENTORY

Current error model + proposed additions per phase. Keep this updated when
new error paths are added.

## 1. Current exception hierarchy (`stealth_engine/exceptions.py`)

```
StealthEngineError (base; message + details dict)
├── ConfigError        — invalid config values
├── IdentityError      — fingerprint generation/extraction/validation,
│                        seeds.json persist failure, provider failure
├── ProxyError         — geo endpoint HTTP/timeout/JSON/connection,
│                        all-proxies-unhealthy, empty proxy list
├── SessionError       — profile dir/lock/state failures, path traversal
├── LaunchError        — camoufox missing/failed, running-loop sync launch,
│                        host-IP resolution failure
└── AutomationError    — page ops (new_page/save_state/human hooks),
                         sync close in running loop, BulkRunner param errors
```

All carry `details={"stage": ..., ...}` for debugging. Public API exports
all 7 names.

## 2. Current handling patterns

| Pattern | Where | Behavior |
|---|---|---|
| Typed propagation | `StealthEngine.alaunch` | `StealthEngineError` subclasses re-raised unchanged; others wrapped in `LaunchError(stage=...)` |
| Emergency cleanup | `_emergency_cleanup()` | camoufox handle `__aexit__` + `release_lock()`, best-effort, never re-raises |
| Lock safety | `SessionManager` | atomic `open("x")`, stale-pid/age detection, non-recursive retry |
| Credential safety | `ProxyManager.mask()`, `to_public_dict()`, log regex | passwords never in logs/exceptions |
| Self-healing | `get_or_create_seeds()` | corrupt/invalid seeds.json → warn + regenerate |
| Retry taxonomy | `BulkRunner._NON_RETRYABLE` | `IdentityError`/`SessionError` → SKIPPED; others retried w/ backoff+jitter |
| Cancellation | `BulkRunner` | `CancelledError` propagates; `shutdown()` cancels inflight |
| Idempotency | `close()`/`aclose()`/`aclose()`/`shutdown()` | safe repeat calls |

## 3. Error paths added by upcoming phases

### PH-09 (GeoIP core)
| New error | Where | Type |
|---|---|---|
| Direct-IP resolve failure | `GeoResolver.resolve` | `ProxyError` (reuse) or new `GeoError`? — DECIDE at plan: prefer reuse `ProxyError` to avoid new exception type |
| Country filter rejects all | `pick_filtered` | `ProxyError("no proxy matches geo policy")` |
| Cache miss + endpoint down | resolver | `ProxyError` as today |
| Batch partial failure | `resolve_many` | per-item `ProxyError` in result dict, not raise-all |
| Validator mismatch | `validate_geo_consistency` | returns report dict (NOT exception — it's a check tool) |

### PH-10 (GeoIP extended) — actual
| New error | Where |
|---|---|
| Unknown policy preset name | `ConfigError` (`stage="geo_policy"`) |
| All endpoints failed | `ProxyError` with `details["attempts"]` list |
| Extended field absent in response | silent `None` (graceful degrade) ✓ |
| `locale="auto"` geo resolve fails | warning log + seed fallback (no raise) ✓ |

### PH-11 (Hardening)
| New error | Where |
|---|---|
| Geo resolve retries exhausted | `ProxyError` with `attempts` detail |
| Task timeout | `ProfileResult(status=FAILED, error="task timeout")` — not exception |
| Async hook failures | `AutomationError` (same as sync) |
| Smoke test env missing | skip, not error |

## 4. Error-handling gaps to consider (owner decision)

| # | Item | Options |
|---|---|---|
| G1 | New `GeoError` exception type vs reuse `ProxyError` | Reuse = smaller API; new = clearer taxonomy. Recommend reuse. |
| G2 | `resolve_many` fail-fast vs collect-errors | Recommend collect-errors (partial results useful for pools) |
| G3 | Geo endpoint provider-down circuit breaker | Nice-to-have; defer unless rate-limit issues appear |
| G4 | Structured error codes (`details["code"]`) | Would help app-level handling; adds API surface — defer |

## 5. Invariants (must never break)

- Single catchable base: `StealthEngineError`
- `details` dict always present on raise
- Credentials NEVER in exception messages/details/logs
- Cleanup paths never mask the original exception
- Non-retryable taxonomy stays: `IdentityError`, `SessionError`
