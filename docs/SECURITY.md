# Security & Stealth Model

---

## Stealth Guarantees

stealth_engine provides the following stealth guarantees by design:

1. **Engine-level fingerprint overrides by default.**
   All browser fingerprint properties (UA, navigator, screen, WebGL, Canvas, fonts) are patched inside the camoufox C++ engine layer. No JavaScript `page.evaluate` or CDP `Runtime.evaluate` calls are used for spoofing.
   **Exception:** `ProfileConfig.js_noise=True` installs an opt-in init script that adds deterministic seeded noise to canvas/WebGL readbacks. This is JS-level patching, is documented as potentially detectable, and is disabled by default.

2. **Coherent identity.**
   All fingerprint attributes for a given profile are generated as a consistent set via browserforge. An observer cannot detect mismatches between, e.g., the reported OS in the UA and the WebGL renderer string.

3. **WebRTC leak prevention.**
   WebRTC local IP exposure is suppressed by camoufox's built-in geoip subsystem. No additional JS patching is required or permitted.

4. **GeoIP-consistent locale.**
   Timezone, locale, currency, and WebRTC IP are derived from the proxy's geolocation. The browser never exposes a timezone that contradicts the exit IP.

5. **Zero cross-profile state.**
   Each profile runs in an isolated `user_data_dir`. Cookies, storage, cache, and credentials are never shared between profiles or engine instances.

6. **Global state behavior is operation-dependent.**
   Importing the package does not load Camoufox/Playwright, but identity generation calls browserforge, whose installed sampler mutates the process-global `random` state. Zero global-state behavior is therefore not currently guaranteed for identity generation.

---

## Threat Model

| Threat                                               | Mitigation                                                          |
| ---------------------------------------------------- | ------------------------------------------------------------------- |
| Browser fingerprint detection (canvas, WebGL, fonts) | camoufox C++-level overrides; coherent identity via browserforge    |
| Timezone / locale inconsistency with exit IP         | GeoIP-aware proxy binding (Feature F, T)                            |
| WebRTC IP leak                                       | camoufox geoip handling (Feature W)                                 |
| Cross-session cookie / storage leakage               | Isolated `user_data_dir` per profile (Feature G, L)                 |
| Seed-based determinism enabling tracking             | Seeds are caller-controlled; random by default                      |
| Proxy identity exposure                              | Per-context proxy binding; health check before use (Feature M, Q)   |
| Log-based data leakage                               | Structured loguru logs; no raw URL or credential logging by default |

## Verified Implementation Limitations

- Proxy URL credentials are now separated from server URLs for both aiohttp and Playwright use; log-safe proxy values do not include passwords.
- `ProfileConfig.to_public_dict()` also strips embedded URL credentials and redacts their username/password fields.
- GeoIP HTTPS requests use aiohttp's default TLS certificate verification.
- The current identity generator uses browserforge sampling that consumes process-global `random` state. Its per-instance seed does not make complete fingerprints reproducible across instances.
- The generated BrowserForge identity dict is not passed wholesale to Camoufox's `fingerprint` option; coherence is enforced through per-field launch kwargs (os/locale/timezone/seeds/webgl/fonts/screen/hardware). Do not treat full identity coherence as externally verified — use `verify_stealth()`/`probe_fingerprint()` for live checks.
- BF-01..BF-04 bugfix sweep resolved 23 audit findings (unawaited async calls, Windows lock-kill, domain-filter leak, host-IP hard-fail, canvas mutation, and minors).

---

## Forbidden Regressions

The following changes are out of scope for this package:

- Replacing camoufox with plain Playwright (removes C++-level fingerprint coverage)
- Adding JavaScript-injection-based fingerprint spoofing as a fallback or *replacement* for engine-level spoofing (the opt-in `js_noise` mode is additive noise, not a replacement)
- Introducing shared mutable state between engine instances or profiles
- Breaking seed reproducibility (same seed must always yield same identity)
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
- **Session audit helpers** — implemented: `probe_fingerprint`, `verify_stealth`, `ban_risk_score`, HAR/video recording, CDP passthrough
- **TLS/JA3 fingerprint alignment** — not implemented; TLS fingerprint is controlled by the browser binary
- **Structured audit logs** — partially covered by loguru structured logs
- **Rate-limiting hooks** — not implemented (caller-side concern)
- **Profile integrity hashing** — not implemented

---

## Reporting Issues

Stealth regressions or security issues should be raised as high-priority bugs. Any change that weakens the guarantees listed in this document requires explicit sign-off before merging.
