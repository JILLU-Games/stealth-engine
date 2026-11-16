# 04 — ERROR HANDLING (advance phases)

## Current model (unchanged)

7-type hierarchy under `StealthEngineError`: ConfigError, IdentityError,
ProxyError, SessionError, LaunchError, AutomationError + base.
All carry `details={"stage": ...}`; credentials never exposed.

## Planned additions per phase

### PH-13
- `network.proxy.socks_remote_dns` unsupported proxy scheme → `ConfigError`
- IPv6-disable config rejected by camoufox → `LaunchError` (wrap)

### PH-14
- Unknown camoufox config key → `ConfigError` (validate against allowlist)
- `webgl_config`/`screen`/`fonts` invalid values → `ConfigError`

### PH-15
- Bezier/typing params out of range → `AutomationError`
- Persisted cadence profile corrupt → warn + regenerate (self-heal)

### PH-16
- Storage leak detected → `SessionError` (audit failure = hard fail)
- Seeded localStorage injection conflict → `ConfigError`

### PH-17
- Drift detected → warning field (NOT exception — informational)
- Risk score threshold exceeded → `ProfileResult.warning` (not raise)

### PH-18
- Proxy file parse error → `ConfigError` with line number
- Unknown preset name → `ConfigError`
- Warmup flow step failure → `AutomationError` with step index

## Invariants (never break)

- Single catchable base `StealthEngineError`
- `details` dict always present
- Credentials never in errors/logs
- Cleanup never masks original exception
- Non-retryable: `IdentityError`, `SessionError`
