# 01 — FORENSIC FINDINGS (2026-11-16)

Baseline: `25a2993` — all PH-13..21 done, 165 tests.
Method: module-by-module source audit + playwright API verification.

Severity: CRITICAL = data loss/security · MAJOR = broken feature ·
MINOR = cosmetic/edge-case.

---

## CRITICAL

### B-01 — `save_state()` never saves: async `storage_state()` not awaited

**File:** `stealth_engine/engine.py` ~L815, ~L905 (called from `close()`/`aclose()`)

```python
def save_state(self) -> None:
    try:
        state: dict = self._ctx.storage_state()   # ← returns COROUTINE
    except Exception as exc:
        ...
    self._session.export_state(state)             # ← SessionError: not a dict
```

Verified: `inspect.iscoroutinefunction(BrowserContext.storage_state) == True`.
The coroutine is passed to `export_state` → `SessionError("must be a dict")`
→ swallowed by best-effort `except` in `close()`/`aclose()` →
**warning logged, cookies/storage NEVER persisted. Silent data loss on
every session close.**

### B-02 — `_pid_alive` kills live processes on Windows

**File:** `stealth_engine/session.py` L24-41

```python
def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
```

On Windows, `os.kill(pid, sig)` for any non-CTRL signal calls
`TerminateProcess(handle, sig)` — signal `0` **terminates the process
with exit code 0**. When a second launch hits an existing lock file,
the staleness check calls `_pid_alive(live_pid)` → **kills the process
holding the lock**, then reports it alive. Dev machine IS Windows.

### B-03 — `close()` calls async `ctx.close()` without await

**File:** `stealth_engine/engine.py` ~L864

```python
try:
    self._ctx.close()        # ← coroutine discarded, never awaited
except Exception as exc:
    ...
```

Verified: `BrowserContext.close` is a coroutine. The call creates a
coroutine that is garbage-collected (RuntimeWarning: never awaited).
Context cleanup only works because `ctx_handle.__aexit__` runs later —
fragile, warning-spamming, and the comment "sync path" is wrong.

---

## MAJOR

### B-04 — `export_state(domains=)` cross-domain leak (no dot boundary)

**File:** `stealth_engine/session.py` L373-388

```python
filtered_cookies = [
    c for c in storage_state["cookies"]
    if any(
        _host_of(str(c.get("domain", ""))).endswith(d)
        or d.endswith(_host_of(str(c.get("domain", ""))))
        for d in allowed
    )
]
```

`"notexample.com".endswith("example.com")` → **True**. A cookie for
`notexample.com` is exported when filtering `example.com` — the
selective-export isolation guarantee is broken. Also `_host_of("")`
returns `""` and `d.endswith("")` is always True → domainless entries
always pass.

### B-05 — `_resolve_host_ip` hard-fails launch without UDP/8.8.8.8

**File:** `stealth_engine/engine.py` L465-495

```python
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(5)
    s.connect(("8.8.8.8", 53))
    host_ip = s.getsockname()[0]
```

Offline / UDP-blocked / DNS-restricted networks → `OSError` →
`LaunchError` — launch dies in Mode A (no proxy) even though WebRTC
spoofing could degrade gracefully. Hard dependency on Google DNS.

### B-06 — `js_noise` `toDataURL` patch mutates the real canvas

**File:** `stealth_engine/engine.py` `_js_noise_init_script` (~L100-110)

```js
HTMLCanvasElement.prototype.toDataURL = function (...a) {
  const cx = this.getContext('2d');
  const d = cx.getImageData(0, 0, this.width, this.height);
  _perturb(d.data, 7);
  cx.putImageData(d, 0, 0);   // ← writes noise INTO the live canvas
  return _td.apply(this, a);
};
```

`toDataURL` must be read-only — this permanently alters canvas pixels
(visible changes + double-noise on subsequent `getImageData` calls).
Should render to an offscreen copy instead.

---

## MINOR

### B-07 — `page.mouse.position` doesn't exist → bezier always starts (0,0)

**File:** `stealth_engine/engine.py` ~L992, ~L1100

```python
pos = getattr(getattr(page, "mouse", None), "position", None)
current_x = float(pos["x"]) if pos else 0.0
```

Verified: Playwright `Mouse` has no `position` attribute → always
falls back to `(0,0)` → every mouse path starts at top-left corner
regardless of actual cursor position. Endpoints still correct.

### B-08 — Stale docstring: "under 5000 ms"

**File:** `stealth_engine/proxy.py` L429 — `pick_healthy` docstring
still says 5000 ms; threshold is `health_threshold_ms` since PH-11.

### B-09 — `resolve_geo` leaks non-ProxyError exceptions

**File:** `stealth_engine/proxy.py` L326-388 — retry loop catches
`ProxyError`/`TimeoutError`/`ClientError` only; other exceptions
(e.g. `OSError`, `ValueError` from aiohttp internals) escape raw,
inconsistent with the ProxyError contract callers expect.

