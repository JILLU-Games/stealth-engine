# 06 — IMPLEMENTED STATUS (bugFix)

## Working now (baseline, pre-fix)

- All 29 public API names import cleanly
- 165 tests (161 pass + 4 gated skips)
- Known-broken paths documented in 01-FINDINGS.md

## Bug status tracker

| Bug | Severity | Status |
|---|---|---|
| B-01 save_state async | CRITICAL | ✅ Fixed (BF-01) |
| B-02 _pid_alive Windows | CRITICAL | ✅ Fixed (BF-01) |
| B-03 ctx.close unawaited | CRITICAL | ✅ Fixed (BF-01) |
| B-04 domain filter leak | MAJOR | ✅ Fixed (BF-02) |
| B-05 host IP hard-fail | MAJOR | ✅ Fixed (BF-02) |
| B-06 js_noise canvas mutate | MAJOR | ✅ Fixed (BF-02) |
| B-17 resolve_ip URL | MAJOR | ✅ Fixed (BF-02) |
| B-07..B-23 minors | MINOR | ✅ Fixed (BF-03) |

## Post-fix verification checklist

- save_state actually writes storage_state.json on aclose
- _pid_alive does not kill test process on Windows
- selective export excludes notexample.com
- launch survives no-UDP environment (fallback path)
- js_noise toDataURL leaves canvas pixels unchanged
- resolve_ip hits correct provider path
- Full suite green + docs synced — DONE (188 tests, BF-04)

## BF-04 done ✅ (2026-11-16)
- All 23 findings FIXED. Bugfix roadmap complete.
- Residual known-limitations (documented, not bugs):
  js_noise webgl-canvas toDataURL un-noised (preserveDrawingBuffer
  unreliable); block_trackers catch-all route adds per-request latency;
  load_proxies no IPv6/colon-passwords; new_context needs live verify.

## BF-01 done ✅ (2026-11-16)
- B-01/B-02/B-03 fixed + regression tests; storage_state now persists

## BF-03 done ✅ (2026-11-16)
- All 12 minor items fixed; verify_stealth now returns mismatches list
