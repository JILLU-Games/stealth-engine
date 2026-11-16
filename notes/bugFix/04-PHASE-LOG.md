# 04 — PHASE LOG (bugFix work)

## Status dashboard

| Phase | Scope | Status | Date |
|---|---|---|---|
| BF-01 | Critical correctness (B-01,02,03) | ✅ Complete | 2026-11-16 |
| BF-02 | Major correctness (B-04,05,06,17) | ✅ Complete | 2026-11-16 |
| BF-03 | Minor batch (B-07..B-23) | ✅ Complete | 2026-11-16 |
| BF-04 | Verification & docs | ✅ Complete | 2026-11-16 |

**Completed: 4 (BF-01..04) · Pending: 0 — BUGFIX ROADMAP COMPLETE**

## Entries

(append per completed phase)

### BF-01 — Critical correctness ✅ (2026-11-16)
- **Delivered:**
  - B-01 `save_state_async()` added (awaited storage_state); `aclose`
    and `close()` (inside shared asyncio.run) now persist state for
    real; sync `save_state()` raises clear AutomationError.
  - B-02 `_pid_alive` Windows-safe via ctypes OpenProcess — verified
    live: self=True, dead=False, caller process NOT killed.
  - B-03 unawaited `ctx.close()` removed from `close()` — teardown
    owned by `ctx_handle.__aexit__`.
- **Tests:** 173 total (169 pass + 4 gated skips); +8 test_bugfix.py.
- **Scope audit:** engine.py, session.py, test_bugfix.py, docs —
  in-scope.
- **Out-of-scope findings:** none.

### BF-02 — Major correctness ✅ (2026-11-16)
- **Delivered:**
  - B-04 `_domain_match` dot-boundary suffix (bidirectional for
    parent-cookie semantics); empty hosts excluded — notexample.com
    no longer leaks into example.com exports.
  - B-05 `_resolve_host_ip` fallback chain: UDP probe → hostname
    resolution → "0.0.0.0"+warning; LaunchError removed.
  - B-06 js_noise toDataURL renders to offscreen clone — live canvas
    pixels never mutated.
  - B-17 `resolve_ip` strips trailing /json from endpoint base and
    tries BOTH provider path shapes ({base}/{ip}/json then
    {base}/json/{ip}) via existing fallback chain.
- **Tests:** 181 total (177 pass + 4 gated skips); +8 new tests.
- **Scope audit:** session.py, engine.py, geo.py, test_bugfix.py,
  docs — in-scope.
- **Out-of-scope findings:** none.

### BF-03 — Minor batch ✅ (2026-11-16)
- **Delivered (12 items):**
  - B-07 `_last_mouse` tracking (class-level default for __new__
    sessions) — bezier start no longer always (0,0)
  - B-08 pick_healthy docstring → health_threshold_ms
  - B-09 resolve_geo wraps unexpected exceptions in ProxyError
  - B-10 verify_stealth mismatches → {"source","detail"} dicts AND
    now actually returned (was computed but dropped!)
  - B-11 validate_fingerprint infers OS from UA when "os" absent —
    coherence check no longer dead code
  - B-12 _record_fingerprint moved post-launch — failed launches
    don't pollute drift history
  - B-13 WebGL2RenderingContext.readPixels patch added
  - B-18 _derive_timezone case-normalised + bare-lang fallbacks
  - B-19 BulkRunner.run() re-entry guard (_run_active flag)
  - B-21 _geo_cache keyed by masked server (no creds in memory)
  - B-22 __aenter__/__aexit__ → aclose() for async with
  - B-23 stage comments relabelled i/j/k
- **Tests:** 188 total (184 pass + 4 gated skips); +7 new tests.
- **Scope audit:** engine.py, session.py(already), proxy.py,
  identity.py, orchestrator.py, geo.py, test_bugfix.py, docs —
  in-scope.
- **Out-of-scope findings:** none.

### BF-04 — Verification & docs sweep ✅ (2026-11-16)
- **Full suite:** 188 tests — 184 pass + 4 gated skips. Green.
- **Scope audit (25a2993..HEAD):** only declared files touched —
  engine.py, session.py, proxy.py, identity.py, orchestrator.py,
  geo.py, test_bugfix.py + project//docs/ markdown. behavior.py,
  config.py, risk.py untouched. No out-of-scope changes.
- **Stale-doc sweep:** fixed 4 spots — engine.md save_state row,
  proxy.md "5000 ms", session.md os.kill wording,
  G/X feature docs save_state→save_state_async.
- **Roadmap status:** ALL 23 findings fixed across BF-01..03.

### BF-05 — Docs audit + markdown rewrite ✅ (2026-11-16, user-requested)
- **New bug found & fixed (B-24):** `BrowserSession.new_page()` called
  unawaited `ctx.new_page()` coroutine — same class as B-01. Added
  `new_page_async()`; sync `new_page()` raises clear AutomationError.
  Fixed `examples/stealth_example.py` + `tests/test_smoke.py`.
- **README rewritten:** correct quickstart (no `async with` on
  engine), complete module/test tree, feature summary, honest
  limitations section, env-gated test docs.
- **Stale info fixed:** FEATURES.md (A/N rows, Implemented status,
  PH-19..21+BF notes), SECURITY.md (js_noise exception, drift
  detection implemented, BF sweep), ARCHITECTURE.md (behavior.py +
  risk.py added, StealthEngine role corrected), ROADMAP.md Phase 5,
  feature A/N files.
- **De-spam:** removed all 🔒 LOCKED banners, "ghost" naming →
  `stealth_example.py`, zero marketing words remain in public docs.
