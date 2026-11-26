# FINAL-DEV-01 — Candidate forensic audit

Status: IMPLEMENTATION PREPARED; CI acceptance pending. Main `f66a2d450ee99f2988e82296e0835c611881d7e3`, tree `6250c962628ed1fbc23974359cb008391fc64f5a`. Candidate identity and terminal results belong to the exact PR/Actions evidence; a candidate cannot contain its own SHA. No release.

Main CI #45901537321 SUCCESS (17 passed, one expected external skip); publisher #45901959965 SKIPPED. Both recovery phases closed.

| Matrix | Entries | Exact lock SHA256 | Acquisition evidence |
|---|---:|---|---|
| linux-3.10 | 69 | 835ed43e71dd6f080f1a10c986693bc50c339012ae28dd53c86063337156992e | [45904536864/140197993059](https://github.com/JILLU-Games/stealth-engine/actions/runs/45904536864/job/140197993059) |
| linux-3.11 | 103 | f72ebfc989611ff0ff359d4d8533ef2fc2dbdb69cdd930576ba9ee0e68a230db | [45904131651/140196696468](https://github.com/JILLU-Games/stealth-engine/actions/runs/45904131651/job/140196696468) |
| linux-3.12 | 99 | 9478f5f26e4b4bc54c1609ed88d5bfb9fcab5c001236f1c3868c2fd9380a1bc9 | [45903945231/140196098380](https://github.com/JILLU-Games/stealth-engine/actions/runs/45903945231/job/140196098380) |
| linux-3.13 | 99 | 087baed0ffba84d8dbbf0240be5c233f2d6c981882bd171680edb8426e4e4982 | [45903945231/140196097999](https://github.com/JILLU-Games/stealth-engine/actions/runs/45903945231/job/140196097999) |
| windows-3.12 | 99 | 96370d8a1d63de7bb95e869f7eda5ba0dd77ebce7720d5ac94e6b5d023e230ef | [45903945231/140196098403](https://github.com/JILLU-Games/stealth-engine/actions/runs/45903945231/job/140196098403) |

| Finding | Candidate change | Acceptance |
|---|---|---|
| FD01/B04 | Five exact locks, package_gate.py prepare, locked Core CI | Pending CI |
| FD02 | package_gate.py package, five native build/install pairs, original 3.12 Twine checks | Pending CI |
| FD03 | package_gate.py audit and build provenance, five exact version sets | Pending CI |
| FD04/B05 | pyproject.toml aiohttp<4; no runtime migration | Containment only; deprecated API remains |
| FD05/B07 | exact notes manifest, current docs | Static inventory reconciled; CI pending |
| FD06/B08 | main protected=false; API 403 Resource not accessible by integration | BLOCKED — owner action |
| FD07 | one candidate PR/CI, original test assertions unchanged | Pending CI |

Owner action: Settings > Branches or Rulesets > main, require PR and GitHub Actions check `Aggregate CI verdict (NO automatic release)` (observed app ID 15368); disallow force pushes/deletion; review policy by owner. No settings write without permission.

No runtime/test/core-release.yml changes. Python wheel locks do not pin OS/browser downloads; no byte-identical cross-platform build claim. Existing unsupported capabilities and external network behavior remain unverified. PR-05 DEFERRED / NOT AUTHORIZED. Terminal evidence belongs to the PR conversation rather than a second CI-triggering commit.
