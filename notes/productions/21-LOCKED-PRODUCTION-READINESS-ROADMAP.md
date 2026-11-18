# Locked Production-Readiness Roadmap

**Plan date:** 2026-11-18
**Starting source baseline:** `58c87e2b4de27e5a0510b628a623fcf6f1a1a96b`
**Status as of 2026-11-18:** PR-01, PR-02, and the authorized localhost-only PR-03 scope are complete; PR-04/PR-05 have not started. External proxy/DNS/WebRTC acceptance remains unverified. No product-code phase is in progress.

## Roadmap Summary

The recorded PH-01…PH-21, BF-01…BF-04, PF-01…PF-04 implementation tracks are complete; the BF-05 documentation sweep is also recorded complete. P-01…P-05 source patches are applied. Therefore there are **zero unstarted phases in those historical implementation roadmaps**. This roadmap contains **five readiness/acceptance phases**: **3/5 complete, 2/5 not started**. They are not five promised source-code features.

No additional anti-detection or third-party-target automation feature is proposed. All network acceptance must be limited to owner-authorized infrastructure and controlled endpoints. No phase may claim bypass, undetectability, or universal production behavior.

## Completed A–Z Implementation Traceability

This crosswalk prevents completed feature work from being mistaken for pending work. Status means the historical phase log records the change as complete; current runtime and evidence limits remain in [the A–Z ledger](24-ACTUAL-WORKING-LEDGER.md).

| Feature IDs   | Completed phase records                       | Historical update scope                                                                                            |
| ------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| A             | PH-01…05, PH-11, PH-19…21, BF-01/BF-05, PF-01 | Launch/session API, task controls, async lifecycle and verification examples                                       |
| B, O          | PH-11, BF-03                                  | Bounded orchestration, retry/timeout behavior, re-entry guard                                                      |
| C, D, E, S, Z | PH-02…05, PH-14, PH-17, P-04, PF-01           | Persisted seeds, provider/identity contract, supported browser config mapping, diversity and truthful limitations  |
| F, M, Q, T, W | PH-08…13, P-03, PF-03                         | GeoIP policy/resolution, proxy schemes/health handling, locale/timezone decisions and guarded WebRTC hint behavior |
| G, L, X       | PH-02…07, PH-16, P-02, BF-01/BF-02            | Profile paths, owner locks/reset, state persistence/export and isolation checks                                    |
| H             | PH-11, PH-15, BF-03, PF-02                    | Async interaction hooks, persisted behavior profile, and explicit sync-helper limitations                          |
| I, V          | PH-01…05, PH-12, PF-04                        | Config schema/package metadata and v0.3.0 build/release preparation                                                |
| J, Y          | PH-06, P-04                                   | JSON/YAML profile IO and redacted-by-default export contract                                                       |
| K, U          | PH-01…05, P-04, BF-03                         | Typed exception boundaries, profile-owned logger behavior, and error sanitization fixes                            |
| N             | PH-20, P-05, PF-03                            | Default no-JS-spoofing contract, opt-in experimental `js_noise`, route behavior and documented limitations         |
| P             | PH-06                                         | Pluggable identity-provider protocol and default provider                                                          |
| R             | PH-18                                         | Reusable package helpers and practical API surface                                                                 |

These phase records cover all 26 feature labels. They do not imply that every feature is fully implemented, live-tested, or suitable for arbitrary environments; consult the status and evidence columns in document `24` before making such a claim.

## PR-01 — Reproducible Local Verification

**Goal:** Replace the current local collection blocker with a dependency-complete, reproducible test result before considering code changes.

**Scope Lock**

- Allowed: ignored local environment only (for example `.venv`); run declared package/test installation and existing tests; record interpreter and dependency versions in the phase log.
- Forbidden: product source, tests, `pyproject.toml`, workflows, dependency pins/lockfiles, runtime profiles, network credentials, release/tag changes.

**Prerequisites:** Complete. Python 3.12 is supported; the user authorized starting this next phase. Dependencies were installed only in ignored `.venv/`; no release credentials/snapshots were used.

**Exit criteria:** `python -m compileall -q stealth_engine tests examples` passes; full `python -m pytest -q` completes; every skip is expected and explained; exact command, interpreter, dependency versions, counts, and exit code are logged. Setup failure is not a test pass.

**On failure:** Record the first reproducible failure and request a new, narrow source/test Scope Lock. Do not patch during this verification phase.

**PR-01 result (2026-11-18): COMPLETE.** Windows Python 3.12.0 isolated `.venv`; `pip install -e . pytest` succeeded; `pip check` found no broken requirements; `compileall` passed; `pytest -q -rs` reported **245 passed, 5 skipped, 32 subtests passed**, exit code 0. Skips: one POSIX-only permissions test, two `STEALTH_SMOKE` tests, and two `STEALTH_CANARY` tests. Four `aiohttp.BasicAuth` deprecation warnings were recorded; no code was changed. See [phase log](22-PRODUCTION-READINESS-PHASE-LOG.md).

## PR-02 — Documentation/Contract Reconciliation

**Goal:** Make maintained project/reference docs match the frozen source and Core Preview limitations.

**Scope Lock**

