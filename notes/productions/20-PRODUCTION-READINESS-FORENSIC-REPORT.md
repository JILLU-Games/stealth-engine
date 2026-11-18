# Production-Readiness Forensic Report

**Audit date:** 2026-11-18
**Source baseline:** [`58c87e2b4de27e5a0510b628a623fcf6f1a1a96b`](19-CURRENT-BASELINE-FREEZE.md)
**Decision:** **Core Preview accepted within its recorded CI scope; full external-proxy production readiness is not established.** This report distinguishes old source findings, their code disposition, and remaining release evidence.

## Audit Method

The current local source and test tree were checked at the frozen SHA; current GitHub `main`, the `v0.3.0` tag/release, CI workflow files, current release evidence, historical finding records, phase logs, and status ledgers were compared. No code was changed. The initial system-Python pytest collection was blocked by missing `aiohttp` and `browserforge`; the later PR-01 isolated `.venv` run is recorded separately below.

## PR-01 Local Verification Update (2026-11-18)

The supported Windows Python 3.12.0 isolated environment installed the editable package and pytest. `pip check` and `compileall` passed. Full `pytest -q -rs` result: **245 passed, 5 expected skips, 32 subtests passed, exit 0**. The five skips were one POSIX-only permission test, two real-browser smoke tests, and two fingerprint canaries; the latter four were intentionally gated because this was not a live-browser phase. Four `aiohttp.BasicAuth` deprecation warnings occurred under aiohttp 3.14.5. No source/test/config/workflow files were changed.

## Historical Source Findings and Current Disposition

| Finding                                        | Current disposition at frozen source                                                                                  | Remaining boundary                                                                     |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| F-01 sync launch loop lifecycle                | Patched; managed loop lifecycle exists; real launch/close covered by scoped CI evidence                               | Arbitrary Playwright integrations/platforms are not certified                          |
| F-02 initial page coroutine                    | Patched; initial page is awaited/created through async path                                                           | None identified in current accepted Core scope                                         |
| F-03 generated identity not fully applied      | Contract narrowed; supported hardware-concurrency/config values are mapped and unsupported proposals are not promised | Full BrowserForge-to-Camoufox parity is not guaranteed                                 |
| F-04 changed locale/timezone vs persisted seed | Patched; explicit values update persisted metadata while numeric seeds remain stable                                  | Full fingerprint reproducibility remains limited by provider behavior                  |
| F-05 SOCKS health-check protocol               | Native local SOCKS protocol path and wire tests are present                                                           | Third-party proxy, external egress, and provider interoperability not verified         |
| F-06 launch-failure cleanup                    | Cleanup path patched; failure/cancellation tests and Core lifecycle gates recorded                                    | Chaos/failure coverage outside tested cases is not implied                             |
| F-07 live PID lock recovery                    | Patched to require evidence of a dead process; current Windows liveness checks process exit state                     | Mixed-version/network-filesystem behavior beyond CI not certified                      |
| F-08 owner-only lock release                   | Patched with per-instance ownership token and guarded release                                                         | Arbitrary shared storage behavior not certified                                        |
| F-09 active-profile reset                      | Patched to fail closed for live or unverifiable owners                                                                | Existing user data must not be reset as part of unrelated testing                      |
| F-10 config export secrets                     | Redacted-by-default export and explicit secret opt-in are present; release regression gate passed                     | Secret-bearing export remains an explicit sensitive operation; follow local policy     |
| F-11 proxy parse error redaction               | Sanitized parse/validation path is present                                                                            | Do not assume every third-party exception/log sink is sanitized                        |
| F-12 malformed proxy authority                 | Host/port validation is present                                                                                       | External endpoint correctness still requires authorized integration evidence           |
| F-13 invalid mobile preset                     | Invalid preset was removed from selectable preset names                                                               | This is an intentional compatibility boundary, not a pending implementation            |
| F-14 `auto` Geo consistency                    | Resolved-value comparison is present                                                                                  | External GeoIP provider accuracy/availability is not certified                         |
| F-15 WebRTC IP hint                            | Non-global/manual hint handling is guarded                                                                            | No general DNS, STUN, NAT, or WebRTC leak guarantee                                    |
| F-16 repeated JS read consistency              | Read stability fixes and real-browser Core checks are recorded                                                        | `js_noise` remains experimental; no concealment/evasion guarantee                      |
| F-17 tracker hostname matching                 | Hostname-boundary matching and live Core routing checks are recorded                                                  | Do not infer universal site/request-routing coverage                                   |
| F-18 first-seen age history                    | Separate durable first-seen metadata and migration handling are present                                               | Age lost before migration cannot be reconstructed                                      |
| F-19 profile logging                           | Scoped logger level and nested-value sanitization are tested in the Core release scope                                | Legacy module-global Loguru records remain process-global/outside the profile contract |

