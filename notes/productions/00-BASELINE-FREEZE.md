# 00 — Immutable Baseline Freeze & Source Fingerprint

> **Status: DOCUMENTED ONLY / NO IMPLEMENTATION**. This is a proposed incremental plan, not a claim of completed fixes.
> **Immutable source baseline:** [`a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`](https://gitlab.com/ivibtools/stealth-engine/-/commit/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5); prior source audit revision [`6255383cac9f29d64bf9ee5957c77ee26ccd7993`](https://gitlab.com/ivibtools/stealth-engine/-/commit/6255383cac9f29d64bf9ee5957c77ee26ccd7993). The 31 audited executable/config blob hashes match across these revisions.


## Baseline decision

- **Repository:** `ivibtools/stealth-engine` (GitLab private)
- **Current HEAD before documentation:** `a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5` on `main`; repository snapshot **157 tracked files**.
- **Earlier finding/source basis:** `6255383cac9f29d64bf9ee5957c77ee26ccd7993`; earlier audit's 19 findings are tied to runtime code that is byte-for-byte unchanged in latest baseline.
- **Freeze type:** immutable SHA pin + content manifest **only**; **no Git tag, branch restriction, zip rewrite or source change is implied**. Future docs commits may advance `main` while this SHA is fixed.
- **Track state:** `0/5` implementation phases completed, 19 findings pending, 6 unsupported/conditional cases pending review.
- **Evidence status:** 31 executable/config Git blobs locally SHA-1 checked against GitLab tree at earlier audit and current runtime code; *the docs revisions have changed, not runtime code*.

## Source proof that this is a Python library, not a user/admin UI

**[Source: `stealth_engine/__init__.py:1-19`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/__init__.py#L1-19)**

```python
   1 | """stealth_engine — a reusable stealth browser runtime for browser automation.
   2 | 
   3 | Provides engine-level fingerprint spoofing, proxy rotation, persistent sessions,
   4 | and bounded-concurrency bulk orchestration as a single drop-in package.
   5 | """
   6 | 
   7 | from __future__ import annotations
   8 | 
   9 | # ---------------------------------------------------------------------------
  10 | # Version — must match pyproject.toml exactly.
  11 | # ---------------------------------------------------------------------------
  12 | __version__: str = "0.3.0"
  13 | 
  14 | # ---------------------------------------------------------------------------
  15 | # Eager imports: lightweight modules with no heavy transitive dependencies.
  16 | # ---------------------------------------------------------------------------
  17 | from .config import ProfileConfig, ProxyConfig, preset_names
  18 | from .exceptions import (
  19 |     AutomationError,
```

**[Source: `stealth_engine/engine.py:258-271`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L258-271)**

```python
 258 |     async def alaunch(self) -> "BrowserSession":
 259 |         """Launch a stealth browser session asynchronously.
 260 | 
 261 |         Executes the mandatory launch sequence in order:
 262 | 
 263 |         a. ``session.ensure_dirs()``
 264 |         b. ``session.acquire_lock()``
 265 |         c. ``fp = identity.generate()``
 266 |         d. proxy resolution (if a proxy is configured)
 267 |         e. GeoIP overrides applied to fingerprint
 268 |         f. camoufox launch
 269 |         g. storage state import (if previous state exists)
 270 |         h. return :class:`BrowserSession`
 271 | 
```

No HTML/CSS/JS GUI or admin backend exists among the tracked runtime-source files identified below. **No UI bug can be marked confirmed without a UI repository.** The presence of Python user-facing API functions does not mean a separate role/auth system exists.

## Frozen 31-file executable/config manifest (Git blob SHA-1)

Git object hash computed exactly as `sha1(b"blob " + byte_length + b"\0" + raw_file_bytes)` and matched to GitLab tree IDs. This protects against accidentally planning from an out-of-date source snapshot.

| Frozen file | Git blob SHA-1 |
|---|---|
| `examples/empty_example.py` | `907eeb23ba0ca665fd84909ccfd9e7f50d158a12` |
| `examples/geoip_example.py` | `2839da7835b5e5c65efec85131653b4828ce2e79` |
| `examples/stealth_example.py` | `f5124356bb1eb957673225ee385967bf95038ab8` |
| `pyproject.toml` | `d04a2aa3604d6fbe320019ddd12afa0ddb12606a` |
| `stealth_engine/__init__.py` | `71c3cf1d8d21a87c8e9f313cdacf7b8f2c4cd960` |
| `stealth_engine/behavior.py` | `78ae65d7d2c5a008d3adbe6242a3dc67dd594ae9` |
| `stealth_engine/config.py` | `dc9fc5aecb7c331d12251a5bdb1a95b525c32bcf` |
| `stealth_engine/engine.py` | `37eb32b1840a7a220796a61de7ff98f2fab4fa05` |
| `stealth_engine/exceptions.py` | `cfe1f0b46c363f1d1ef81f7d8f177d89daaf7426` |
| `stealth_engine/geo.py` | `6b696b2f204f2b0222e2e81de7bc5e30055fdc3e` |
| `stealth_engine/identity.py` | `e5943855b416890b8b718a1d778c00ed61f24b48` |
| `stealth_engine/orchestrator.py` | `565bf785869ba9e99d5529a9cf7d3ff9b5bb3ee0` |
| `stealth_engine/proxy.py` | `59706d4ba7f5e3d4b038c14b594e49c6ea7dd513` |
| `stealth_engine/risk.py` | `1ecbab20ecb6ae5dce9e4143c12f650af2dff684` |
| `stealth_engine/session.py` | `fe06fe08196d9dbc2cb84a60a8f44b687dcbf629` |
| `stealth_engine/utils/__init__.py` | `8e6420261efb11612317441c6fd6cb033332bb64` |
| `stealth_engine/utils/logging.py` | `024e6153dbcd5ff9df05e103c4ed38668aa1d248` |
| `tests/__init__.py` | `1f6e2e1ac9b7d74b06cc50dbc6a6a5b31c7514d5` |
| `tests/test_behavior.py` | `d12842dbe5346a1f9c88e4e41c049f83f42f5b36` |
| `tests/test_bugfix.py` | `eb227ba7d4b80a52f9a57355582e057c71abb4cf` |
| `tests/test_engine_depth.py` | `fa325557bbacf04c6e8036af639b404b74781a7c` |
| `tests/test_feature_p_y.py` | `e3db307768e29f5c3268eeb549e00a3c2050d016` |
| `tests/test_forensic_regressions.py` | `ae0fc8ad34924a2bbd54aca0c875b4b8f5720507` |
| `tests/test_geo.py` | `c366e088a55ffeafb195f3ebdac01ebc303240d5` |
| `tests/test_ghost.py` | `57e15bb145ad920459ca09dc211014c2a62c9f1e` |
| `tests/test_hardening.py` | `4531382b54d8ccbd0fe7e0afe8398236053cef3b` |
| `tests/test_hygiene.py` | `8750bfb04c4ee46be7094305d4d5a44323486de8` |
| `tests/test_meta.py` | `2d659df6c6c03665179a0a0fcb1d2db2689c9302` |
| `tests/test_placeholder.py` | `2a28ecb1bda9beb2f04c43fbd8e709acaf44925d` |
| `tests/test_smoke.py` | `0d03e0e4ec18d4d367e3791547bc08f948c41c31` |
| `tests/test_uxpack.py` | `30bd6d6d72f77345500574f4bd26f3bdb6386c67` |


## Freeze rules

- Every phase must start by checking the current remote `main` SHA and verifying no unexpected source-blob change; plan/reference SHA remains `a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5` for audit provenance.
- If a source file changes before its locked phase, mark **BASELINE DRIFT**, stop that phase and record the exact new SHA/diff before replanning. No silent scope extension.
- Do not rewrite original `notes/production/2026-11-16-*` forensic evidence; planning docs reside only in `notes/productions/`.
- Preserve tests, config schema, public Python APIs, examples, packaging, identity/cookie/profile data and all unrelated features unless a phase explicitly allows a change.
- Each implementation phase gets a separate Git commit and one focused verification, then patch audit, then status docs update; run a full suite only for final release gate.

## Runtime evidence is narrower than source completeness

- Prior audit: `compileall` succeeded; JSON config round-trip, storage state round-trip, proxy parse, Geo policy, Bezier path, heuristic score passed *isolated* checks.
- Prior audit: normal `pytest` **did not pass**; collection halted with missing `browserforge` on audit host. The frozen project runtime deps may be installable elsewhere; absence here does not prove packaging is broken.
- Prior audit: real Camoufox launch, WebRTC leak, live proxy exits, fingerprint readback, HAR/upload/download and large-scale bulk runner **were not executed**. These cannot be called actual production working.
- Test gate variables referenced by `tests/test_smoke.py` and related tests require explicit live acceptance execution; don't simulate a pass.

**[Source: `stealth_engine/identity.py:10-18`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/identity.py#L10-18)**

```python
  10 | import secrets
  11 | from pathlib import Path
  12 | from typing import Any, Protocol
  13 | 
  14 | from browserforge.fingerprints import FingerprintGenerator
  15 | 
  16 | from .config import ProfileConfig
  17 | from .exceptions import IdentityError
  18 | from .utils.logging import get_logger
```

**[Source: `stealth_engine/engine.py:363-372`](https://gitlab.com/ivibtools/stealth-engine/-/blob/a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5/stealth_engine/engine.py#L363-372)**

```python
 363 |             try:
 364 |                 from camoufox.async_api import AsyncCamoufox  # type: ignore[import]
 365 |             except ImportError as exc:
 366 |                 raise LaunchError(
 367 |                     "camoufox is not installed; run: pip install 'camoufox[geoip]'",
 368 |                     details={"stage": stage, "reason": str(exc)},
 369 |                 ) from exc
 370 | 
 371 |             ctx_handle = AsyncCamoufox(**launch_kwargs)
 372 |             playwright_ctx: PlaywrightBrowserContext = await ctx_handle.__aenter__()
```


**Next authorized work:** Plan is ready for review, but **no phase is authorized or started by this document alone**.
