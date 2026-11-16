# notes/advance/ — Next-Level Stealth Work Package

All documentation for the "full identity concealment" feature line.
Read in order:

| File | Contents |
|---|---|
| `00-BASELINE-FREEZE.md` | Frozen v0.2.0 baseline + stealth coverage today |
| `01-FEATURE-CATALOG.md` | All candidate features (N1-N56) with scoring + shortlists |
| `02-CURRENT-STATE.md` | Compact forensic snapshot — what exists |
| `03-STEALTH-GAPS.md` | Forensic gap analysis — what leaks identity, by risk |
| `04-ROADMAP-PHASES.md` | PH-13…PH-18 scope-locked implementation plan |
| `05-PHASE-LOG.md` | Running phase-completion log |
| `06-ERROR-HANDLING.md` | Exception model + per-phase error additions |
| `07-IMPLEMENTED-STATUS.md` | Working/pending tracker + stealth coverage score |

## Workflow

1. Owner picks phases/features from catalog/roadmap.
2. Scope-locked plan per phase; implement; test; docs.
3. Update `05-PHASE-LOG.md` + `07-IMPLEMENTED-STATUS.md` after each phase.
4. New error paths → update `06-ERROR-HANDLING.md`.