These are the 19 historical P-01…P-05 findings. They are **not 19 currently open source bugs**. The patches were applied before the release; current work is to preserve scope truth and finish only explicitly selected acceptance/documentation tasks.

## Additional Historical Production-Audit Items

| Item                                                   | Disposition                                                                                                      | Remaining boundary                                              |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| B-24 `new_page()` coroutine misuse                     | Fixed; async page API added and sync form rejects clearly                                                        | Sync convenience methods are intentionally unsupported          |
| B-25/B-26 sync human hooks and dwell position          | Fixed by explicit unsupported errors and async alternatives/state tracking                                       | Use documented async API; no promise of human-behavior fidelity |
| B-27/B-28 invalid launch kwargs and smoke-test masking | Fixed; launch patch settings are passed through supported configuration; real smoke gate fails on launch defects | Tested Camoufox release/runner only                             |
| B-29 CDP on Firefox/Juggler                            | Documented unsupported capability with typed failure                                                             | Not a planned implementation task for this backend              |
| B-30 WebRTC effect uncertainty                         | Current safeguards and Core checks are recorded                                                                  | Proxy-specific/browser/network leak proof remains absent        |
| B-31 release version drift                             | Resolved at v0.3.0                                                                                               | Future version changes need a new release scope                 |
| B-32 Camoufox warning noise                            | Resolved through the documented launch option                                                                    | No global warning suppression implied                           |
| B-33 Firefox video incompatibility                     | Clear rejection is implemented                                                                                   | Video recording remains unsupported for this backend            |

## Production Gaps / Decisions Still Open

1. **External network acceptance:** authorized third-party proxy authentication/egress and proxy-specific DNS/WebRTC behavior were not tested. If pursued, use only owner-authorized infrastructure and record no credentials in notes or logs.
2. **Identity claims:** generated identity values are not all applied as browser-visible values; full provider-to-browser parity and identical complete fingerprints across runs are not promised.
3. **Runtime scope:** Windows and Linux CI hosts passed the recorded Core gates; arbitrary user machines, enterprise ACLs, NAS/network filesystems, and future dependency versions are outside that evidence.
4. **Logging scope:** profile-owned records are scoped; legacy/global records are not profile-isolated.
5. **Supply-chain repeatability:** release dependency snapshot exists, but it is not a complete cross-platform transitive lock or signed provenance attestation.
6. **Conditional API contract:** video and CDP are unsupported for the current Firefox backend; sync session helpers reject; engine-level proxy-pool integration is not exposed; task timeout does not cover engine launch/cleanup. `new_context` was live-verified in the production audit and should not be listed as an unresolved failure.
7. **Local test setup:** PR-01 resolved collection in the isolated `.venv`; the system interpreter still lacks `aiohttp` and `browserforge`. Use the venv for repeatability; the venv is not a committed lockfile.
8. **Dependency deprecation:** aiohttp 3.14.5 emitted four `BasicAuth` deprecation warnings at `proxy.py:718`, noting removal in aiohttp 4.0. No failure occurred; evaluate before an aiohttp 4 upgrade under a separate source Scope Lock.

## Documentation Drift Found

- `MEMORY.md` now has the current Core Preview/test baseline; older 188-test entries remain historical phase records.
- `project/modules/engine.md` has stale version, kwargs, and sync-hook descriptions.
- `notes/browser/08-IMPLEMENTED-STATUS.md` conflicts with its completed PH-19…21 phase log.
- `docs/SECURITY.md` was initially outside PR-02's allowlist and contained unqualified guarantees for full identity coherence, WebRTC leak prevention, currency alignment, zero cross-profile sharing, and same-seed identity, plus unsupported Firefox video/CDP descriptions. A separate one-file Scope Lock was subsequently approved and completed; the document now describes source- and release-evidence-backed controls and limitations. External proxy, DNS/WebRTC, arbitrary-host, and complete fingerprint-parity behavior remain unverified.
- `docs/ROADMAP-v2-FREEZE.md` has unchecked boxes despite completed steps; it is frozen and must not be edited without owner approval.
- `notes/productions/11…15` are pre-Core-CI snapshots. Their historical results remain valid for those earlier commits, but they must not be presented as the current Core release verdict; use `16…18` for the scoped release.
- Notes policy and manifest mismatch is documented in [the baseline freeze](19-CURRENT-BASELINE-FREEZE.md); changing tracking policy is not included in this roadmap.

## Readiness Verdict

**No unstarted implementation phase from the recorded PH/BF/PF/P audit roadmaps remains.** PR-01 and PR-02 documentation reconciliation are complete, including the separately approved `docs/SECURITY.md` Scope Lock. PR-03's authorized localhost-only protocol and real-browser checks are complete; no direct-host or external-proxy checks ran, so external proxy/DNS/WebRTC behavior remains **NOT VERIFIED**. PR-04/PR-05 have not started. Core Preview is accepted only within its explicit CI scope. This is not permission to expand browser behavior or claim full external-proxy production readiness.
