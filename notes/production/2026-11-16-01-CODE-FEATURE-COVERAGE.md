# Production Source Forensic Audit — Feature Coverage

**Repository:** `ivibtools/stealth-engine`  
**Code revision:** `6255383cac9f29d64bf9ee5957c77ee26ccd7993`  
**Date:** 2026-11-16 UTC  
**Evidence method:** GitLab tree and exact Git-blob hash verification for every audited Python/config file, direct AST/source review, isolated read-only probes. No project Markdown documents used for conclusions.

## Inventory & evidence provenance

- GitLab `main` at audit start had **154 tracked files** (including notes); verified **31 files** in executable Python/config scope: **13 runtime `.py`**, **14 test `.py`**, **3 example `.py`**, **1 `pyproject.toml`**. Each ZIP snapshot Git blob SHA-1 matched the GitLab repository tree ID for these 31 files. The rest are documentation/license/metadata, not executable browser/UI source.
- Runtime reviewed: `stealth_engine/__init__.py`, `behavior.py`, `config.py`, `engine.py`, `exceptions.py`, `geo.py`, `identity.py`, `orchestrator.py`, `proxy.py`, `risk.py`, `session.py`, `utils/__init__.py`, `utils/logging.py`.
- Test paths reviewed: `tests/test_*.py` and environment gates. Test existence and passing real-world behavior are different facts.
- **No GUI/Web UI or admin dashboard implementation exists among tracked application code.** This repo ships a Python library. Therefore no user/admin buttons or allegedly working visible UI were available to inspect or classify; this does not prove a separate external app lacks a UI.
- No explicit `demo_mode` or demo/production backend switch is present in the reviewed runtime Python modules. Test doubles/mocks in tests are **not** proof that an application feature is demo-only.

## Per-feature source-to-runtime coverage

| Feature / user-facing API | Source anchor | Evidence-backed status | Production proof boundary |
|---|---|---|---|
| Profile config (`ProfileConfig`, presets) | `config.py:65-190, 342-382` | Implemented; JSON validation/round-trip offline passed; F-13 invalid Android preset | No user UI |
| JSON/YAML config export/import | `config.py:249-329` | Implemented; JSON round-trip offline passed; F-10 plaintext credentials/permissions | YAML real-user path and Windows ACL untested |
| Identity provider / generated fingerprint | `identity.py:130-292, 362-619` | Implemented generation code; engine application gap F-03 | BrowserForge/Camoufox identity readback unverified |
| Deterministic seeds & diversity | `identity.py:376-572` | Persisted seed code exists; F-04 stale override behavior | Whole fingerprint reproducibility in live browser unverified |
| Camoufox async launch / persistent context | `engine.py:258-424, 594-721` | Code path exists; F-06 cleanup issue | Cannot claim real browser launch success |
| Sync launch and session controls | `engine.py:229-256, 754-1058` | F-01/F-02, multiple deliberately unsupported sync helpers | No live sync browser test |
| Proxies, rotation, health, GeoIP | `proxy.py:190-615` | Standalone pool and selection code exist; F-05 SOCKS proxy health path | No real proxy endpoint tested |
| GeoResolver, geo filters, drift tracking | `geo.py:34-572` | Pure geo parsing/policy offline passed; F-14 in validator | Real GeoIP APIs unverified |
| Persistent profiles, lock, state export/import | `session.py:61-571` | JSON storage-state offline round-trip passed; F-07/F-08/F-09 safety failures | Real Firefox profile restore unverified |
| BulkRunner concurrency/retries | `orchestrator.py:61-462` | Async scheduling implementation exists, per-profile retry/cleanup | No live multi-browser load/timeout observation |
| Human move/type/scroll/dwell | `behavior.py:35-301`, `engine.py:1074-1269` | Bezier generator offline passed; async wrappers exist | Human interactions in real browser not tested |
| Request listeners/routes/tracker block | `engine.py:1481-1560` | Route handlers exist; F-17 false positive reproduced | Real browser traffic not tested |
| Download/upload, headers, HAR | `engine.py:1271-1423, 666-687` | Wrappers/config paths exist; video unsupported | Real upload/download/HAR not tested |
| JS canvas/WebGL noise | `engine.py:67-137, 375-385` | Experimental script; F-16 identical-read instability reproduced in JS test double | Camoufox fingerprint readback not tested |
| Fingerprint probe + risk heuristic | `engine.py:1324-1392, 1592-1661`, `risk.py:24-99` | Probe JS and heuristic scoring code exist; pure risk scoring returned score in offline test | Risk score is **not** observed bot-detection bypass or ban probability |
| Logging levels | `config.py:148`, `utils/logging.py:13-49` | Logger configured independently; F-19 profile setting unconnected | App-integrated log filtering unverified |
| Browser CDP and extra contexts | `engine.py:1663-1747` | Conditional/unsupported paths; separate report | No live Camoufox context creation test |
| Admin panel, role permissions, UI controls | No HTML/JS GUI/backend route/auth controller in tracked code | **Not implemented in this repo's reviewed code** | Cannot infer external product UI status |

## Offline positive evidence (not a browser pass)

- `python -m compileall -q stealth_engine tests examples`: **passed** on Python 3.13 audit host.
- `ProfileConfig.save_json()` → `load_json()` equality: **passed**.
- `SessionManager.export_state()` → `import_state()` exact dict equality: **passed** in isolated temporary directory.
- `_parse_proxy_line('127.0.0.1:8080')`: yielded `http://127.0.0.1:8080`.
- `bezier_path(..., steps=6)`: returned 7 path points.
- `parse_geo_data` returned country `US` for supplied fixed JSON; country filter `US` matched.
- `ban_risk_score({})` returned numeric score `75` (heuristic computation only).

## UI/user/admin audit outcome

Repository files are Python library, tests, examples, build metadata, Markdown and license. There is no standalone application GUI or web administration frontend/backend here. No screenshot/UI build was provided for this version. Thus **0 source-evidenced nonfunctional UI controls** can be enumerated; do not misread that as proof all UI works. User-initiated controls exist via Python APIs (`ProfileConfig`, session/profile handling, BulkRunner); authorization, authentication and admin roles are **not implemented here**, and should not be conflated with missing features of a separate application.

## Evidence traceability

All source links in the companion findings report pin the exact revision `[code snapshot](https://gitlab.com/ivibtools/stealth-engine/-/blob/6255383cac9f29d64bf9ee5957c77ee26ccd7993/stealth_engine/engine.py)`. An unverified real-browser behavior is not marked as confirmed functioning or confirmed failing.
