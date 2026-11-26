# SDK-LIFECYCLE-01 — owner-approved additive maintenance

Baseline: accepted but unmerged FINAL-DEV-01 candidate `24c4f528a756ea57c4c4bea45fe926c2080bbb92`, tree `a324692bc999da19a60102f8b440fcd5191f6868`. Separate stacked draft PR against ci/final-dev-01, so prior accepted PR #3 and main are unchanged. No publish, merge, deployment, connected machine or local build. GitHub Actions only.

Scope: stealth_engine/engine.py, stealth_engine/config.py, stealth_engine/behavior.py, tests/test_sdk_lifecycle.py (new), project/modules/engine.md, project/modules/config.md, project/modules/behavior.md, docs/MODULES.md, notes/MANIFEST.md, this note. Existing public APIs, modules, tests and CI gates preserved. No changes to fingerprint, evasion, proxy behavior or interaction timing.

Plan: optional lifecycle callbacks; context-close listener and idempotent owner-only cleanup; best-effort storage export (a closed context may no longer return state, retain existing snapshot). Offload synchronous session filesystem operations and existing behavior-profile loading only, without changing behavior generation. Cancellation must not race an in-flight lock acquisition/release. Optional host probe opt-out defaults to existing behavior. Explicit same-profile snapshot restore only, using supported Playwright API; default false, existing profile storage retained if disabled. Native restore replaces browser storage; do not claim lossless merge or guaranteed recovery after manual closure. No cross-profile imports. Existing methods and tests intact. Focused tests and existing GitHub regression/acceptance; record exact result, no release.

Status: pre-change plan, implementation and verification pending.
