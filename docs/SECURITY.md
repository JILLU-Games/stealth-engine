# Security & Runtime Assurance Boundaries

This document describes implemented controls and their evidence boundaries. It does **not** promise undetectability, account safety, universal isolation, or leak-free behavior on arbitrary browsers, proxies, networks, or hosts. The published v0.3.0 package is a **Core Preview prerelease**; see the [Core acceptance record](../notes/productions/16-CORE-PRODUCTION-ACCEPTANCE.md) and [release publication evidence](../notes/productions/18-CORE-RELEASE-PUBLICATION-EVIDENCE.md) for the exact tested scope.

## Implemented Controls and Limits

1. **Camoufox configuration.** The engine passes supported configured values and device seeds through Camoufox's launch configuration. It does not pass the full BrowserForge identity dictionary to Camoufox's `fingerprint` option; full generated-to-browser parity is not established. `js_noise` is an opt-in experimental JavaScript init-script exception and may be detectable.

2. **Identity generation.** BrowserForge produces an identity proposal that the engine validates and selectively applies. Not every generated value is applied or verified as browser-visible. BrowserForge also consumes process-global `random` state, so identical seeds do not guarantee identical complete fingerprints across generator instances.

3. **GeoIP and WebRTC configuration.** When a proxy is configured, `geoip=True`, and proxy GeoIP data is available, locale/timezone use that data and Camoufox handles its GeoIP behavior. Without that data, or when GeoIP is disabled, the ordinary locale/timezone path uses configured or persisted values; an explicit `"auto"` setting separately invokes GeoResolver and may use proxy or host GeoIP. In Mode A, a manual `webrtc:ipv4` hint is passed only for a globally routable IPv4; otherwise it is omitted. These are configuration controls, **not** a guarantee against DNS, STUN, NAT, or WebRTC leakage.

4. **Locale and currency.** Locale/timezone handling follows the selected mode and `ProfileConfig.geoip`; currency is GeoIP metadata and is not applied as a browser override. External GeoIP provider accuracy and third-party proxy behavior are not certified.

5. **Profile storage and ownership.** Profiles use separate resolved directories, storage-state files, and guarded lock ownership. The release CI exercised specified lifecycle, ownership, and filesystem cases. This does not guarantee isolation when callers deliberately reuse paths or when using untested filesystems, mounts, or host policies.

6. **Logging and process-global state.** `ProfileLogger` filters/scrubs records emitted through its profile-owned wrapper. Legacy module-level Loguru records remain process-global and do not inherit profile filters. BrowserForge's process-global randomness also means zero global-state behavior is not guaranteed.

## Release Evidence Boundary

- GitHub Actions Run #8 accepted the defined Core scope on its listed Ubuntu/Windows runners: real Camoufox checks, direct-host checks, controlled localhost HTTP proxy tests, package installation, filesystem checks, and dependency audit. See the [exact acceptance record](../notes/productions/16-CORE-PRODUCTION-ACCEPTANCE.md).
- **Not verified:** third-party HTTP/SOCKS proxy egress/authentication, external proxy DNS/WebRTC behavior, arbitrary end-user networks/filesystems, and complete BrowserForge-to-Camoufox fingerprint parity.
- A local proxy test is not evidence for an external proxy. Passing Core CI does not establish anti-bot bypass or account safety.

---

## Threat Model

| Threat / concern                              | Implemented control and limit                                                                      |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Browser fingerprint inconsistency             | BrowserForge proposal, selected Camoufox options, and readback helpers; complete parity unverified |
| Timezone / locale mismatch                    | Config/GeoIP mode selects locale/timezone; external provider correctness is not certified          |
| WebRTC / DNS / STUN exposure                  | Conditional GeoIP/manual IPv4 configuration; no general leak-free guarantee                        |
| Cross-profile storage                         | Separate profile roots and guarded locks; evidence is limited to tested cases/environments         |
| Seed-linked or non-repeatable identities      | Persisted device seeds; complete identity equality is not guaranteed                               |
| Proxy credentials and external proxy identity | Credentials are separated/redacted in covered paths; third-party proxy egress is unverified        |
| Log-based data exposure                       | Profile-owned wrapper filters/scrubs known secrets; legacy module-global logs remain global        |

## Verified Implementation Limitations

- Proxy URL credentials are now separated from server URLs for both aiohttp and Playwright use; log-safe proxy values do not include passwords.
- `ProfileConfig.to_public_dict()` also strips embedded URL credentials and redacts their username/password fields.
- GeoIP HTTPS requests use aiohttp's default TLS certificate verification.
- The current identity generator uses browserforge sampling that consumes process-global `random` state. Its per-instance seed does not make complete fingerprints reproducible across instances.
- The generated BrowserForge identity dict is not passed wholesale to Camoufox's `fingerprint` option; coherence is enforced through per-field launch kwargs (os/locale/timezone/seeds/webgl/fonts/screen/hardware). Do not treat full identity coherence as externally verified — use `verify_stealth()`/`probe_fingerprint()` for live checks.
- `GeoInfo.currency` is metadata-only. The engine does not apply a browser currency override.
- `ProfileConfig.geoip` controls GeoIP-derived browser behavior; a configured proxy does not imply that every locale/timezone override is applied.
- The Core release's Windows/POSIX permission checks cover only their listed CI runner environments; they do not prove behavior on every user machine or shared/network filesystem.
- BF-01..BF-04 bugfix sweep resolved 23 audit findings (unawaited async calls, Windows lock-kill, domain-filter leak, host-IP hard-fail, canvas mutation, and minors).

---

## Forbidden Regressions

The following changes are out of scope for this package:

- Replacing camoufox with plain Playwright (removes C++-level fingerprint coverage)
- Adding JavaScript-injection-based fingerprint spoofing as a fallback or _replacement_ for engine-level spoofing (the opt-in `js_noise` mode is additive noise, not a replacement)
- Introducing shared mutable state between engine instances or profiles
- Changing the documented stability of persisted device seeds without approval; complete same-seed fingerprint identity is not guaranteed
- Removing or weakening proxy health checks
- Storing credentials, cookies, or proxy URLs in process-global variables
- Adding any form of telemetry, external HTTP call, or data transmission not explicitly initiated by the caller
- Changing the public API signature of `StealthEngine`, `BulkRunner`, or `ProfileConfig` in a backward-incompatible way

---

## Allowed Extensions

Extensions are permitted only if they meet all four criteria from the project rules:

(a) Strictly increase stealth, security, reliability, or observability
(b) Do not weaken, slow down, or break any A-Z feature
(c) Can be layered on top without changing the public API
(d) Are documented under "Optional Advanced Extensions (Non-Breaking)"

### Extension categories

- **Fingerprint drift detection** — implemented (PH-17): `fingerprint_history.json` + diversity-mode drift warnings
- **Session audit helpers** — implemented: `probe_fingerprint`, `verify_stealth`, `ban_risk_score`, HAR recording. Video recording and CDP are unsupported on the tested Firefox backend.
- **TLS/JA3 fingerprint alignment** — not implemented; TLS fingerprint is controlled by the browser binary
- **Structured audit logs** — partially covered by loguru structured logs
- **Rate-limiting hooks** — not implemented (caller-side concern)
- **Profile integrity hashing** — not implemented

---

## Reporting Issues

Stealth regressions or security issues should be raised as high-priority bugs. Any change that weakens the guarantees listed in this document requires explicit sign-off before merging.
