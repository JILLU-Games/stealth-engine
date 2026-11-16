# 06 — Scope Lock, Change Control & Verification Protocol

> **Status: DOCUMENTED ONLY / NO IMPLEMENTATION**. This is a proposed incremental plan, not a claim of completed fixes.
> **Immutable source baseline:** [`a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`](https://gitlab.com/ivibtools/stealth-engine/-/commit/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5); prior source audit revision [`6255383cac9f29d64bf9ee5957c77ee26ccd7993`](https://gitlab.com/ivibtools/stealth-engine/-/commit/6255383cac9f29d64bf9ee5957c77ee26ccd7993). The 31 audited executable/config blob hashes match across these revisions.


## Before implementation (mandatory)

1. Compare remote `main` with documented SHA `a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`; save current HEAD and Git blob hashes of allowed source files.
2. Read `01` finding evidence and `02` exact allowed scope for the **single** requested phase. Do not use old product roadmap prose to override source evidence.
3. Validate environment + test availability; missing `browserforge`, `camoufox`, `tzlocal` in the audit host means live tests must be installed/verified separately. Do not claim unrun tests passed.
4. Announce the locked phase in the phase log as `IN PROGRESS` **only when implementation actually begins**. Planning documentation alone never starts a phase.

## During one phase

- Touch only allowed function regions and designated test files; no unrelated UI/API/repo restructuring, dependency major-version upgrades or public behavior changes.
- For a cross-region dependency, record a scope change request and obtain approval before proceeding. Don't silently amend previous phases.
- Preserve data and session profiles: no reset/delete of user runtime files as a test side effect.
- Use locally controlled fixtures for credential/proxy/network probes; never hardcode actual usernames/passwords or live personal accounts in tests.
- Keep exception messages redacted and async cleanup reliable; errors from non-retryable paths must retain classification.

## Focused phase exit gate (single pass, no long loops)

1. Run 1 **focused** test command including cases for the phase finding IDs and adjacent backward-compatibility behavior. Save command, platform, dependency versions, result summary and exit status.
2. Run a source diff/patch audit and cross-check all changed source ranges with that phase's Scope Lock.
3. If either fails: record `BLOCKED`, preserve minimal repro, fix only in the same scope, and do not overstate completion. Re-test only the failing focused cases.
4. When passing: create **one commit per phase** (with tests), update status docs (`03` & `05`) with real evidence and commit IDs; **do not count report-only commits as phase progress**.
5. Run global suite + real browser/proxy acceptance at final release gate, not repeated needlessly each phase.

## Release/blocking matrix

| Release prerequisite | Required evidence | Baseline status |
|---|---|---|
| 19 source findings dispositioned | 19 source/test links + each phase commit | OPEN |
| U-01..U-06 truthfully documented/verified | Runtime result or explicit unsupported decision | UNDECIDED |
| Async/sync lifecycle + cleanup | Real Camoufox and bounded fake-context regressions | NOT VERIFIED |
| Profile owner/reset safety | Multi-instance tests, preserved profile data | Source defects OPEN |
| Proxy/WebRTC/Geo | Controlled SOCKS, HTTP, egress/leak tests | NOT LIVE VERIFIED |
| Fingerprint and API interactions | Supported backend readback + request route tests | NOT LIVE VERIFIED |
| Security/data protection | Config export file tests, redaction, no credential leaks | OPEN |
| Packaging/CI | Actual pipeline, artifact install/smoke test, dependency lock | NOT VERIFIED |
| Admin/user UI | App source if elsewhere + actual UI test | NOT APPLICABLE to this Python repo |

## Rollback and baseline drift

- Every implementation commit must be reversible independently; rollback must not delete or mutate user profiles, cookies or previous state.
- Save Git revision + tests + exact source-file list in `03` before declaring complete.
- If unrelated branch commits alter source, pause and reconcile SHA/hashes, then version the phase plan before continuing.
- When real-backend behavior contradicts prior mock-only evidence, change `01` finding disposition **with new exact source/runtime proof**, not by erasing historical evidence.
- Avoid force-pushing, rebasing published evidence commits, deleting existing `notes/production/` audit reports, or silently renaming `notes/productions/`.

## Reference source blocks for implementation boundaries

**[Source: `stealth_engine/engine.py:415-424`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L415-424)**

```python
 415 |         except StealthEngineError:
 416 |             # Preserve typed sub-exceptions from sub-modules unchanged.
 417 |             await self._emergency_cleanup(ctx_handle, session)
 418 |             raise
 419 |         except Exception as exc:
 420 |             await self._emergency_cleanup(ctx_handle, session)
 421 |             raise LaunchError(
 422 |                 f"camoufox launch failed at stage={stage!r}: {exc}",
 423 |                 details={"stage": stage, "reason": str(exc)},
 424 |             ) from exc
```

**[Source: `stealth_engine/orchestrator.py:404-443`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/orchestrator.py#L404-443)**

```python
 404 |             except _NON_RETRYABLE as exc:
 405 |                 # SessionError (locked) or IdentityError — not worth retrying.
 406 |                 duration_ms = round((time.perf_counter() - wall_start) * 1000.0, 2)
 407 |                 _log.warning(
 408 |                     "profile skipped (non-retryable)",
 409 |                     profile=profile.profile_name,
 410 |                     reason=str(exc),
 411 |                 )
 412 |                 return ProfileResult(
 413 |                     profile_name=profile.profile_name,
 414 |                     status=ProfileStatus.SKIPPED,
 415 |                     attempts=attempts,
 416 |                     duration_ms=duration_ms,
 417 |                     error=str(exc),
 418 |                 )
 419 | 
 420 |             except asyncio.CancelledError:
 421 |                 # Propagate cancellation immediately — do not swallow.
 422 |                 raise
 423 | 
 424 |             except Exception as exc:
 425 |                 last_error = str(exc) or type(exc).__name__
 426 |                 _log.warning(
 427 |                     "profile attempt failed",
 428 |                     profile=profile.profile_name,
 429 |                     attempt=attempt,
 430 |                     max_attempts=self._max_attempts,
 431 |                     error=last_error,
 432 |                 )
 433 | 
 434 |             finally:
 435 |                 if session is not None:
 436 |                     try:
 437 |                         await session.aclose()
 438 |                     except Exception as close_exc:
 439 |                         _log.warning(
 440 |                             "session.aclose() failed during cleanup",
 441 |                             profile=profile.profile_name,
 442 |                             reason=str(close_exc),
 443 |                         )
```

**Planning deliverable only:** this protocol does not itself alter app code, run a phase, or establish production certification.
