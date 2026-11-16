# notes/browser/ — Browser Engine Work Package

All research + implementation docs for browser runtime/engine depth.

## Research (review before deciding)

| File | Contents |
|---|---|
| `00-BASELINE.md` | Current camoufox+playwright stack, verified facts |
| `01-ENGINE-COMPARISON.md` | Engine options analysis — why camoufox stays |
| `02-STEALTH-SURFACE.md` | Covered vs residual detection surface |
| `03-FEATURE-CANDIDATES.md` | M1-M4 must-have, N1-N5 nice, S1-S7 skip |
| `04-RECOMMENDED-SCOPE.md` | PH-19 recommendation + verification needs |

## Implementation tracking

| File | Contents |
|---|---|
| `05-ROADMAP-PHASES.md` | PH-19/PH-20 scope-locked plan |
| `06-PHASE-LOG.md` | Running phase-completion log |
| `07-ERROR-HANDLING.md` | Exception model + per-item error paths |
| `08-IMPLEMENTED-STATUS.md` | Working/pending tracker + capability score |

## Workflow

1. Review 00-04 → decide scope (M1-M4 or subset).
2. Approve → I write/update 05-ROADMAP if scope changes.
3. Implement per phase → update 06/08 + project/+docs/.
4. New error paths → update 07.
