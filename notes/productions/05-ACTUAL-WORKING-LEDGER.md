# 05 — Actual Working vs Code-Present vs Unsupported Feature Ledger

> **Current status: P-01–P-05 CODE PATCHED / FOCUSED OFFLINE VERIFIED; P-05 71 PASS, full suite 235 PASS / 8 FAIL / 4 SKIP. None fully production accepted; real Camoufox/Windows remain unverified.** Historical baseline probe classifications retained.
> **Immutable source baseline:** [`a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`](https://gitlab.com/ivibtools/stealth-engine/-/commit/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5); prior source audit revision [`6255383cac9f29d64bf9ee5957c77ee26ccd7993`](https://gitlab.com/ivibtools/stealth-engine/-/commit/6255383cac9f29d64bf9ee5957c77ee26ccd7993). The 31 audited executable/config blob hashes match across these revisions.


## Definitions (must not conflate)

- `OFFLINE VERIFIED` = deterministic pure-Python/probe behavior witnessed in earlier audit (not a real browser pass).
- `SOURCE PRESENT / REAL UNVERIFIED` = actual code path exists, but successful live browser/proxy workload not demonstrated.
- `SOURCE DEFECT OPEN` = source/reproduction gap mapped to `F-xx`; this does **not** imply every call fails on a live browser.
- `UNSUPPORTED / CONDITIONAL` = API explicitly throws or requires conditions; mapped to U-xx; not counted as code defect by default.
- `REAL VERIFIED` = only when actual production-like browser/API execution + recorded environment, evidence, and commit SHA pass. **None are certified at baseline.**

## Baseline feature inventory (from source and earlier isolated audit)

| Feature / API | Exact source proof | Baseline evidence | Open gap / condition | After phase evidence/status |
|---|---|---|---|---|
| Profile JSON config serialization | [`stealth_engine/config.py:249-286`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L249-286) | OFFLINE: SECURE REDACTED DEFAULT | F-10: default secrets intentionally omitted; explicit private include_secrets=True roundtrip PASS; legacy test FAIL | P-04 commit 997e5dd5 / proof 09; real browser+Windows pending |
| YAML serialization | [`stealth_engine/config.py:288-317`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L288-317) | OFFLINE: SECURE REDACTED DEFAULT | F-10: secret-safe default; opt-in private secrets PASS; legacy YAML roundtrip test FAIL | P-04 commit 997e5dd5 / proof 09; real browser+Windows pending |
| Builtin preset profiles | [`stealth_engine/config.py:345-379`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L345-379) | OFFLINE: VALID DESKTOP PRESETS | F-13: invalid mobile-android removed from selectable names, breaking invalid preset name | P-04 commit 997e5dd5 / proof 09; real browser+Windows pending |
| Proxy URL config parsing | [`stealth_engine/config.py:38-62`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L38-62) | OFFLINE PATCH VERIFIED — HOST/PORT TABLE | F-12 strict authority and F-11 error text redaction; real network unverified | P-03 source patch b2d1884a; proof 08; real browser/Windows pending |
| Fingerprint generation/provider | [`stealth_engine/identity.py:429-445`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/identity.py#L429-445) | OFFLINE: CONTRACT MAPPING ONLY | F-03 hardware concurrency mapping+advisory contract; real Camoufox fingerprint parity NOT VERIFIED | P-04 commit 997e5dd5 / proof 09; real browser+Windows pending |
| Deterministic persisted seeds | [`stealth_engine/identity.py:480-505`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/identity.py#L480-505) | OFFLINE: PERSISTED PRECEDENCE VERIFIED | F-04 locale/timezone explicit overrides persist; numeric seeds unchanged; Windows unverified | P-04 commit 997e5dd5 / proof 09; real browser+Windows pending |
| Async Camoufox launch | [`engine.py:429-475`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/stealth_engine/engine.py#L429-475) | OFFLINE MOCK VERIFIED / REAL UNVERIFIED | F-02/F-06 patched; fake initial page and failure cleanup pass | P-01 patch applied; live acceptance blocked |
| Sync launch/close | [`engine.py:258-298`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/stealth_engine/engine.py#L258-298) | OFFLINE MOCK VERIFIED / REAL UNVERIFIED | F-01: worker loop ownership / teardown; U-01 sync helper rejection retained | P-01 patch applied; real smoke pending |
| Proxy selection, health and rotation manager | [`stealth_engine/proxy.py:299-335`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/proxy.py#L299-335) | OFFLINE SOCKS WIRE VERIFIED — EXTERNAL PROXY UNVERIFIED | F-05 SOCKS5/auth/SOCKS4a local HTTP GeoIP; U-05 unchanged conditional | P-03 source patch b2d1884a; proof 08; real browser/Windows pending |
| GeoIP parsing and policy | [`stealth_engine/geo.py:34-80`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/geo.py#L34-80) | OFFLINE GEO `auto` VERIFIED — LIVE UNVERIFIED | F-14 auto resolved; explicit conflict still detected | P-03 source patch b2d1884a; proof 08; real browser/Windows pending |
| WebRTC browser policy | [`stealth_engine/engine.py:628-645`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L628-645) | OFFLINE LAUNCH KWARG VERIFIED — REAL WEBRTC UNVERIFIED | F-15 non-global manual WebRTC hints omitted; explicit invalid target rejected | P-03 source patch b2d1884a; proof 08; real browser/Windows pending |
| Persistent profile locking and reset | [P-02 current `session.py:232-407`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L232-407) | LINUX OFFLINE VERIFIED, WINDOWS/REAL SESSION UNVERIFIED | F-07/F-08/F-09 patched; guard and owner-token checks; live/unknown reset denied | P-02 patch applied; 18 new + 17 adjacent offline tests PASS |
| Storage state export/import | [`stealth_engine/session.py:349-455`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/session.py#L349-455) | OFFLINE VERIFIED: JSON round-trip | Real browser persistence not verified | P-02 ownership patched; real browser persistence still unverified |
| Session first-seen age / fingerprint history | [P-02 current `engine.py:485-551`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/engine.py#L485-551) / [`session_age_days:1674-1705`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/engine.py#L1674-1705) | LINUX OFFLINE VERIFIED, REAL SESSION UNVERIFIED | F-18 patched; sidecar metadata & backup, 50-entry cap retained; already-lost pre-migration age not recoverable | P-02 patch applied; 51+/legacy/invalid-meta tests pass |
| BulkRunner retries, concurrency and cancellation | [`stealth_engine/orchestrator.py:372-453`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/orchestrator.py#L372-453) | SOURCE PRESENT / REAL UNVERIFIED | U-06 task-only timeout; real multi-browser untested | P-05 U-06 source-contract test PASS; timeout unchanged, real unverified |
| Human movement path generator | [`stealth_engine/behavior.py:35-84`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/behavior.py#L35-84) | OFFLINE VERIFIED: Bezier point generator | Actual mouse/scroll/type in live browser unverified | P-05: live acceptance pending |
| Browser automation wrappers / upload / download | [`stealth_engine/engine.py:1271-1423`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L1271-1423) | SOURCE PRESENT / REAL UNVERIFIED | Live file actions untested | P-05: live acceptance pending |
| Request blocking / routes | [baseline source](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L1544-1559) | BASELINE SOURCE DEFECT (historical) | F-17: current hostname matching now correct in fake route tests; real browser UNVERIFIED | [P-05 code](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L1670-1717) / [proof](10-P05-VERIFICATION-EVIDENCE.md) |
| Experimental JS noise | [baseline source](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L84-116) | BASELINE SOURCE DEFECT (historical) | F-16: repeated canvas/WebGL readbacks stable in Node test double; real browser UNVERIFIED; experimental JS detectable | [P-05 code](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L87-140) / [proof](10-P05-VERIFICATION-EVIDENCE.md) |
| Risk heuristic scoring | [`stealth_engine/risk.py:24-99`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/risk.py#L24-99) | OFFLINE VERIFIED: numeric score returned | Not a real anti-bot bypass guarantee | P-05: live effectiveness remains out of scope |
| Per-profile logging | [`stealth_engine/config.py:143-149`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L143-149) | OFFLINE: ENGINE-OWNED LOGS ONLY | F-19 scoped engine launch log threshold PASS; legacy module-level logs remain outside profile filter | P-04 commit 997e5dd5 / proof 09; real browser+Windows pending |
| CDP session API | [`stealth_engine/engine.py:1673-1695`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L1673-1695) | UNSUPPORTED / CONDITIONAL | U-03 backend support unknown | P-05 mock unsupported-backend test PASS, actual CDP support unchanged |
| Additional contexts | [`stealth_engine/engine.py:1719-1731`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L1719-1731) | UNSUPPORTED / CONDITIONAL | U-04 requires browser handle | P-01: evaluate/document |
| Video recording | [`stealth_engine/engine.py:676-687`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L676-687) | UNSUPPORTED / CONDITIONAL | U-02 rejected by design | P-05 rejection test PASS, unsupported unchanged |
| Sync session convenience methods | [`stealth_engine/engine.py:862-875`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L862-875) | UNSUPPORTED / CONDITIONAL | U-01 always throws for sync new_page | P-01: clarify contract |
| Admin/user permission/UI pages | [`stealth_engine/__init__.py:1-19`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/__init__.py#L1-19) | NOT IN THIS REPOSITORY | No tracked GUI/admin source; cannot audit external app | Out of scope until another repo provided |

## Positive probe anchors (previous isolated evidence, not live production)

**[Source: `stealth_engine/config.py:249-269`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/config.py#L249-269)**

```python
 249 |     def save_json(self, path: str | Path) -> None:
 250 |         """Write this config to ``path`` as pretty-printed JSON.
 251 | 
 252 |         Uses ``model_dump(mode="json")`` so the output is plain JSON types.
 253 |         The file is written atomically (``.tmp`` then ``os.replace``).
 254 | 
 255 |         Args:
 256 |             path: Destination file path.
 257 |         """
 258 |         import os
 259 | 
 260 |         p = Path(path)
 261 |         tmp = p.with_suffix(p.suffix + ".tmp")
 262 |         tmp.write_text(
 263 |             json.dumps(
 264 |                 self.model_dump(mode="json"), indent=2, sort_keys=True
 265 |             )
 266 |             + "\n",
 267 |             encoding="utf-8",
 268 |         )
 269 |         os.replace(tmp, p)
```
**[Source: `stealth_engine/session.py:405-433`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/session.py#L405-433)**

```python
 405 |                 c for c in storage_state["cookies"]
 406 |                 if any(
 407 |                     _domain_match(_host_of(str(c.get("domain", ""))), d)
 408 |                     for d in allowed
 409 |                 )
 410 |             ]
 411 |             filtered_origins = [
 412 |                 o for o in storage_state["origins"]
 413 |                 if any(
 414 |                     _domain_match(_host_of(str(o.get("origin", ""))), d)
 415 |                     for d in allowed
 416 |                 )
 417 |             ]
 418 |             storage_state = {
 419 |                 "cookies": filtered_cookies,
 420 |                 "origins": filtered_origins,
 421 |             }
 422 | 
 423 |         self.ensure_dirs()
 424 | 
 425 |         serialised = json.dumps(storage_state, sort_keys=True)
 426 |         tmp_path = self._storage_state_path.with_suffix(".json.tmp")
 427 | 
 428 |         wrote = False
 429 |         try:
 430 |             tmp_path.write_text(serialised, encoding="utf-8")
 431 |             os.replace(str(tmp_path), str(self._storage_state_path))
 432 |             wrote = True
 433 |         except OSError as exc:
```
**[Source: `stealth_engine/behavior.py:35-56`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/behavior.py#L35-56)**

```python
  35 | def _bezier_point(
  36 |     p0: tuple[float, float],
  37 |     p1: tuple[float, float],
  38 |     p2: tuple[float, float],
  39 |     p3: tuple[float, float],
  40 |     t: float,
  41 | ) -> tuple[float, float]:
  42 |     """Cubic bezier interpolation at parameter ``t``."""
  43 |     u = 1.0 - t
  44 |     x = (
  45 |         u * u * u * p0[0]
  46 |         + 3 * u * u * t * p1[0]
  47 |         + 3 * u * t * t * p2[0]
  48 |         + t * t * t * p3[0]
  49 |     )
  50 |     y = (
  51 |         u * u * u * p0[1]
  52 |         + 3 * u * u * t * p1[1]
  53 |         + 3 * u * t * t * p2[1]
  54 |         + t * t * t * p3[1]
  55 |     )
  56 |     return (x, y)
```
**[Source: `stealth_engine/risk.py:24-39`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/risk.py#L24-39)**

```python
  24 | def ban_risk_score(
  25 |     probe: dict[str, Any],
  26 |     geo: "GeoInfo | None" = None,
  27 |     config: "ProfileConfig | None" = None,
  28 | ) -> dict[str, Any]:
  29 |     """Score ban/detection risk from probe + optional geo/config signals.
  30 | 
  31 |     Args:
  32 |         probe: Dict from ``BrowserSession.probe_fingerprint`` (missing
  33 |             keys are treated as absent, not errors).
  34 |         geo: Optional :class:`GeoInfo` for timezone/locale cross-checks.
  35 |         config: Optional :class:`ProfileConfig` for explicit overrides.
  36 | 
  37 |     Returns:
  38 |         ``{"score": int, "level": "low"|"medium"|"high", "signals": [str]}``
  39 |     """
```

## Post-phase incremental feature ledger — fill only after verified implementation

| Phase | Newly actual working feature | Existing feature behavior confirmed unchanged | Live environment & command | Evidence URL / commit | Status |
|---|---|---|---|---|---|
| P-01 | Sync loop lifecycle; awaited first page; emergency proxy/lock cleanup **in fake contexts** | No code changed outside locked engine lifecycle + P-01 tests; 6 adjacent regressions pass | Python 3.13 + fake Camoufox; **not real browser** | [`9638c789`](https://gitlab.com/ivibtools/stealth-engine/-/commit/9638c789c7b06def4b51a54583bd728ee42e746b) | PATCH APPLIED / OFFLINE PASS / LIVE GATE BLOCKED |
| P-02 | PID/token guard ownership, fail-closed reset; versioned first_seen sidecar/legacy backup **offline only** | P-01 code AST unchanged; all other backend modules untouched | Linux Python 3.13, 35/35 tests with test-only imports; Windows/browser untested | [code `cb06b63b`](https://gitlab.com/ivibtools/stealth-engine/-/commit/cb06b63b10130e99c28747a95837ab901ae42dfc), [final `e4c60c11`](https://gitlab.com/ivibtools/stealth-engine/-/commit/e4c60c11c62d4fcef0f8892ae484014f4324659f), [07](07-P02-VERIFICATION-EVIDENCE.md) | PATCH APPLIED / OFFLINE PASS / WINDOWS+LIVE GATES BLOCKED |
| P-03 | Native SOCKS4a/SOCKS5 local GeoIP transport; proxy credential redaction; strict authority; Geo auto; WebRTC public-IP hint guard | P-01/P-02 lifecycle/session code AST unchanged, U-05 unchanged, no UI files | Linux Python 3.13, 59/59 scoped/adjacent PASS; local SOCKS only; real HTTPS, external proxy, Windows, browser UNVERIFIED | [code `b2d1884a`](https://gitlab.com/ivibtools/stealth-engine/-/commit/b2d1884a8e7534d28f492d9f3274eb17c5551b3a), [proof 08](08-P03-VERIFICATION-EVIDENCE.md) | PATCH APPLIED / OFFLINE PASS / LIVE GATES BLOCKED |
| P-04 | F-03/F-04/F-10/F-13/F-19 source patched within documented files | P-01..03 logic and UI unchanged; default JSON/YAML secrets redacted; invalid Android preset removed; scoped launch logging | 61/61 focused Linux offline PASS, 2/6 legacy Feature Y FAIL, real Camoufox/Windows/whole-app logs NOT VERIFIED | [code `997e5dd5`](https://gitlab.com/ivibtools/stealth-engine/-/commit/997e5dd5087d4e366dc573f561e2e9ac3a063520), [proof 09](09-P04-VERIFICATION-EVIDENCE.md) | PATCH APPLIED; LEGACY & LIVE ACCEPTANCE BLOCKED |
| P-05 | F-16 canvas/WebGL stable repeated reads and F-17 hostname-safe tracker rules **offline** | P-01..04 methods unchanged; U-02/U-03/U-06 conditional unchanged; no UI | Linux Python 3.13 + Node 22, 71/71 focused PASS; full 235 PASS/8 FAIL/4 SKIP; real browser NOT VERIFIED | [source `38b44068`](https://gitlab.com/ivibtools/stealth-engine/-/commit/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd), [proof 10](10-P05-VERIFICATION-EVIDENCE.md) | PATCH APPLIED / OFFLINE PASS / FULL SUITE & LIVE ACCEPTANCE BLOCKED |

## Production verification queue (remain unverified until executed)

- [ ] Real `AsyncCamoufox` launch, page navigation, and clean teardown; async/sync contract.
- [ ] Cookies/profile state persist across restart; concurrent same-profile access prevented.
- [ ] Proxy health/rotation, controlled egress geo/DNS/WebRTC leak checks; no use of real user credentials in test.
- [ ] Identity readback coherence (UA/viewport/screen/locale/timezone) with browser-generated fingerprint.
- [ ] Human move/type/scroll; download/upload/HAR; request blocking/routing.
- [ ] Concurrent bulk jobs, cancellation, timeout/retry and resource cleanup under bounded load.
- [ ] Supported/unsupported decisions for all U-01..U-06; no false successful feature labels.
- [ ] Full dependency-installed test suite, compatible Windows platform if release targeted, CI build/package/install and release smoke.

**Status rule:** A single passing pure-Python unit test cannot promote its entire feature to `REAL VERIFIED`; record the exact capability, environment, behavior and limitations.

## P-01 incremental outcome (2026-11-16)

**Newly verified behavior (local fake backend only):** 15/15 targeted tests pass (9 P-01 scenarios plus 6 adjacent regressions). Worker event loop stays active after sync launch and closes at teardown, empty-page context returns a real fake-page object not a coroutine, and failed startup or cancellation attempts release the lock and close proxy manager. Original typed error remains when proxy shutdown itself fails.

**Still not actual production working:** No installed Camoufox/browserforge on this test host; no real browser launch, browser context readback, cross-thread Playwright calls, live proxy session, or full integration tests. Mark these **NOT VERIFIED**, not failed and not passed. U-01 sync convenience methods are deliberately unsupported; U-04 additional context depends on browser handle.

**Unmodified:** Profile ownership/force reset, identity generation, proxy transport, GeoIP, WebRTC, logging, tracker filtering, JS noise, bulk orchestration, config schema, public API names and non-existent GUI.

**Source proof:** [`engine.py:258-298`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/stealth_engine/engine.py#L258-298), [`engine.py:429-445`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/stealth_engine/engine.py#L429-445), [`engine.py:775-804`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/stealth_engine/engine.py#L775-804), and the [`P-01 test classes`](https://gitlab.com/ivibtools/stealth-engine/-/blob/9638c789c7b06def4b51a54583bd728ee42e746b/tests/test_forensic_regressions.py). **Formal P-01 live release acceptance remains open.**


## P-05 actual-working increment (post-commit `38b44068`)

| API/feature | Source-applied result | What is actually verified | Remaining gap |
|---|---|---|---|
| JS canvas/WebGL noise | [fresh per-read PRNG](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L87-103) | Node mock same-pixel repeated `toDataURL`, `getImageData`, WebGL1/2 pass; 2 seeds; original canvas pixels unchanged | Real Camoufox/probe detectability NOT VERIFIED; experimental only |
| `block_trackers` | [destination hostname matching](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L1670-1717) | Async fake route test: real tracker hosts block, benign query/path/redirect URL allow, lookalikes allow, userinfo and malformed authority handled | Real browser request routing and redirect chain NOT VERIFIED |
| Video option (U-02) | unchanged reject | Offline `AutomationError` assertion PASS | Unsupported on Firefox backend; not promoted |
| CDP (U-03) | unchanged conditional error | Simulated backend `NotImplementedError` maps to `AutomationError` | Real Firefox backend capabilities NOT VERIFIED |
| Runner timeout (U-06) | unchanged task-only | AST check `wait_for(task_fn(...))` PASS | End-to-end launch/cleanup timeout not promised; separate approval needed |

**Project status:** 5/5 code patches applied; 19/19 findings code-addressed, **0/5 fully production accepted**. Full-suite 235 PASS / **8 FAIL** / 4 SKIP. P-04 per-profile legacy global log coverage remains partial. No live browser/Windows/proxy/packaging certification; see [10](10-P05-VERIFICATION-EVIDENCE.md).
