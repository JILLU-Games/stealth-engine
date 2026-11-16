# 05 — ERROR HANDLING (bugFix phases)

## Current model (unchanged)

7-type hierarchy under `StealthEngineError`; `details={"stage":...}`;
credentials never exposed; cleanup never masks original exception.

## Per-bug error-path notes

- **B-01**: `save_state_async` raises `AutomationError` on capture
  failure; `aclose`/`close` keep best-effort swallow+warn (unchanged
  contract — save failure must not block close).
- **B-02**: ctypes `OpenProcess` failure → treat as dead (stale) —
  safe direction (removes stale lock rather than killing live proc).
- **B-04**: filter mismatch → cookie simply excluded; no error.
- **B-05**: all fallbacks exhausted → `webrtc:ipv4="0.0.0.0"` +
  warning (launch continues; WebRTC advertises unspecified addr —
  camoufox may ignore; documented).
- **B-17**: endpoint normalisation happens at init; bad endpoint →
  ProxyError at resolve time (unchanged contract).
- **B-09**: unexpected exceptions wrapped → `ProxyError` with
  `reason` — callers see consistent type.

## Invariants (never break)

- Single catchable base `StealthEngineError`
- `details` dict always present
- Credentials never in errors/logs
- Async methods raise `AutomationError`, not bare exceptions
- `CancelledError`/`KeyboardInterrupt` always propagate
