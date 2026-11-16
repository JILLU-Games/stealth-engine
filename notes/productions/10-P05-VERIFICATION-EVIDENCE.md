# 10 — Phase-05 Source Patch & Verification Evidence

**Repository:** `ivibtools/stealth-engine` (GitLab private).  
**Date:** 2026-11-16 UTC.  
**Frozen original baseline:** `a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`.  
**Phase start HEAD:** `4a1512ff7c95eafba1d951eb73eb194c66d74977`.  
**Phase-05 code commit:** [`38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd`](https://gitlab.com/ivibtools/stealth-engine/-/commit/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd).  
**Status:** **Source patch applied, focused offline pass, FULL PRODUCTION ACCEPTANCE BLOCKED.** This is not a claim of all real-browser features working.

## 1. Findings, exact changed regions and evidence

### F-16 — Experimental JS noise repeated-readback consistency (Medium)

Baseline `_js_noise_init_script()` kept an incrementing PRNG state outside readback, so identical pixels read multiple times consumed different jitter values. P-05 now initializes a new seed-local PRNG within `_perturb(data, step)` on each read. The offscreen clone and WebGL1/WebGL2 readback hooks remain in place. **Identical input pixels are stable for the same seed in controlled tests; this does not imply invisibility of JS monkey-patches.**

**Source: [`stealth_engine/engine.py:85-103`](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L85-103)**

```python
  85 |     s = int(hashlib.sha256(f"jsn-{seed}".encode()).hexdigest()[:8], 16)
  86 |     return f"""
  87 | (() => {{
  88 |   const _seed = {s} | 0;
  89 |   const _perturb = (data, step) => {{
  90 |     // F-16: reset the seeded stream for each readback. Identical pixels
  91 |     // yield identical output even when other canvas/WebGL reads intervene.
  92 |     let state = _seed;
  93 |     const rnd = () => {{
  94 |       state = state + 0x6D2B79F5 | 0;
  95 |       let t = Math.imul(state ^ state >>> 15, 1 | state);
  96 |       t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
  97 |       return ((t ^ t >>> 14) >>> 0) / 4294967296;
  98 |     }};
  99 |     for (let i = 0; i < data.length; i += step * 4) {{
 100 |       const jitter = (rnd() < 0.5 ? -1 : 1) * (rnd() * 3 | 0);
 101 |       data[i] = Math.max(0, Math.min(255, data[i] + jitter));
 102 |     }}
 103 |   }};
```

**Source: [`stealth_engine/engine.py:104-139`](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L104-139)**

```python
 104 |   try {{
 105 |     const _td = HTMLCanvasElement.prototype.toDataURL;
 106 |     HTMLCanvasElement.prototype.toDataURL = function (...a) {{
 107 |       try {{
 108 |         const cx = this.getContext('2d');
 109 |         if (cx && this.width * this.height < 4000000) {{
 110 |           // BF-02/B-06: render to an OFFSCREEN clone — never mutate the
 111 |           // live canvas (putImageData would alter real pixels).
 112 |           const tmp = document.createElement('canvas');
 113 |           tmp.width = this.width; tmp.height = this.height;
 114 |           const tctx = tmp.getContext('2d');
 115 |           tctx.drawImage(this, 0, 0);
 116 |           const d = tctx.getImageData(0, 0, tmp.width, tmp.height);
 117 |           _perturb(d.data, 7);
 118 |           tctx.putImageData(d, 0, 0);
 119 |           return _td.apply(tmp, a);
 120 |         }}
 121 |       }} catch (e) {{}}
 122 |       return _td.apply(this, a);
 123 |     }};
 124 |     const _gid = CanvasRenderingContext2D.prototype.getImageData;
 125 |     CanvasRenderingContext2D.prototype.getImageData = function (...a) {{
 126 |       const d = _gid.apply(this, a);
 127 |       try {{ _perturb(d.data, 7); }} catch (e) {{}}
 128 |       return d;
 129 |     }};
 130 |     const _rp = WebGLRenderingContext.prototype.readPixels;
 131 |     WebGLRenderingContext.prototype.readPixels = function (...a) {{
 132 |       _rp.apply(this, a);
 133 |       try {{
 134 |         const px = a[a.length - 1];
 135 |         if (px && px.length) _perturb(px, 11);
 136 |       }} catch (e) {{}}
 137 |     }};
 138 |     // BF-03/B-13: WebGL2 shares the same readPixels signature.
 139 |     if (typeof WebGL2RenderingContext !== 'undefined') {{
```

**Reproduction test reference:** [P-05 regression source](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/tests/test_forensic_regressions.py#L1462-1534) executes real Node v22 JavaScript against a canvas-shaped test double (not a Firefox engine), checks first/second/third `toDataURL` match, repeated `getImageData` and WebGL1/2 buffer parity, and verifies unmodified live source pixels. Two different seeds run. **Passed.**

### F-17 — Tracker false positives caused by full-URL substring matching (Medium)

Baseline `if any(d in url for d in domains)` also caught benign URLs with tracker names in query/path or lookalike hosts. Current route normalizes configured destination domain labels and matches `urlsplit(request.url).hostname` by exact match or **dot-prefixed subdomain**; invalid authority triggers `ValueError` → continue. Redirect destination is inspected when that request is routed, not guessed from a query string.

**Source: [`stealth_engine/engine.py:1670-1717`](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L1670-1717)**

```python
1670 |     async def block_trackers(
1671 |         self, extra_domains: list[str] | None = None
1672 |     ) -> int:
1673 |         """Abort requests to common tracker/analytics domains (PH-20, G2).
1674 | 
1675 |         Registers a ``**/*`` route that aborts requests whose *destination
1676 |         hostname* equals a known tracker domain or is its subdomain. URL
1677 |         paths, queries and lookalike suffixes are never treated as hosts.
1678 | 
1679 |         Args:
1680 |             extra_domains: Additional domain names to block (including
1681 |                 subdomains); optional leading ``*.`` is accepted.
1682 | 
1683 |         Returns:
1684 |             Number of domains now blocked.
1685 | 
1686 |         Raises:
1687 |             AutomationError: If route registration fails.
1688 |         """
1689 |         from urllib.parse import urlsplit
1690 | 
1691 |         domains = list(_TRACKER_DOMAINS) + list(extra_domains or [])
1692 |         # F-17: normalize domain rules once; use label boundaries, not URL
1693 |         # substring matching (which also matches queries and lookalikes).
1694 |         blocked_hosts = tuple(
1695 |             domain.strip().lower().removeprefix("*.").strip(".")
1696 |             for domain in domains
1697 |             if isinstance(domain, str) and domain.strip(".* ")
1698 |         )
1699 | 
1700 |         async def _handler(route: Any, request: Any) -> None:
1701 |             try:
1702 |                 host = (urlsplit(request.url).hostname or "").lower().rstrip(".")
1703 |             except ValueError:  # Invalid URL authority must not become a tracker match.
1704 |                 host = ""
1705 |             if host and any(host == d or host.endswith("." + d) for d in blocked_hosts):
1706 |                 await route.abort()
1707 |             else:
1708 |                 await route.continue_()
1709 | 
1710 |         try:
1711 |             await self._ctx.route("**/*", _handler)
1712 |         except Exception as exc:
1713 |             raise AutomationError(
1714 |                 "block_trackers failed",
1715 |                 details={"stage": "block_trackers", "reason": str(exc)},
1716 |             ) from exc
1717 |         return len(domains)
```

**Mock regression reference:** [P-05 regression source](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/tests/test_forensic_regressions.py#L1537-1584) verifies tracker host/subdomain abort, benign query/path and fake redirect URL continue, host-lookalike continue, hostname case/trailing dots, userinfo, invalid IPv6 authority, `extra_domains` with leading `*.`; route registration failure still `AutomationError`. **Passed.**

**Compatibility change:** `extra_domains` now means literal destination hostname plus subdomains (`*.example.com` accepted), not an arbitrary substring that can match a URL query/path. The count return value still reflects supplied list length, not unique normalized hosts. This is intentional under F-17.

## 2. Conditional API decisions — NO feature expansion

| ID | Exact current implementation | What was checked | Product-status boundary |
|---|---|---|---|
| U-02 | [`StealthEngine._build_launch_kwargs` rejects video config](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L777-786) | `test_u02_video_recording_still_rejected` passes using an actual `ProfileConfig`, no browser | **UNSUPPORTED** Firefox recording option; unchanged |
| U-03 | [`BrowserSession.cdp_session` wraps backend failure](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/engine.py#L1825-1857) | simulated `NotImplementedError('Firefox')` → `AutomationError` passes | **UNSUPPORTED/CONDITIONAL**, actual CDP backend unverified; unchanged |
| U-06 | [`BulkRunner._attempt_profile` task timeout](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/stealth_engine/orchestrator.py#L386-396) | inspect+AST confirmed sole `asyncio.wait_for` targets `task_fn(session)` | **TASK-ONLY**; launch/cleanup not bounded; unchanged |
| U-05 | P-03 conditional proxy-pool integration | `orchestrator.py` and proxy-manager source SHA unchanged | **CONDITIONAL**, not implemented or enabled |

**Conditional tests:** [P-05 regression source](https://gitlab.com/ivibtools/stealth-engine/-/blob/38b44068cb9fec1c64af1cb6a7aeff4aefed5bbd/tests/test_forensic_regressions.py#L1587-1619). No source edits to video/CDP/timeout methods.

## 3. Exact focused verification — green but not real browser

**Command executed in this isolated Linux runtime** (temporary import-only Camoufox/browserforge stubs, never committed):

```bash
cd /mnt/data/stealth_audit_workspace
PYTHONPATH=/mnt/data/stealth_audit_workspace python /mnt/data/stealth_phase01_test_shim/run_p05_tests.py
```

**Result:** `Ran 71 tests ... OK`; exit 0. **10 newly authored P-05 tests** + 61 existing scoped/adjacent tests from P-01/P-02/P-03/P-04. Source compiles: `python -m compileall -q stealth_engine tests/test_forensic_regressions.py` exit 0. Node mock runs actual generated JavaScript. Python version 3.13, Node v22, Linux. **No real Camoufox startup, Firefox tab, proxy egress, Windows host, UI, web API request, profile credentials or binary packaging tested.**

Initial focused run had one test-only naming error (`BulkRunner._run_one` did not exist; actual method `_attempt_profile`); corrected inside the appended P-05 test before final 71/71 pass. App source unaffected by this correction.

## 4. Full-source-suite run — RELEASE GATE NOT GREEN

**Command** (imports faked only to make tests collect; no actual Camoufox/browserforge runtime):

```bash
cd /mnt/data/stealth_audit_workspace
PYTHONPATH=/mnt/data/stealth_audit_workspace timeout 40 python /mnt/data/stealth_phase01_test_shim/run_p05_full.py
```

**Final result:** `8 failed, 235 passed, 4 skipped, 32 subtests passed`, **exit 1**. Failures are neither silently skipped nor counted as fixed:

| Failure | Test | Actual observed reason | Classification / responsibility |
|---|---|---|---|
| 1 | `tests/test_feature_p_y.py::FeatureY_Tests::test_json_round_trip` | `load_json(save_json(...))` removes inline proxy secret under P-04 redacted default; test compares unredacted original | **P-04 legacy contract conflict; open; not P-05 scope** |
| 2 | `tests/test_feature_p_y.py::FeatureY_Tests::test_yaml_round_trip` | Same plaintext-secret expectation for YAML | **P-04 legacy contract conflict; open; not P-05 scope** |
| 3 | `tests/test_forensic_regressions.py::PH05_VerificationTests::test_check_25_seed_persistence_fingerprint_consistency` | import-only `FingerprintGenerator` stub raises `RuntimeError('stub: browserforge not installed')`, wrapped as `IdentityError` | **Environment limitation; actual browserforge dependency missing** |
| 4 | `tests/test_geo.py::AutoSentinelEngineTests::test_auto_locale_uses_proxy_geo_even_when_geoip_false` | Same missing browserforge backend stub raises `IdentityError` | **Environment limitation; actual browserforge dependency missing** |
| 5 | `tests/test_hardening.py::FingerprintDepthTests::test_screen_bounds_builds_screen_obj` | `ModuleNotFoundError: camoufox.fingerprints` on Screen import | **Environment limitation; actual Camoufox dependency missing** |
| 6 | `tests/test_meta.py::DriftDetectionTests::test_first_record_no_drift` | Expected `fingerprint_history.json` path absent; `_record_fingerprint` logs history write failed | **Existing historical test/storage contract discrepancy; root cause not resolved under P-05** |
| 7 | `tests/test_meta.py::DriftDetectionTests::test_history_capped_at_50` | Test sees length 60 instead of 50; `_record_fingerprint` history write failed | **Existing historical test/storage contract discrepancy; root cause not resolved under P-05** |
| 8 | `tests/test_meta.py::DriftDetectionTests::test_tampered_history_reports_drift` | `FileNotFoundError` reading expected history; `_record_fingerprint` logs history write failed | **Existing historical test/storage contract discrepancy; root cause not resolved under P-05** |

These categories are **observed failures**, not evidence that every one would reproduce with installed dependencies or on the production OS. The three `test_meta.py` failures are **not automatically dismissed as stale tests**; require separate approved forensic review of metadata path, 50-entry cap and test expectation vs implementation.

## 5. Precise Scope Lock & hash audit

| File | Pre-P05 Git blob | Post-P05 Git blob | Allowed change |
|---|---|---|---|
| `stealth_engine/engine.py` | `d7181136ceeae87630004c423fd94635f5325316` | `765ed769cee934d270ae00638d6d4fe780acca12` | `_js_noise_init_script`, `BrowserSession.block_trackers` only |
| `tests/test_forensic_regressions.py` | `16c1b015c9063898da5d2f7bf8149a284ede6449` | `df6d8fcfe4a0e45ff828dbc01889dc8fb6d9fa4f` | appended 4 P-05 test classes; 10 cases; original test file bytes preserved |

**AST baseline/current check:** every other `engine.py` top-level/class method AST matches exactly; only the above two methods differ. `orchestrator.py`, `session.py`, `proxy.py`, `geo.py`, `identity.py`, `config.py`, logging, other existing test files, UI and release pipeline source unchanged. GitLab checked post-commit blob IDs match local tested files. Original engine/test CRLF preserved. P-01–P-04 implementations not reverted/refactored.

## 6. Next status — release gate, not an invented P-06

- **5/5 planned implementation code phases patched**, 19/19 originally classified finding targets have code changes; **0/5 phases fully production accepted**.
- Real Camoufox/Firefox browser smoke, Windows locking/permissions and packaging, external SOCKS/HTTPS egress/WebRTC/fingerprint parity, profile logging coverage, bulk cancellation/timeout remain **NOT VERIFIED**.
- Full suite **8 unresolved failures** prevent a credible production-ready statement; P-04 two legacy tests and F-19 partial profile log coverage remain open, and the three fingerprint-history failures require explicit resolution.
- No fixes to out-of-scope legacy tests or other engine components made. Any further code work requires separate approval/change-control, not automatic phase expansion.
