# notes/bugFix/ — Forensic Bug-Fix Package

Deep forensic audit of stealth_engine @ 25a2993 (2026-11-16).

| File | Contents |
|---|---|
| README.md | Index |
| 00-BASELINE-FREEZE.md | Frozen baseline + audit coverage |
| 01-FINDINGS.md | 23 bugs with exact code proof |
| 02-FIX-PLAN.md | Original A/B/C grouping (superseded by 03) |
| 03-ROADMAP-PHASES.md | BF-01..BF-04 scope-locked phases |
| 04-PHASE-LOG.md | Running phase log |
| 05-ERROR-HANDLING.md | Error model + per-bug paths |
| 06-IMPLEMENTED-STATUS.md | Bug tracker + verification checklist |

## Workflow

1. Review 01-FINDINGS → approve phase order in 03.
2. Implement BF-01 → log in 04, update 06.
3. Repeat per phase; BF-04 closes with docs sweep.