- Allowed: `MEMORY.md`, `README.md`, `project/modules/engine.md`, specific stale `project/features/*.md`, `docs/FEATURES.md`, `docs/MODULES.md`, relevant non-frozen `notes/` indexes/status reports.
- Forbidden: all `stealth_engine/` and `tests/` files, API/schema changes, workflow/release edits, and `docs/ROADMAP-v2-FREEZE.md` without separate owner approval.

**Required corrections:** v0.3.0/Core Preview status and test evidence; launch-kwargs documentation; async-only session helper behavior; unsupported video/CDP; partial identity/reproducibility; profile-vs-global logging boundary; notes tracking/manifest policy. Historical notes must stay clearly labeled historical and retain their original evidence.

**Exit criteria:** every edited statement is cross-checked against source or pinned CI evidence; no historical result is rewritten as current; local links resolve; docs diff contains no source/test/workflow change.

**Separate Scope Lock amendment (2026-11-18):** The owner separately authorized `docs/SECURITY.md` as the sole additional product/reference file. No other path was added to the PR-02 content scope; the amendment and execution proof are in `notes/2026-11-18-security-doc-scope-plan-log.md`.

**PR-02 result (2026-11-18): COMPLETE.** The allowlisted docs and separately authorized `docs/SECURITY.md` now describe source-/release-evidence-backed controls and limits. No source, tests, workflows, API/schema, UI, release, or frozen roadmap changed. PR-03 remains a separate gate requiring its own authorization and an authorized endpoint policy.

## PR-03 — Authorized Network/Browser Acceptance

**Goal:** Decide whether the explicit external-network exclusions are acceptable or require additional authorized evidence.

**Scope Lock**

- Allowed: execute existing CI/browser checks against owned or explicitly authorized test infrastructure; store sanitized results in the phase log; use controlled endpoints only.
- Forbidden: third-party target websites, unowned proxies/accounts, credentials in chat/notes/logs, new evasion behavior, fingerprint-spoofing enhancements, or edits to runtime/test/workflow files unless a separate Scope Lock is approved.

**Prerequisites:** PR-02 complete; written owner authorization for the network/browser checks, defined endpoint/operator, safe secret handling in the CI secret store, and a stated test policy. No credentials are requested or stored in this planning set.

**Exit criteria:** Record exactly which authorized checks ran and their source SHA, OS, browser/dependency versions, result and limitations. A skipped gate remains `NOT VERIFIED`; passing a direct-host/local-proxy check does not certify external proxies or general DNS/WebRTC privacy.

**PR-03 result (2026-11-18): COMPLETE — authorized localhost-only scope.** The controlled proxy protocol test and real Camoufox-through-loopback test each passed on the frozen source SHA; exact commands, environment, warnings, and scope audit are in [the PR-03 phase log](22-PRODUCTION-READINESS-PHASE-LOG.md) and [the local plan/log](../2026-11-18-pr03-localhost-plan-log.md). No direct-host or external-proxy checks ran. Third-party proxy, external DNS/WebRTC, and arbitrary-host behavior remain **NOT VERIFIED**; this completion does not certify those behaviors.

## PR-04 — Dependency/Build Repeatability Decision

**Goal:** Decide whether a cross-platform dependency lock and stronger build provenance are required for the next release.

**Scope Lock**

- Allowed only after explicit approval: `pyproject.toml`, one selected lock/snapshot mechanism, the smallest necessary packaging workflow/helper files, and dependency/release documentation.
- Forbidden: runtime behavior changes, broad dependency upgrades, silent version-range changes, release publication, signing claims, or edits to unrelated tests/modules.

**Prerequisites:** PR-01 green; owner chooses supported Python/OS matrix and lock format.

**Exit criteria:** clean wheel and sdist build/install from the selected locked inputs on the supported matrix; `pip check`/dependency audit evidence recorded; artifact/source SHA and limitations recorded. If no lock is desired, record an explicit waiver and retain the current non-reproducibility caveat.

## PR-05 — Release Readiness Decision

**Goal:** Make an explicit Core Preview continuation, new prerelease, or no-release decision from the completed evidence.

**Scope Lock**

- Allowed: release checklist, release notes, and minimal release-workflow changes only when separately approved.
- Forbidden: moving/replacing the existing `v0.3.0` tag, publishing without explicit owner approval, claiming external-proxy certification from Core CI, changing source/API as part of a docs-only release, or altering frozen roadmap content.

**Prerequisites:** PR-01 and PR-02 complete; PR-03 explicitly dispositioned; PR-04 complete or waived; clean exact candidate SHA and required CI green.

**Exit criteria:** Owner records `RELEASE`, `DEFER`, or `NO-GO`; all claims map to immutable artifacts/CI; limitations and skipped gates remain visible. Release publication is a separate authorized operation, not an automatic consequence of this roadmap.

## Phase Order / Change Control

1. PR-01 environment evidence.
2. PR-02 docs contract alignment (may proceed after baseline freeze; do not change frozen docs).
3. PR-03 controlled acceptance decision/evidence.
4. PR-04 lock/provenance decision and, only if approved, implementation.
5. PR-05 owner release decision.

Each phase is an independent Scope Lock. If evidence reveals a product defect, stop, record it, and obtain a new phase authorization before editing code. Do not combine independent phases into one broad patch. Update [the execution log](22-PRODUCTION-READINESS-PHASE-LOG.md) after every phase; no phase is complete without its evidence and exact SHA.
