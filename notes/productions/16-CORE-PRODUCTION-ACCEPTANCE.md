# Core Production Release Acceptance — GitHub Actions

**Date:** 2026-11-16  
**Status:** **CORE_CI_ACCEPTED — scoped core release candidate; no release or deployment**  
**Immutable tested GitHub commit:** `e94b4f613d856ff62bb7c2699e29ecdfc9694955`  
**Verified workflow:** [Production Validation Run #8](https://github.com/JILLU-Games/stealth-engine/actions/runs/43948468121) (completed **SUCCESS**)

## Approved release scope

The owner explicitly chose to test and ship the **direct-host core** and the
**controlled local proxy protocol contracts** without an external proxy account.
The approved scope is **not** a certification of live third-party proxy behavior.

- Direct-host Firefox/Camoufox: public outbound IPv4 observed over HTTPS, DNS
  resolution and expected runner egress; `target_ip` is a WebRTC hint, not
  an override of browser outgoing IP.
- Local deterministic HTTP proxy: real loopback socket, authenticated GEO
  handshake, incorrect-password denial, actual Camoufox request forwarding to
  a synthetic `.invalid` hostname. The browser test synthesizes proxy GEO
  metadata **only** to avoid contacting an uncontrolled geo service.
- Existing real local SOCKS4a/SOCKS5 wire tests remain in full regression.
  **No real external SOCKS provider was tested.**
- Profile lifecycle, two-process ownership/recovery, private profile file
  permissions, secure config export and explicitly scoped structured logging.
- Real 2D canvas and WebGL readback consistency, software WebGL on Linux via
  Xvfb/Mesa, actual Windows headless Camoufox, tracker routing.
- Clean package wheel/sdist installs, dependency vulnerability audit and
  complete baseline regression matrix.

## Exact GitHub Actions acceptance evidence

| Required CI job | Actual verified result |
|---|---|
| Ubuntu Python 3.10 | **245 passed / 0 failed / 4 deliberately skipped** |
| Ubuntu Python 3.11 | **245 passed / 0 failed / 4 deliberately skipped** |
| Ubuntu Python 3.12 | **245 passed / 0 failed / 4 deliberately skipped** |
| Ubuntu Python 3.13 | **245 passed / 0 failed / 4 deliberately skipped** |
| Windows 2022 Python 3.12 | **244 passed / 0 failed / 5 deliberately skipped** (one POSIX-only case) |
| Real Camoufox — Ubuntu | **9/9 passed**, 0 skipped, real headed Firefox under Mesa/Xvfb |
| Real Camoufox — Windows | **9/9 passed**, 0 skipped, headless Firefox |
| Direct host public HTTPS/IP | **1/1 passed**; no proxy |
| Local HTTP proxy + real browser | **2/2 passed**, proxy auth + routing |
| POSIX private file modes | **PASS** |
| Windows NTFS ACL broad-principal inspection | **PASS** on Windows-2022 runner |
| F-19 profile-owned raw Loguru record sanitization | **PASS** |
| Dependency audit (`pip-audit`) | **PASS**; no known vulnerabilities in tested install |
| Wheel/sdist/clean installation | **PASS** on Ubuntu and Windows |
| Core aggregate verdict | **CORE_CI_ACCEPTED**, overall workflow **SUCCESS** |
| External real proxy | **SKIPPED intentionally**; NOT certified |

**Evidence:** Run #8 archived **14 CI artifacts**, including JUnit results,
dependency versions, packages and the dependency-audit JSON. No browser mock or
import stub was used for the real browser / direct-host / local-proxy suites.
Actual Linux WebGL required a supported Mesa + Xvfb session; the original
headless-no-GL environment failure was not silenced or converted into PASS.

## Precise exclusions — do NOT present as accepted

1. **Real external HTTP/SOCKS proxy** authentication, third-party exit IP,
   reliability, remote DNS and WebRTC leak properties: **NOT VERIFIED**.
2. Direct mode IP check does not establish a general IP-anonymity guarantee,
   secure WebRTC on other machines, or proxy DNS/WebRTC leak safety.
3. Generated identity values are proposals. Full browserforge-to-browser
   parity is not guaranteed by Camoufox and was not certified here.
4. Experimental JS noise changes and non-native fingerprint hooks may be
   detectable. No guarantee against anti-bot/abuse detection is made.
5. F-19 `ProfileLogger` protects profile-owned records and per-profile severity
   only. **Legacy module-global Loguru records remain process-global**, outside
   this narrow contract; do not promise module-wide profile-isolated logs.
6. Windows ACL pass applies to the exact GitHub Windows-2022 runner and its
   temporary user filesystem. It is **not** proof of all domain/NAS/network
   file storage policies.
7. Video capture, CDP and other explicitly unsupported Firefox-specific
   capabilities remain unsupported. No feature expansion was authorized.
8. The current dependency installer captures `pip freeze` artifacts, but there
   is **no committed full transitive dependency lock**. Repeatable future
   installs require a separate approved release-lock/provenance step.

## Release decision & change control

**Scoped decision: CORE CI ACCEPTED / CORE RELEASE CANDIDATE PREPARED.**

This confirms all **required Core CI jobs** on the tested GitHub hosts.
It does **not** authorize claiming the **full proxy-enabled engine** is
production-verified. It also does not prove operation on arbitrary user PCs,
websites, networks or future dependency versions.

There is **no GitHub tag, GitHub Release, publication, deployment or live
third-party proxy run**. Shipping a production package should follow
dependency/version provenance, release notes, and explicit operator approval.

GitLab mirror should be checked against this tested source before publication.
The original immutable audit files (11–15) retain their historical meaning;
this report supersedes their older release-status snapshot for the **Core** scope.
