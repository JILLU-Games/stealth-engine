# 00 — BASELINE FREEZE (bugFix audit)

Frozen at commit `25a2993` (2026-11-16), before any bugFix work.

## Verified state

- Version: stealth_engine 0.2.0 (+ PH-13..21 uncommitted-to-release
  but committed to git: d2ecb8f, 247564e, 482c31e, 25a2993)
- Tests: 165 (161 pass + 4 env-gated skips)
- Public API: 29 names — all resolve on import
- Modules: config, identity, engine, session, proxy, geo, behavior,
  orchestrator, risk, exceptions, utils/logging
- Git: clean tree at freeze point

## Audit coverage (deep scan, 2 passes)

| Module | Lines reviewed | Bugs found |
|---|---|---|
| engine.py | ~1700 | 8 (B-01,03,05,06,07,10,12,22-part) |
| session.py | ~480 | 2 (B-02, B-04) |
| identity.py | ~780 | 2 (B-11, B-18) |
| proxy.py | ~700 | 2 (B-08, B-09, B-21-part) |
| geo.py | ~700 | 1 (B-17) |
| orchestrator.py | ~450 | 1 (B-19) |
| behavior.py | ~300 | 0 |
| config.py | ~380 | 0 |
| risk.py | ~100 | 0 |
| exceptions/utils | ~100 | 0 |

Total: 23 findings — 3 critical, 4 major, 16 minor/cosmetic.
