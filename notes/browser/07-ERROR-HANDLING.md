# 07 — ERROR HANDLING (browser-depth phases)

## Current model (unchanged)

7-type hierarchy under `StealthEngineError`; all carry
`details={"stage": ...}`; credentials never exposed; cleanup never
masks original exception.

## Planned additions per item

### M1 verify_stealth
- Probe/evaluate failure → `AutomationError` (stage="verify_stealth")
- Partial probe data → degrade to `None` fields, still return report
  (never raise on missing signals — risk score handles them)

### M2 CDP passthrough
- `new_cdp_session` unsupported → `AutomationError`
  (stage="cdp_session", reason="unsupported by camoufox")
- Session closed → `AutomationError`

### M3 recording
- Invalid record path → `ConfigError` (stage="recording")
- Unsupported kwarg → `LaunchError` with camoufox error passthrough

### M4 new_context
- Context creation unsupported → `AutomationError`
  (stage="new_context")
- Context limit exceeded → `AutomationError` with details

## Invariants (never break)

- Single catchable base `StealthEngineError`
- `details` dict always present
- Credentials never in errors/logs
- Async methods raise `AutomationError`, not bare exceptions
