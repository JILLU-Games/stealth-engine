# notes/geoip/ — GeoIP Work Package

All documentation for the geoip feature line. Read in order:

| File | Contents |
|---|---|
| `00-BASELINE-FREEZE.md` | Frozen current-state snapshot (code, tests, limitations, rules) |
| `01-PRODUCTION-GAPS.md` | Every bug/gap/missing feature found by forensic audit, with fix-phase mapping |
| `02-ROADMAP-PHASES.md` | PH-09…PH-12 step-by-step scope-locked implementation plan |
| `03-PHASE-LOG.md` | Running phase-completion log + status dashboard |
| `04-ERROR-HANDLING.md` | Current exception model, per-phase new errors, invariants |
| `05-IMPLEMENTED-STATUS.md` | What's working now / added per phase / still pending |
| `GEOIP-FEATURE-AUDIT.md` | The 28-item feature inventory (used vs missing) |

## Workflow

1. Baseline is frozen in `00` — do not change retroactively.
2. Implement phases in `02` order; each phase scope-locked.
3. After each phase: update `03` log + `05` status tracker.
4. New error paths → update `04`.
