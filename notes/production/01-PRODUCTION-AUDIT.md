# 01 — PRODUCTION FORENSIC AUDIT (2026-11-16)

Method: full source audit + REAL camoufox launch verification
(binary v156.0.1-beta.36 installed). Every finding has code proof.

---

## CRITICAL

### B-27 — Engine cannot launch a real browser (invalid camoufox kwargs) — ✅ FIXED (PF-01)

**File:** `stealth_engine/engine.py` `_build_launch_kwargs` (~L613-623, ~L633-636)

```python
kwargs: dict[str, Any] = {
    "os": cfg.os,
    "headless": cfg.headless,
    "persistent_context": True,
    "user_data_dir": self._session.user_data_dir,
    "locale": fp.get("locale", "en-US"),
    "canvas:seed": seeds["canvas"],        # ← INVALID top-level kwarg
    "audio:seed": seeds["audio"],          # ← INVALID top-level kwarg
    "fonts:spacing_seed": seeds["fonts"],  # ← INVALID top-level kwarg
}
...
kwargs["webrtc:ipv4"] = self._resolve_host_ip()   # ← INVALID top-level kwarg
```

**Proof — real launch attempt:**

```
TypeError: BrowserType.launch_persistent_context() got an unexpected
keyword argument 'canvas:seed'
→ wrapped as LaunchError stage='camoufox.launch'
```

After removing `canvas:seed`, next failure:
`unexpected keyword argument 'webrtc:ipv4'`.

**Camoufox source verification** (`.venv/.../camoufox/`):
- `launch_options()` signature has NO `canvas:seed`/`audio:seed`/
  `fonts:spacing_seed`/`webrtc:ipv4` params — unknown kwargs fall
  through `**launch_options` into `launch_persistent_context` → TypeError.
- `audio:seed` IS a real camoufox **config dict** key
  (`fingerprints.py:1633` `config.setdefault('audio:seed', ...)`).
- `canvas:seed` and `fonts:spacing_seed` are **not camoufox keys at
  all** — canvas noise was documented as a camoufox no-op (PH-14).
- WebRTC IP belongs in config as `webrtcIP`
  (`fingerprints.py:1748`) or via the `webrtc_ip` param of the
  non-persistent `AsyncNewContext` API — NOT `webrtc:ipv4`.

**Impact:** EVERY `engine.alaunch()`/`launch()` fails on a real
browser. The package cannot start a session in production.

**Why tests missed it:** `tests/test_smoke.py` catches launch failure
and `skipTest("camoufox binary unavailable")` — a TypeError is
indistinguishable from a missing binary, so the suite stayed green.

### B-25 — Sync `human_*` hooks are dead code (unawaited coroutines)

**File:** `stealth_engine/engine.py` `human_move` (~L1086),
`human_type` (~L1119), `human_scroll` (~L1154), `human_dwell` (~L1200)

```python
for px, py in path[1:]:
    page.mouse.move(px, py)      # ← coroutine, never awaited
    time.sleep(sleep_per_step)
page.mouse.move(x, y)            # ← same
```

**Proof:** `inspect.iscoroutinefunction(Mouse.move) == True`,
`Page.click == True`, `Keyboard.type == True`, `Mouse.wheel == True`.
The ctx is ALWAYS async (AsyncCamoufox) — so every sync hook creates
coroutines that are garbage-collected. The hooks only sleep; no mouse
movement, no typing, no scroll ever reaches the browser. Only the
`ahuman_*`/`adwell` variants actually work.

**Impact:** 4 public API methods documented as working do nothing.

---

## MAJOR

### B-28 — Smoke test masks real launch bugs (test design flaw) — ✅ FIXED (PF-01)

**File:** `tests/test_smoke.py`

```python
except Exception as exc:
    self.skipTest(f"camoufox binary unavailable: {exc}")
```

Any launch exception — including TypeError from bad kwargs — is
reported as "binary unavailable" and skipped. This hid B-27 across
multiple phases. The gate should only skip on ImportError/missing
binary, and FAIL on launch TypeError.

### B-29 — `cdp_session()` cannot work on camoufox (Firefox/Juggler)

**Verified live:** `await s.cdp_session(page)` →
`AutomationError: cdp_session failed (CDP may be unsupported on
Firefox/Juggler)`. Camoufox is Firefox — CDP is a Chrome protocol.
The method exists and fails gracefully, but the feature is effectively
unavailable on the only supported backend. Should be documented as
such (or gated), not presented as a working passthrough.

### B-30 — WebRTC IP spoof unverified / possibly ignored

Real run logged: `Skipping unknown patch webrtcIP : 169.40.116.14`
(camoufox stderr). The `webrtcIP` config key may not be applied by
this camoufox version — Mode A WebRTC spoofing needs verification
against a real WebRTC probe. `geoip=True` path (Mode B) is the
documented camoufox mechanism and is unaffected.

---

## MINOR

### B-26 — `adwell` still uses dead `page.mouse.position` getter

**File:** `engine.py` ~L1311 — `pos = getattr(page.mouse, "position",
None)` → always None → jiggle center hardcoded (200,200) instead of
`self._last_mouse` (B-07 fix missed this call site).

### B-31 — Version/release drift

`pyproject.toml` still `0.2.0` while CHANGELOG documents PH-13..21 +
BF-01..04 + docs overhaul — no release bump yet.

### B-32 — `LeakWarning` noise on every launch

camoufox warns "use the `geoip` parameter instead of setting your
geolocation manually" when `webrtcIP`/geolocation is set without
`geoip=True` (Mode A path). Cosmetic but noisy in production logs.

---

## Verified NON-issues (checked, clean)

- `save_state_async`/`aclose`/`close` — state persists (verified live)
- `new_page_async`, `probe_fingerprint`, `verify_stealth` — real data
- `new_context` — WORKS on real camoufox (B-14 resolved positively)
- `_pid_alive`, domain filter, resolve_ip, host-IP fallback — fixed
- Orchestrator, config validation, yaml/json roundtrip — unit-verified
- `expect_download`/`attach_file`/`fetch_headers`/`block_trackers`/
  `add_route`/`add_listener`/`warmup`/`session_age_days` — code correct,
  await usage verified (not exercised on live site)

---

## PF-01 resolution (2026-11-16)

- All patch keys moved into `config` dict: `canvas:seed`, `audio:seed`,
  `fonts:spacing_seed` (valid camoufox uint keys; browser reports
  canvas/fonts-spacing "removed in 156.0.1-beta.32" → graceful skip),
  `webrtc:ipv4` (valid str key — replaces bogus `webrtcIP` attempt),
  `navigator.hardwareConcurrency`, `timezone`.
- `test_smoke.py` skips only on missing binary markers; launch
  TypeErrors now FAIL.
- Verified: `STEALTH_SMOKE=1 STEALTH_CANARY=1` → 188 tests, 0 skips,
  real camoufox launch + verify_stealth green.
- Side-fix: canary tests imported `IdentityGenerator` from package
  root (not exported) → corrected to `stealth_engine.identity`.
