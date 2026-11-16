# 00 — BASELINE FREEZE (2026-11-15)

Current project state snapshot — frozen reference for all future geoip work.
Verified by forensic audit + test run on this date.

## Code baseline

- Package: `stealth_engine` v0.1.0, Python >=3.10
- Public API: **17 names** (`__init__.py` `__all__`)
- Modules: `config`, `exceptions`, `identity`, `engine`, `session`, `proxy`,
  `orchestrator`, `utils/logging`
- Tests: **20/20 PASS** (`tests/test_forensic_regressions.py` 9,
  `tests/test_feature_p_y.py` 11)
- Dependencies: camoufox, playwright, browserforge, pydantic, aiohttp,
  loguru, tzlocal>=5.0, pyyaml>=6.0

## Completed phases (all verified in source)

| Phase | Scope | Status |
|---|---|---|
| Init/F1–F5 | Package wiring + 12 bug fixes | ✅ |
| PH-01…05 | Frozen roadmap Steps 1–5 (config→seeds→Mode A/B→checks #23-26) | ✅ |
| PH-06 | Feature P (pluggable identity) + Feature Y (YAML/JSON IO) | ✅ |
| PH-07 | Audit-debt cleanup (seeds validation, path fix, real #25, docs sync) | ✅ |
| PH-08 | GeoIP gate owner decision (docs-only) | ✅ |

## Feature status (26 A–Z)

- **21 Implemented**, **5 Partially implemented** (C, D, E, S, T — all with
  documented limitations, not pending work)

## GeoIP current state (see GEOIP-FEATURE-AUDIT.md)

- Implemented+consumed: 8 | Partial: 3 | Missing engine-appropriate: 8 |
  App-level (out of scope): 6 | Verify-first: 3

## Known limitations (frozen, do not "fix" without owner approval)

1. browserforge uses process-global `random` → no full fingerprint reproducibility
2. BrowserForge dict NOT passed to Camoufox `fingerprint` (Stage 4A incompatible)
3. `GeoInfo.currency` resolved but unused
4. Mode A `timezone_id` not forwarded to Camoufox (host OS timezone used)
5. "22-check F6-Final baseline" does not exist — unverifiable
6. `ProfileConfig.geoip` = intentional per-app ON/OFF gate (PH-08)
7. No `.git` in workspace
8. Real camoufox launch never smoke-tested (all tests mock it)

## Rules in force

- AGENTS.md: plan in notes/ before changes; phase log during; project/+docs/
  updated in same unit; notes/ never committed.
- Frozen doc `docs/ROADMAP-v2-FREEZE.md` untouched without owner approval.
- Engine stays generic/reusable; consuming apps own feature policy.
