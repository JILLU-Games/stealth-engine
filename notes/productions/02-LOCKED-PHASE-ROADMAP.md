# 02 — Step-by-Step Production Roadmap (Scope Locked)

> **Current status: P-01–P-05 code patches applied / focused offline pass; P-05 71/71 focused tests PASS. Full suite 235 PASS / 8 FAIL / 4 SKIP. Real browser, external proxy, Windows and packaging release gates BLOCKED. 0/5 fully production-accepted.**
> **Immutable source baseline:** [`a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`](https://gitlab.com/ivibtools/stealth-engine/-/commit/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5); prior source audit revision [`6255383cac9f29d64bf9ee5957c77ee26ccd7993`](https://gitlab.com/ivibtools/stealth-engine/-/commit/6255383cac9f29d64bf9ee5957c77ee26ccd7993). The 31 audited executable/config blob hashes match across these revisions.


## Non-negotiable interpretation

- `P-01 → P-02 → P-03 → P-04 → P-05` is **proposed execution order**, not authorization to run.
- 19 source-evidenced findings assigned exactly once; 6 unsupported/conditional API cases assigned to validation/decision gates. **Do not silently expand unsupported APIs into new features.**
- Each phase: baseline diff → targeted patch only in explicitly allowed paths/regions → 1 focused verification → patch audit → individual commit → log/status update. A final real-browser certification requires separately evidenced runtime execution.
- **Scope lock:** approval required to change any file/function outside the listed boundaries; otherwise mark `BLOCKED / SCOPE CHANGE REQUEST`, don't improvise.

## Exact issue-to-phase mapping

| Phase | Findings | Count | Unsupported/conditional decision gates | Completion |
|---|---|---:|---|---|
| P-01 | F-01, F-02, F-06 | 3 | U-01, U-04 | PATCH APPLIED; LIVE GATE BLOCKED |
| P-02 | F-07, F-08, F-09, F-18 | 4 | None | PATCH APPLIED; WINDOWS/LIVE GATES PENDING |
| P-03 | F-05, F-11, F-12, F-14, F-15 | 5 | U-05 (unchanged conditional) | PATCH APPLIED; LIVE/WINDOWS GATES PENDING |
| P-04 | F-03, F-04, F-10, F-13, F-19 | 5 | None | PATCH APPLIED; 61/61 focused pass; 2 legacy failures, live parity/logging blocked |
| P-05 | F-16, F-17 | 2 | U-02, U-03, U-06 (unchanged conditional) | PATCH APPLIED; OFFLINE PASS; FULL SUITE/LIVE GATES BLOCKED |

## P-01 — Browser lifecycle, sync/async safety & failure cleanup

**State:** `PATCH APPLIED — OFFLINE VERIFIED / LIVE GATE BLOCKED` ([source commit `9638c789`](https://gitlab.com/ivibtools/stealth-engine/-/commit/9638c789c7b06def4b51a54583bd728ee42e746b)). **Objective:** Session launch, initial page এবং cleanup-এর contract নিরাপদ করা; browser-backed baseline smoke সম্ভব হলে gate করা।

**Scope lock / findings:** `F-01`, `F-02`, `F-06` (3 findings). Conditional decisions: `U-01`, `U-04`.

**Allowed source regions/files ONLY:**
1. `stealth_engine/engine.py`—**শুধু** sync launch/lifecycle, initial-page setup ও emergency cleanup blocks
2. `tests/test_engine_depth.py`, `tests/test_bugfix.py`, `tests/test_forensic_regressions.py`—সংশ্লিষ্ট regression tests

**Must remain unchanged / forbidden:**
- Proxy transport/Geo logic, identity generation, config preset, request blocking, bulk orchestration, external UI
- নতুন browser framework, UI বা নতুন public API অনুমোদন ছাড়া যোগ করা যাবে না

**Ordered P-01 implementation steps (code patch applied 2026-11-16; live gate pending):**
1. Sync facade-এর supported contract নির্দিষ্ট করে managed loop অথবা safe explicit rejection test-সহ implement.
2. `BrowserSession` initial page awaited ও type-safe.
3. Failure on launch stage→close proxy, Camoufox handle এবং lock ownership; original exception preserved.
4. U-01 sync helpers ও U-04 additional context-এর documented unsupported/conditional behavior regression tests; প্রমাণ ছাড়া supported ঘোষণা নয়.

**Acceptance / exit criteria:**
- [x] Async success/failure path unit and fake-context tests green — 15/15 scoped/adjacent tests pass, test stubs acknowledged.
- [ ] Real browser launch+close and optional initial page smoke **NOT RUN** — `browserforge`/`camoufox` absent in verification environment; P-01 remains `blocked-unverified`.
- [x] Controlled fake-context success/failure paths: loop closed after close, no unawaited coroutine, lock absent, no unrelated module modifications. Real browser not tested.
- [x] Patch scope audit passed: only allowed `engine.py` lifecycle regions and `tests/test_forensic_regressions.py` changed; code commit and 15/15 test evidence in `03`.

**Baseline code anchors:** [`stealth_engine/engine.py:244-256`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L244-256), [`stealth_engine/engine.py:805-811`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L805-811), [`stealth_engine/engine.py:415-424`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L415-424)

**Blocking/rollback rule:** On failed acceptance, missing runtime dependency, external behavior mismatch, or scope drift: keep `NOT COMPLETE`, record blockers, restore/rollback the phase patch safely; do not mark production-ready.

## P-02 — Profile ownership, reset safety & durable session metadata

**State:** `PATCH APPLIED — LINUX OFFLINE 35/35 PASS; WINDOWS + REAL-BROWSER GATES PENDING`. **Objective:** Same-profile concurrent process ownership, reset and session-age correctness; destructive behavior fail-closed।

**Scope lock / findings:** `F-07`, `F-08`, `F-09`, `F-18` (4 findings). Conditional decisions: none.

**Allowed source regions/files ONLY:**
1. `stealth_engine/session.py`—lock ownership, release, force_reset only
2. `stealth_engine/engine.py`—`_record_fingerprint`/`session_age_days` metadata only
3. `tests/test_forensic_regressions.py`, `tests/test_hardening.py`, `tests/test_ghost.py`—targeted cases

**Must remain unchanged / forbidden:**
- Browser launch semantics P-01, network transport, config export, fingerprint generation, UI
- Active-profile deletion or lock takeover without ownership verification

**Ordered documented steps (implemented on 2026-11-16, current-version lock co-operation only):**
1. Atomic owner identity + PID liveness and race-aware stale recovery.
2. Only owner may release, including cross-instance and idempotent cases.
3. Force reset requires proof of no active owner; typed error and no deletion otherwise.
4. Separate immutable first_seen from capped recent history; migration rules with backup.

**Acceptance / exit criteria:**
- [x] Live-PID old lock never stolen; same-PID different-owner token tested (Linux offline).
- [x] Non-owner release/reset leaves profile unchanged; idle reset works (Linux offline).
- [x] 51+ launch history preserves first-seen; existing legacy history copied to a one-time backup before migration (Linux offline).
- [x] Patch audit verified: session lock/manager ownership and engine metadata methods only; 35/35 tests. Source commits `cb06b63b` and `e4c60c11`; log in `03`.
- [ ] Real browser/Windows OS lock and cross-version client interoperability (not run; release acceptance blocked).

**Baseline code anchors:** [`stealth_engine/session.py:275-292`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/session.py#L275-292), [`stealth_engine/session.py:307-317`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/session.py#L307-317), [`stealth_engine/session.py:323-336`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/session.py#L323-336), [`stealth_engine/engine.py:465-476`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L465-476)

**Blocking/rollback rule:** On failed acceptance, missing runtime dependency, external behavior mismatch, or scope drift: keep `NOT COMPLETE`, record blockers, restore/rollback the phase patch safely; do not mark production-ready.


**Actual P-02 evidence:** [Source patch `cb06b63b`](https://gitlab.com/ivibtools/stealth-engine/-/commit/cb06b63b10130e99c28747a95837ab901ae42dfc) → [line-ending restoration `e4c60c11`](https://gitlab.com/ivibtools/stealth-engine/-/commit/e4c60c11c62d4fcef0f8892ae484014f4324659f); [post-patch exact source blocks + tests](07-P02-VERIFICATION-EVIDENCE.md). Lock guard file persists at `<base>/.<profile>.lock.guard` after reset; `.lock` owner-token/PID check is fail-closed. Legacy `fingerprint_history.json` stays a capped list; `fingerprint_history_meta.json` stores immutable first-known timestamp. If pre-migration history was previously truncated, earlier unknown age cannot be recovered.

## P-03 — Proxy correctness, Geo consistency & WebRTC policy

**State:** `PATCH APPLIED — LINUX OFFLINE 59/59 PASS; EXTERNAL/HTTPS/WINDOWS/BROWSER GATES PENDING`. **Objective:** Network configuration validation, health-check transport, geo decisions ও WebRTC IP assertions সঠিক করা।

**Scope lock / findings:** `F-05`, `F-11`, `F-12`, `F-14`, `F-15` (5 findings). Conditional decisions: `U-05`.

**Allowed source regions/files ONLY:**
1. `stealth_engine/proxy.py`—health transport, proxy parse/redaction only
2. `stealth_engine/config.py`—**শুধু** `ProxyConfig.server` validation
3. `stealth_engine/geo.py`—**শুধু** `auto` consistency logic
4. `stealth_engine/engine.py`—**শুধু** WebRTC address acquisition/launch config
5. Relevant proxy/geo tests: `tests/test_geo.py`, `tests/test_hardening.py`, `tests/test_forensic_regressions.py`

**Must remain unchanged / forbidden:**
- General profile serialization (P-04), identity seed logic, JS behavior, product UI
- Proxy pool integration U-05 কে নতুন feature হিসেবে silently scope-এ ঢোকানো যাবে না

**Ordered implementation steps (P-03 code patch applied 2026-11-16):**
1. SOCKS4a/SOCKS5-aware GeoIP health transport implemented with native Python socket/TLS/HTTP; no external dependency added, HTTP aiohttp behavior preserved.
2. Strip credentials from parse error message, details and logs.
3. Reject empty/malformed proxy authority with valid protocol handling.
4. Geo `auto` resolution before consistency compare.
5. No private LAN IP advertised as public WebRTC egress; supported policy + network checks.
6. U-05 standalone pool-vs-profile integration status explicitly document; optional expansion deferred unless approved.

**Acceptance / exit criteria:**
- [x] Local in-process SOCKS5 (authenticated + no auth) and SOCKS4a wire greeting/GET tested; HTTP aiohttp path regression PASS. HTTPS over SOCKS is implemented with validated TLS but remains **not runtime tested**.
- [x] Invalid proxy line tests assert sanitized ProxyError message/details/no chained ValidationError; direct Pydantic error string masked in tested examples. Broader logging/unknown third-party errors still require live validation.
- [x] Valid/invalid URL authority table, socks5h alias, Geo auto/explicit conflict tests green (offline).
- [ ] External proxy egress and HTTPS over SOCKS, Camoufox WebRTC public IP/browser leak readback and Windows need consenting controlled runtime; **NOT RUN**, release gate blocked. Default direct launch omits manual IP hint if local address is not globally routed; this is not proof the browser emits no local candidates.
- [x] AST diff and Git blob audit found changes only in P-03 allowed methods of `proxy.py`, `config.py`, `geo.py`, `engine.py` and relevant tests. P-01/P-02 AST unchanged; evidence in `03` and `08`.

**Baseline code anchors:** [`stealth_engine/proxy.py:320-335`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/proxy.py#L320-335), [`stealth_engine/proxy.py:643-655`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/proxy.py#L643-655), [`stealth_engine/config.py:38-62`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L38-62), [`stealth_engine/geo.py:130-144`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/geo.py#L130-144), [`stealth_engine/engine.py:499-525`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L499-525)

**Blocking/rollback rule:** On failed acceptance, missing runtime dependency, external behavior mismatch, or scope drift: keep `NOT COMPLETE`, record blockers, restore/rollback the phase patch safely; do not mark production-ready.


**P-03 implementation evidence:** [code commit `b2d1884a`](https://gitlab.com/ivibtools/stealth-engine/-/commit/b2d1884a8e7534d28f492d9f3274eb17c5551b3a), [current exact code + local SOCKS transcripts/test results](08-P03-VERIFICATION-EVIDENCE.md). **U-05 unchanged:** no BrowserSession multi-proxy-pool integration; ProxyManager standalone pool still exists. No `pyproject.toml` dependency change; SOCKS GeoIP tunnel uses Python stdlib TLS/HTTP, and does not turn standalone pool integration into a new feature.

## P-04 — Identity contract, persistent seed precedence, safe configuration & logging

**State:** `CODE PATCH APPLIED / 61/61 FOCUSED OFFLINE PASS / 2 LEGACY FEATURE Y TEST FAIL / LIVE-WINDOWS GATES BLOCKED` ([source commit](https://gitlab.com/ivibtools/stealth-engine/-/commit/997e5dd5087d4e366dc573f561e2e9ac3a063520)). **Objective:** Identity-generation claims align with launch behavior; config secrets protected; presets and logs behave predictably।

**Scope lock / findings:** `F-03`, `F-04`, `F-10`, `F-13`, `F-19` (5 findings). Conditional decisions: none.

**Allowed source regions/files ONLY:**
1. `stealth_engine/identity.py`—persisted seed/locale/timezone only
2. `stealth_engine/engine.py`—fingerprint-launch mapping and profile log settings only
3. `stealth_engine/config.py`—JSON/YAML export and presets only; **not** proxy validator
4. `stealth_engine/utils/logging.py`—per-profile logging policy only
5. Relevant identity/config/log tests: `tests/test_hardening.py`, `tests/test_uxpack.py`, `tests/test_forensic_regressions.py`

**Must remain unchanged / forbidden:**
- Runtime profile data deletion, proxy manager transport, JS noise, request routing, UI
- Unverified fingerprint field support falsely advertised বা arbitrary browser launch kwarg ঢোকানো যাবে না

**Ordered P-04 patch decisions (implemented 2026-11-16; conditional acceptance):**
1. Backend-accepted fingerprint fields with explicit supported/unsupported mapping and consistency tests.
2. Numeric seed stability with updated explicit locale/timezone precedence.
3. Redacted-by-default JSON/YAML config with secure explicit opt-in for secrets, safe permissions.
4. Every public preset validates under supported OS contract.
5. Per-profile logging level with no cross-profile global mutation; redact secrets in error paths.

**Acceptance / exit criteria:**
- [x] Supported `navigator.hardwareConcurrency` mapping tests pass.
- [ ] Real browser-visible fingerprint parity canary **NOT RUN**.
- [x] Persistent-seed and JSON/YAML redacted-export targeted tests pass; legacy plaintext expectation **2 FAIL**, still unresolved.
- [x] Remaining public presets validate; two independent engine-owned profile loggers pass threshold/scrub tests; pre-existing global module logs **not fully covered**.
- [x] Five allowed source/test paths and current hashes checked; code, scope and test limitations logged in `03` and `09`.

**Baseline code anchors:** [`stealth_engine/identity.py:429-438`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/identity.py#L429-438), [`stealth_engine/identity.py:486-500`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/identity.py#L486-500), [`stealth_engine/config.py:260-269`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L260-269), [`stealth_engine/config.py:354-359`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L354-359), [`stealth_engine/config.py:143-149`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L143-149)

**Blocking/rollback rule:** On failed acceptance, missing runtime dependency, external behavior mismatch, or scope drift: keep `NOT COMPLETE`, record blockers, restore/rollback the phase patch safely; do not mark production-ready.

**P-04 compatibility and acceptance blockers:** default config export now intentionally drops proxy secrets; two old `tests/test_feature_p_y.py` cases expect plaintext roundtrip and fail. Under Scope Lock this out-of-scope file was **not edited**. `mobile-android` invalid preset removed from public names (breaking invalid name); Windows file ACL, live Camoufox fingerprint and legacy module-global per-profile logging remain not verified/partially unsupported. No scope expansion without approval. See [09-P04-VERIFICATION-EVIDENCE.md](09-P04-VERIFICATION-EVIDENCE.md).

## P-05 — Interaction fidelity, conditional APIs & release verification

**State:** `PATCH APPLIED / 71/71 FOCUSED OFFLINE PASS; FULL SUITE 8 FAIL / LIVE GATES BLOCKED` ([code commit](https://gitlab.com/ivibtools/stealth-engine/-/commit/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd)). **Objective:** Remaining behavior correctness, public API capability transparency এবং comprehensive final verification।

**Scope lock / findings:** `F-16`, `F-17` (2 findings). Conditional decisions: `U-02`, `U-03`, `U-06`.

**Allowed source regions/files ONLY:**
1. `stealth_engine/engine.py`—experimental JS noise and tracker URL rules only
2. `stealth_engine/orchestrator.py`—**only if explicitly approved** to change U-06 timeout contract
3. `tests/`—targeted behavior + opt-in integration/smoke gates
4. `notes/productions/`—verification ledger and phase status logs

**Must remain unchanged / forbidden:**
- Mandatory video/CDP support without backend proof; browser engine replacement, UI/admin features, whole-project refactor
- U-02/U-03/U-06 কে already-fixed বা live-tested ধরে নেওয়া

**Documented implementation steps (P-05 code applied; acceptance still pending):**
1. Identical canvas reads deterministic or experimental toggle disabled/flagged by contract.
2. Tracker matcher uses parsed destination host with redirects/query tests.
3. U-02 (video) and U-03 (CDP) explicit supported/unsupported tests and documented limitation.
4. U-06 timeout scope: current task-only behavior document; end-to-end expansion separate approval gate.
5. Run focused regression followed by one final full test suite, opt-in real browser/proxy/fingerprint canary if environment supports; document exact commands/results.

**Acceptance / exit criteria:**
- [x] Repeated canvas/WebGL readback stability and tracker false-positive regressions green in mock/Node offline tests (not live Camoufox).
- [ ] Full acceptance remains BLOCKED: 235 PASS / 8 FAIL / 4 SKIP. P-04 2 legacy failures, 3 import-stub dependency failures, 3 older fingerprint-history tests; see P-05 proof.
- [ ] Real-browser, proxy, lifecycle and artifact packaging evidence required before production-ready claim.
- [x] No new unapproved features or source files modified; U-02/U-03/U-06 and U-05 remain conditional.
- [x] Patch audit confirms only `_js_noise_init_script`, `BrowserSession.block_trackers` and additive P-05 tests changed; commit and evidence in `03` and `10`.

**Baseline code anchors:** [`stealth_engine/engine.py:84-99`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L84-99), [`stealth_engine/engine.py:1544-1559`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L1544-1559)

**Blocking/rollback rule:** On failed acceptance, missing runtime dependency, external behavior mismatch, or scope drift: keep `NOT COMPLETE`, record blockers, restore/rollback the phase patch safely; do not mark production-ready.


**P-05 completion note (2026-11-16):** 10 new P-05 tests and 61 adjacent tests pass (71/71). Full suite 8 FAIL/4 SKIP; conditional U cases remain unchanged. [Exact code and failure evidence](10-P05-VERIFICATION-EVIDENCE.md). **Implementation patch completed; production acceptance not completed.**

## After phase P-05 — release gate (not a sixth implementation phase)

- Pin final candidate commit and update manifest/diff from `a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`.
- Verify all 19 findings with source/test evidence, explicitly disposition all 6 U-cases, run complete test suite in pinned dependencies. Distinguish setup failure, test failure and skipped external test.
- Run authorized real Camoufox smoke, profile lifecycle, proxy egress/DNS/WebRTC, fingerprint readback, persistence, interactions, bulk cancellation/timeout. If a test cannot run, mark **NOT VERIFIED** and block **fully production-ready** certification.
- Confirm package build/install and release metadata; do not claim UI/admin test for a repo without UI.
- Close with `03` log, `05` ledger and exact final commit SHA. Do not add extra phases without explicit decision and versioned revision.
