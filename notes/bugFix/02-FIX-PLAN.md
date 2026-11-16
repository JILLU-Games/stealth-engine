# 02 — FIX PLAN (scope-locked, pending approval)

Proposed grouping — each group independently shippable.

## Group A — Critical fixes (must, small diffs)

| Bug | Fix | Files |
|---|---|---|
| B-01 save_state | Make `save_state`/`aclose` path async-correct: add `async def save_state_async()` using `await ctx.storage_state()`; `aclose` uses it; sync `close()` runs it inside the existing `asyncio.run` block; keep sync `save_state()` raising clear error or delegate | engine.py |
| B-02 _pid_alive | Windows-safe liveness: use `psutil`-free approach — `OpenProcess` via ctypes or `tasklist` filter, or simplest: on Windows treat lock as stale only by age (>24h) OR use `os.waitpid`-free check via `ctypes.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)` | session.py |
| B-03 ctx.close() | Remove unawaited `self._ctx.close()` in `close()` — rely on `ctx_handle.__aexit__` (persistent context close) inside the asyncio.run block | engine.py |

## Group B — Major fixes

| Bug | Fix | Files |
|---|---|---|
| B-04 domain filter | Dot-boundary suffix match: `host == d or host.endswith("." + d)`; drop the reverse `d.endswith(host)` clause or keep only for explicit parent-domain semantics; skip empty hosts | session.py |
| B-05 host IP | Best-effort: try UDP connect, on failure try `socket.gethostbyname(socket.gethostname())` then fall back to `"0.0.0.0"`+warning instead of LaunchError | engine.py |
| B-06 js_noise canvas | Don't `putImageData` on live canvas — draw toDataURL on an offscreen clone, or perturb a copy of ImageData and encode manually | engine.py |

## Group C — Minor fixes

| Bug | Fix |
|---|---|
| B-07 mouse.position | Track last known position in session (`self._last_mouse`), update on each move; fallback (0,0) only first call |
| B-08 docstring | Update to `health_threshold_ms` |
| B-09 resolve_geo | Catch broad `Exception` → wrap in ProxyError (keep CancelledError/BaseException passthrough) |
| B-10 verify_stealth | Normalize mismatches to `{"source","detail"}` dicts |
| B-11 dead OS check | Read `fp.get("os") or infer from UA tokens` — or drop dead branch + document |
| B-12 drift pollution | Move `_record_fingerprint()` after successful launch wrap |
| B-13 WebGL2 | Add `WebGL2RenderingContext.prototype.readPixels` patch |
| B-14 new_context | Live-verify; if `ctx.browser` None → document limitation (already graceful) |
| B-15 perf | Document in `block_trackers` docstring |
| B-16 formats | Document in `load_proxies` docstring |

## Non-goals

- No API signature breaks (all additive/fixes internal)
- No behavior change for correct paths
- Tests added per fix; full suite must stay green

## Approval needed

- Group A only? A+B? All?
- B-02 approach preference: ctypes OpenProcess vs age-only staleness on Windows
