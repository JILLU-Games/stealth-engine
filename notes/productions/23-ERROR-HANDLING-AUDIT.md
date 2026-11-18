# Error-Handling Audit and Follow-up Register

**Audit date:** 2026-11-18
**Baseline:** `58c87e2b4de27e5a0510b628a623fcf6f1a1a96b`
**Purpose:** Record existing exception contracts, their actual boundaries, and evidence needed before any error-handling change. No source changes are authorized by this register.

## Error Taxonomy Present in Source

The shared hierarchy in `stealth_engine/exceptions.py` is `StealthEngineError` with typed subclasses `ConfigError`, `IdentityError`, `ProxyError`, `SessionError`, `LaunchError`, and `AutomationError`. Pydantic `ValidationError`, standard filesystem/network exceptions, and cancellation exceptions may also appear at API boundaries; do not claim every external exception is converted to the shared hierarchy.

| Area                                  | Existing handling                                                                                                                                                                                      | Current limitation / evidence boundary                                                                                             |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| Config and proxy validation           | Pydantic validators reject invalid profiles/proxy authorities; credential-bearing input is hidden/sanitized in the patched validation paths                                                            | Pydantic validation remains a distinct exception type; test exact output before displaying/logging user input                      |
| Identity and seed persistence         | Provider failures are surfaced as `IdentityError`; corrupt seed files are regenerated; update-write failure is typed and temp cleanup is attempted                                                     | Filesystem permissions/full-disk/platform failures still need environment-specific tests                                           |
| GeoIP and proxy requests              | Typed `ProxyError`; retry/backoff for configured transient paths; credential-free/masked proxy identity in the patched path                                                                            | External provider/network behavior, proxy errors from arbitrary libraries, and live third-party proxies are not certified          |
| Session directories and ownership     | `SessionError`; guarded owner-token lock operations; malformed/unknown lock state fails closed; reset refuses live/unknown owners                                                                      | Current Windows CI is evidence for its runner only; other shared/network filesystems are outside the acceptance scope              |
| Browser launch and session operations | Launch failure invokes cleanup; known engine errors retain type; unexpected launch exceptions become `LaunchError`; unsupported async-context operations use `AutomationError`                         | Cleanup is not proven for every possible process crash or arbitrary third-party backend failure                                    |
| Bulk orchestration                    | Retryable task failures are recorded; non-retryable session/identity failures become skipped results; task callback can use `task_timeout_s`; cancellation propagates and session cleanup is attempted | Timeout excludes engine launch and final cleanup; cleanup errors are logged and do not replace the original task outcome           |
| Behavioral profile file               | Missing/corrupt behavior profile is regenerated with a warning                                                                                                                                         | A persistent write failure may prevent first-use behavior initialization; record the exact path and error without profile contents |
| Logging                               | `ProfileLogger` filters severity and recursively scrubs known profile secrets in profile-owned records                                                                                                 | Legacy module-global Loguru records are process-global and outside this profile contract; never claim system-wide redaction        |
| Package/runtime setup                 | Missing imports surface during module/test collection; PR-01's isolated `.venv` now collects/runs the suite                                                                                            | Initial system interpreter lacks `aiohttp`/`browserforge`; venv install resolves PR-01 without changing package source             |

## Failure-Handling Principles Already Required

1. Preserve typed errors when they carry the caller's actionable classification; wrap unexpected errors only at a documented boundary.
2. Do not retry validation, ownership, or other non-retryable failures as though they were transient network errors.
3. Keep cleanup best-effort but observable; do not erase the primary error with a cleanup error.
4. Fail closed for unknown profile-lock ownership. Never use a test to delete/reset user profile data.
5. Keep credentials, cookies, storage state, and raw profile contents out of exception details, logs, test reports, and this notes tree.
6. Cancellation must propagate after owned resources receive the documented cleanup attempt.
7. Record a skipped/unavailable test as `NOT RUN` or `BLOCKED`, never as a pass.

## Open Error/Acceptance Items

| ID    | Item                                                                                     | State                   | Gate / owner decision                                                                                 |
| ----- | ---------------------------------------------------------------------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------- |
| EH-01 | Local dependency collection cannot start in the system Python 3.12 environment           | RESOLVED IN PR-01 VENV  | `.venv` Windows Python 3.12: 245 passed, 5 expected skips, `pip check` clean; system Python unchanged |
| EH-02 | External proxy/provider errors and credential redaction under real third-party libraries | NOT VERIFIED            | PR-03 only with owner-authorized infrastructure; do not store credentials in notes                    |
| EH-03 | Proxy DNS/WebRTC/network errors on external paths                                        | NOT VERIFIED            | PR-03 controlled scope; no general leak-free claim                                                    |
| EH-04 | Module-global logger error records are not profile-isolated                              | KNOWN LIMITATION        | Accept/document as is or request a new source Scope Lock; no silent global logger reconfiguration     |
| EH-05 | Windows/file-lock behavior beyond the tested GitHub runner                               | NOT VERIFIED            | Restrict claims to tested platform/filesystem evidence                                                |
| EH-06 | Task timeout does not bound launch/cleanup                                               | DOCUMENTED CONTRACT     | Any broader timeout behavior requires a separate behavior/API decision                                |
| EH-07 | Video/CDP and synchronous session helper operations                                      | UNSUPPORTED/CONDITIONAL | Preserve clear typed errors; do not report as active features                                         |
| EH-08 | `aiohttp.BasicAuth` deprecation under aiohttp 3.14.5                                     | FOLLOW-UP CANDIDATE     | Four warnings, no failures; decide a source/test scope before aiohttp 4 compatibility work            |

## Change Gate

Any future exception-handling edit needs one finding ID, exact allowed function/file list, a non-secret minimal reproduction, expected exception type/message/details, focused tests, and an adjacent regression check. Expand no logger scope, retry scope, timeout scope, or public error contract without explicit approval. Update this register only after the code/test evidence exists.
