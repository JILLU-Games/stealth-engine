# 03 — BUGFIX ROADMAP (scope-locked phases)

Continuation: BF-01..BF-04. Each phase independently shippable,
each with tests. Order = risk reduction.

## BF-01 — Critical correctness (data loss + safety)

**Scope lock:** `engine.py`, `session.py`, tests, docs.

| Bug | Fix |
|---|---|
| B-01 | `save_state` async-correct: add `async def save_state_async()` (`await ctx.storage_state()`); `aclose` uses it; sync `close()` runs it inside `asyncio.run`; sync `save_state()` delegates or raises clear error |
| B-02 | `_pid_alive` Windows-safe: replace `os.kill(pid,0)` with ctypes `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)` on Windows; keep POSIX path |
| B-03 | Remove unawaited `self._ctx.close()` in `close()` — `ctx_handle.__aexit__` owns context teardown |

**Non-goals:** no API changes; `save_state()` keeps working for sync callers.

## BF-02 — Major correctness

**Scope lock:** `session.py`, `engine.py`, `geo.py`, tests, docs.

| Bug | Fix |
|---|---|
| B-04 | Dot-boundary domain match: `host == d or host.endswith("."+d)`; drop unsafe reverse clause; skip empty hosts |
| B-05 | `_resolve_host_ip` best-effort chain: UDP connect → `gethostbyname(hostname)` → warn + `"0.0.0.0"` fallback (no LaunchError) |
| B-06 | `js_noise` toDataURL: render to offscreen clone instead of `putImageData` on live canvas |
| B-17 | `resolve_ip` URL builder: strip trailing `/json`-style suffix from endpoint before appending `/{ip}/json`, or document+normalize endpoint base |

## BF-03 — Minor correctness batch

**Scope lock:** `engine.py`, `identity.py`, `proxy.py`, `geo.py`,
`orchestrator.py`, tests, docs.

| Bug | Fix |
|---|---|
| B-07 | Track `_last_mouse` position in BrowserSession; update on moves |
| B-08 | `pick_healthy` docstring → `health_threshold_ms` |
| B-09 | `resolve_geo` wrap unexpected exceptions in ProxyError |
| B-10 | `verify_stealth` normalize mismatches to `{source, detail}` |
| B-11 | `validate_fingerprint`: infer OS from UA tokens when `os` key absent |
| B-12 | Move `_record_fingerprint()` after successful launch |
| B-13/B-20 | js_noise: add WebGL2 + webgl-canvas toDataURL coverage |
| B-18 | `_derive_timezone` normalise locale case before lookup |
| B-19 | `BulkRunner.run` guard: raise if already running |
| B-21 | `_geo_cache` key → masked server |
| B-22 | Add `BrowserSession.__aexit__` → `aclose()` |
| B-23 | Fix duplicate stage comments |

## BF-04 — Verification & docs sweep

- Re-run full suite; update project/+docs/ for every touched module
- Update MEMORY/CHANGELOG; notes/bugFix/06 status
- Optional: `STEALTH_SMOKE=1` live verify of save_state fix

## Dependency notes

- BF-01 first (data loss)
- BF-02 independent of BF-01
- BF-03 independent; can split further if wanted
- BF-04 always last

## Out of scope (locked)

- No new features; no API breaks; no engine changes