### B-10 — `verify_stealth` mixes mismatch types

**File:** `stealth_engine/engine.py` ~L1460 — `mismatches` list gets
geo field-names (str) AND fp issue-strings (str) but geo
`mismatches` are field names not descriptions — `summary`/consumers
can't distinguish severity/source cleanly.

### B-11 — `validate_fingerprint` OS-coherence is dead code

**File:** `stealth_engine/identity.py` ~L690 — real
`IdentityGenerator.generate()` output has **no `"os"` key**
(verified: keys are color_scheme/device_memory/.../viewport).
`os_name` is always `""` → platform↔OS checks never run on real fps.

### B-12 — Failed launches pollute fingerprint drift history

**File:** `stealth_engine/engine.py` ~L292 — `_record_fingerprint()`
runs right after `identity.generate()`, BEFORE camoufox launch.
A launch that fails afterward still appends a history entry →
`session_age_days`/drift detection counts failed attempts as launches.

### B-13 — `js_noise` misses WebGL2

`_js_noise_init_script` patches `WebGLRenderingContext.readPixels`
only; `WebGL2RenderingContext` unpatched → sites using WebGL2 get
un-noised readbacks (inconsistent noise coverage).

### B-14 — `new_context` may be dead on persistent contexts (unverified)

`BrowserSession.new_context` relies on `self._ctx.browser`; playwright
docs indicate persistent contexts may return `None` → always raises
AutomationError in real usage. Needs live verification.

### B-15 — `block_trackers` catch-all route latency

`**/*` route intercepts EVERY request — adds per-request overhead on
heavy pages. Acceptable but undocumented perf cost.

### B-16 — `load_proxies` format gaps (documented limitations)

No IPv6 literals; passwords containing `:` unsupported (4-field split).
Edge cases raise ProxyError correctly — limitation, not defect.

---

## Verified NON-bugs (checked, clean)

- `"auto"` locale/timezone sentinel — never persisted, resolved at launch
- `socks5h://` normalization + `socks_remote_dns` pref — correct
- Orchestrator `task_timeout_s` + error class-name fallback — correct
- `export_state` atomic write + validation — correct (filter aside)
- Lock acquire/release retry logic — correct logic (B-02 is platform bug)
- `warmup` template override + unknown-template error — correct
- `session_age_days` file resolution — correct
- `StickyGeoStore`/`GeoDriftMonitor` persistence — correct
- `_derive_base_dir` profile path resolution — correct
- `IdentityGenerator.launch_salt` rng derivation — correct

---

## DEEP-SCAN ADDITIONS (second pass, 2026-11-16)

### B-17 — `GeoResolver.resolve_ip` builds wrong URL path (MAJOR)

**File:** `stealth_engine/geo.py` L276

```python
urls = [f"{e}/{ip}/json" for e in self._endpoints]
```

Default endpoint is `"https://ipinfo.io/json"` → produces
`"https://ipinfo.io/json/8.8.8.8/json"` → **404**. For ip-api
(`"http://ip-api.com/json"`) the real path is `/json/{ip}` — the
`{e}/{ip}/json` template is wrong for BOTH providers. `resolve_ip`
only works if the user passes a bare host endpoint — undocumented
contract mismatch with `resolve()` which uses endpoints as full URLs.

### B-18 — `_derive_timezone` fallback broken for lowercase locales (MINOR)

**File:** `stealth_engine/identity.py` L328-332 — for `"en-us"` it
tries `"en-EN"` (not in map) → UTC, instead of normalising case.
Only ~20 locales mapped — others always UTC.

### B-19 — `BulkRunner.run()` concurrent calls bypass semaphore (MINOR)

`run()` recreates `self._semaphore` each call — two overlapping
`run()` invocations get independent semaphores → concurrency limit
doubled. Edge case; document or guard.

### B-20 — `js_noise` misses WebGL-canvas `toDataURL` + WebGL2 (MINOR, extends B-13)

`toDataURL` patch only handles `getContext('2d')` — a canvas created
with `webgl`/`webgl2` context returns null → un-noised readback.
Combined with B-13, WebGL2 path is fully unpatched.

### B-21 — `_geo_cache` key embeds credentials (MINOR)

`ProxyManager._geo_cache` keyed by `proxy.server` which may contain
`user:pass@` — credentials sit in memory dict (never logged, but
unnecessary exposure; use masked server as key).

### B-22 — `close()` inside `__exit__` in async context raises (MINOR, by design?)

`__exit__` → `self.close()` → raises `AutomationError` if a loop is
running — `with session:` inside async code always fails. Document
or provide `__aexit__` that calls `aclose()`.

### B-23 — Duplicate stage labels "g)" in `alaunch` (COSMETIC)

Two consecutive steps both labelled `g)` — comment-only, no behavior.
