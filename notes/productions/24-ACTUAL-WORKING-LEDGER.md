# Actual-Working Feature Ledger (A–Z)

**Audit date:** 2026-11-18
**Source baseline:** `58c87e2b4de27e5a0510b628a623fcf6f1a1a96b`
**Interpretation:** “Implemented” means a source path exists. “Core CI verified” is limited to the exact GitHub runner/test contract recorded in `16`–`18`. Neither label promises arbitrary-machine behavior, target-site acceptance, or detection avoidance.

## A–Z Feature Status

| ID  | Feature                              | Actual source state                                                                                             | Verification and boundary                                                                                       |
| --- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| A   | Async/sync launch API                | Implemented; sync launch owns a managed loop; page/session helpers remain async-only where documented           | Real Camoufox lifecycle included in scoped CI; sync convenience calls that cannot await raise `AutomationError` |
| B   | Bulk runner                          | Bounded concurrency, ordered per-profile results, retry/backoff, cancellation, and task timeout are implemented | Source/unit coverage; large-scale real multi-browser load is not certified; timeout is task-only                |
| C   | Camoufox native configuration        | Native Camoufox launch configuration is used; selected config/seeds are forwarded                               | Partial contract; not every generated BrowserForge value is applied or browser-visible                          |
| D   | Coherent identity generation         | BrowserForge provider, pluggable provider protocol, validation/scoring helpers exist                            | Generation is implemented; complete generated-to-browser parity is not guaranteed                               |
| E   | Deterministic seed                   | Per-profile device/locale/timezone seed persistence exists                                                      | Partial: complete fingerprint reproducibility is limited by BrowserForge process-global randomness              |
| F   | GeoIP proxy binding                  | Geo resolution, policy, locale/timezone handling, and proxy path exist                                          | Core/local tests do not certify external provider accuracy or third-party proxy egress                          |
| G   | Persistent sessions                  | Per-profile paths, storage-state persistence, and guarded lock/reset behavior exist                             | Lifecycle and filesystem checks passed within the recorded CI hosts; arbitrary filesystems are outside scope    |
| H   | Human behavior hooks                 | Async movement/type/scroll/dwell helpers and persisted behavior profiles exist                                  | API/source exists; sync helper variants intentionally reject; no behavior-evasion guarantee                     |
| I   | Installable package                  | Setuptools wheel and source distribution are defined                                                            | Clean wheel/sdist install passed in recorded CI; current local environment is missing test dependencies         |
| J   | JSON configuration                   | Pydantic config plus JSON file import/export exists; default export redacts secrets                             | Core config/security checks are recorded; explicit secret-inclusive export remains sensitive                    |
| K   | Structured logging                   | Loguru integration and profile-owned severity/scrubbing wrapper exist                                           | Profile-owned records are scoped/tested; legacy module-global records are not profile-isolated                  |
| L   | Multi-profile isolation              | Separate profile roots, lock ownership, and storage-state isolation code exist                                  | Specific lifecycle/ownership checks passed in CI; no universal cross-filesystem guarantee                       |
| M   | Proxy rotation                       | Standalone `ProxyManager` supports multiple proxies and selection/failover                                      | Engine construction is configured around a profile's proxy; do not promise an integrated arbitrary pool API     |
| N   | No JavaScript spoofing by default    | Default fingerprint behavior uses the browser engine path                                                       | `js_noise` is an explicit opt-in experimental JavaScript exception and may be detectable                        |
| O   | Retry/backoff                        | Orchestrator retry/backoff implementation exists                                                                | Unit/CI coverage for bounded contracts; no production-scale throughput claim                                    |
| P   | Pluggable identity provider          | `IdentityProvider` protocol and default BrowserForge provider are implemented                                   | Covered by provider tests/CI; no claim that custom providers produce browser parity automatically               |
| Q   | Proxy health/failover                | Health check and selection code exist                                                                           | Controlled/local protocol checks exist; real external proxy health/egress is unverified                         |
| R   | Reusable package                     | Python library with config, engine, session, GeoIP, and orchestration APIs                                      | Package build/install is verified in CI; no GUI/admin layer is in this repository                               |
| S   | Seed reproducibility                 | Persistent numeric seeds and stable profile metadata exist                                                      | Partial: BrowserForge's process-global randomness prevents claiming identical complete identities               |
| T   | Locale/timezone/currency consistency | Locale/timezone resolution and consistency reports exist                                                        | Partial: currency is metadata, not a browser override; behavior depends on explicit GeoIP/config choices        |
| U   | Typed error model                    | Shared `StealthEngineError` hierarchy and module-specific subclasses exist                                      | External/Pydantic errors may remain distinct; see [error register](23-ERROR-HANDLING-AUDIT.md)                  |
| V   | Versioned config                     | `schema_version` field exists                                                                                   | Source/model behavior is present; forward migration policy beyond current schema is not independently certified |
| W   | WebRTC leak prevention               | Camoufox GeoIP and guarded manual IPv4 hint handling exist                                                      | Partial: no proxy-specific DNS/STUN/WebRTC leak-free guarantee                                                  |
| X   | Session export                       | Storage-state import/export and selective domain export exist                                                   | Core lifecycle/storage checks are in CI; arbitrary cross-version/profile migration is not certified             |
| Y   | YAML/JSON import-export              | Config load/save APIs are implemented; YAML dependency is declared                                              | CI package/config checks passed; defaults intentionally redact credentials                                      |
| Z   | Zero global state                    | Most profile state is instance/profile scoped                                                                   | Partial: BrowserForge mutates process-global random state; Loguru retains process-global handlers               |

## Verified Core Release Scope

The published v0.3.0 Core Preview has recorded CI evidence for Linux/Windows test matrices, real Camoufox launch/readback checks on the specified runners, direct-host checks, controlled localhost HTTP proxy behavior, filesystem checks, package build/install, and dependency audit. Consult [16](16-CORE-PRODUCTION-ACCEPTANCE.md) and [18](18-CORE-RELEASE-PUBLICATION-EVIDENCE.md) for exact run/tag provenance.

Do not extend this verified label to third-party proxies, arbitrary network paths, arbitrary end-user Windows policies, complete identity parity, or a claim that automation avoids site controls.

## Not Working / Unsupported / Deferred

- `record_video_dir`: configuration is recognized but launch is rejected for the Firefox backend.
- `cdp_session`: method exists with a typed unsupported path for Firefox/Juggler.
- Sync page/state/human helper methods: async-context operations intentionally raise and direct callers to async alternatives.
- Engine-integrated profile proxy-pool API: not exposed as an automatic pool interface; the standalone manager is a separate capability.
- End-to-end runner timeout covering engine launch and cleanup: not implemented by the task-only timeout contract.
- N54 scheduled identity rotation and N56 A/B comparison harness: optional roadmap items deferred, not production blockers.
- External proxy/DNS/WebRTC acceptance and full dependency lock: not established by the current Core Preview release.

## Phase Attribution

PH-01…PH-21, BF-01…BF-04, PF-01…PF-04, and the five P-01…P-05 source patches are historical completed implementation work. This ledger is a current status overlay, not a claim that every historical feature has equal evidence. New evidence must include source SHA, environment, exact capability exercised, and result before a status is promoted.
