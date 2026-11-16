# Release Gate — GitHub Actions Production Validation Evidence

**GitHub private repository:** https://github.com/JILLU-Games/stealth-engine  
**Baseline imported from GitLab:** `54d7f801d32e814a7b38cde42f5bf8f32fff0e8b` (179 exact Git blob matches at initial mirror)  
**Evaluated GitHub patch head:** `47c0b6d6efb36222459025fd4e156e7e487ab408`  
**Scope:** release-regression fixes, controlled acceptance tests, CI/reporting, no tag/release/deployment.

## Actual GitHub Actions evidence

| Run | Revision | Direct observation |
|---|---|---|
| [#1](https://github.com/JILLU-Games/stealth-engine/actions/runs/43933777427) | `965b7873` | Real Camoufox 4/4 each platform and packaging pass; 2 obsolete redaction-expectation failures per regression matrix, external proxy skipped |
| [#2](https://github.com/JILLU-Games/stealth-engine/actions/runs/43937468849) | `d2d24c31` | Legacy test contract corrected without restoring plaintext defaults; Linux regressions pass; Windows 0 test failures but CI skip validator incorrectly expected 4 rather than 5 |
| [#3](https://github.com/JILLU-Games/stealth-engine/actions/runs/43938348534) | `4f9be0d9` | Full regression matrix green, real browser sync/locale/tracker checks passed, but Ubuntu native canvas `toDataURL()` repeated read varied |
| [#4](https://github.com/JILLU-Games/stealth-engine/actions/runs/43939409758) | `da291fa8` | Canvas URL repeatability corrected, but Linux native `getImageData()` repeated read differed |
| [#5](https://github.com/JILLU-Games/stealth-engine/actions/runs/43940238583) | `47c0b6d6` | **Four regression matrices PASS, two real-browser suites PASS (8/8 each), both packaging jobs PASS, scoped F-19 nested-record test PASS.** External proxy SKIPPED; aggregate correctly **NO-GO** |

### Scope of actual fixes

- **RG-01:** Default JSON/YAML export continues to redact credentials. Legacy plaintext round-trip test expectations were replaced with safe-default plus explicit `include_secrets=True` backup checks.
- **RG-01 F-19 scoped logger:** Nested structured extras are sanitized recursively, with raw Loguru `record["extra"]` assertions and per-profile severity checks. This does **not** grant global/module logger profile isolation.
- **RG-02:** Cross-process Windows/Linux owner-only lock + reset tests, dead-process takeover and recovery, real sync Camoufox lifecycle, actual hardware/timezone/browser-language readback, stable canvas readback and destination-host tracker routing. Windows's POSIX-only test is an explicitly recognized skip.
- **RG-02 follow-up:** Real Linux Camoufox confirmed F-16 inconsistencies that synthetic JS tests missed. Opt-in JS noise serializations now cache unchanged 2D canvas export and region reads until canvas mutation, with bounded per-canvas read cache. Experimental/detectability caveat remains; no production spoofing guarantee.

### Verified GitHub-hosted gates after run #5

| Gate | Evidence / remaining acceptance |
|---|---|
| G-01 lifecycle | Real sync launch/close, async launch/close PASSED on Ubuntu and Windows; no destructive crash/failure chaos campaign |
| G-02 ownership | Two-process deny/reset and dead-process recovery PASSED on both; NTFS ACL/mixed-version interoperability remains |
| G-03 external HTTP/SOCKS | Local wire mock tests PASS; **authorized real proxy auth, egress and TLS NOT RUN** |
| G-04 WebRTC/DNS | Public-IP hint guard source/offline tested; **controlled DNS/WebRTC leak proof NOT RUN** |
| G-05 fingerprint | Browser-visible hardware, locale, timezone PASSED in actual Camoufox; full generated-to-browser fingerprint parity not certified |
| G-06 secure export | Secure defaults + private backup contract PASS in Linux/Windows tests; Windows NTFS ACL security not independently certified |
| G-07 scoped logging | Structured nested secret scrub/level checks PASS. Legacy module-global logging remains a known limitation |
| G-08 JS/tracker | Real 2D canvas and local routing PASS on both platforms; WebGL live readback/detectability limits remain |
| G-09 full regressions | Ubuntu Py3.10/3.12/3.13 and Windows Py3.12 **PASS**, no failed tests; 4 expected env-gated smoke skips Linux, 5 skips Windows (including POSIX-only permission test) |
| G-10 supported OS | Real browser/packaging run on Ubuntu 24.04 and Windows 2022 CI hosts; personal-user/older Windows environments not certified |
| G-11 packaging | sdist, wheel, clean venv installation PASS on both |
| G-12 CI/release | GitHub Actions tests and artifacts exist; **dependency security scan and external acceptance before production sign-off**, no release/tag published |

## Release criteria and blockers

**Status: NO-GO / NOT PRODUCTION READY** until all required scope-specific gates are verified. Specifically:

1. Authorized external proxy configuration is absent. Add GitHub repository Actions secrets `CI_PROXY_SERVER`, optional `CI_PROXY_USERNAME`/`CI_PROXY_PASSWORD`, `CI_EGRESS_JSON_URL` (a controlled credential-free HTTPS JSON `{"ip":"..."}` endpoint) and `CI_EXPECTED_EXIT_IP`; dispatch with `run_external_proxy=true`. Do not paste credentials into chat, commits, or CI logs.
2. External egress success **does not** certify DNS/WebRTC leakage. A controlled test endpoint and defined acceptance policy are required separately.
3. Profile-scoped F-19 logging is tested; module-level Loguru handlers still do not inherit the profile-level filtering contract. A separate implementation/waiver decision is necessary.
4. Windows NTFS ACLs, full WebGL readback and the generated-to-visible fingerprint contract are not comprehensively accepted. Dependency security audit is being introduced as an explicit required CI job.
5. CI artifact success is not permission to tag/release. Reproducible dependency/version constraints, audited release provenance and risk sign-off remain for the final candidate.

GitLab source was not silently modified by these GitHub-side acceptance patches. The GitHub mirror now contains additional commits; explicitly verify/synchronize before treating GitLab as an identical mirror.
