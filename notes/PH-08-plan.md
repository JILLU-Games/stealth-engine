# PH-08 Plan — GeoIP gate owner decision (docs-only)

Date: 2026-11-15

## Decision (from owner)

`ProfileConfig.geoip` ON/OFF gate stays AS-IS. Rationale: stealth_engine is a
global reusable API — `modules/engine` must stay generic; whichever app
consumes the engine decides per-use-case whether GeoIP alignment is on or
off. The frozen Step-4 text (`geoip=True` unconditional) is superseded by
this owner decision for the `cfg.geoip=False` + proxy case.

## Changes (docs only, NO code)

- `docs/MODULES.md` — rewrite the PH-07 "Known deviation" bullet into an
  "Owner decision" note: gate is intentional per-app toggle.
- `MEMORY.md` — same conversion.
- `project/features/F-geoip-proxy.md` — strengthen wording: gate is the
  designed per-app switch.
- `project/modules/engine.md` — clarify `geoip=config.geoip` is intentional.
- `CHANGELOG.md` — record decision.
- `notes/PH-08-plan.md`, `notes/PH-08-log.md`, `notes/MANIFEST.md`.

## Non-goals

- No code change. `docs/ROADMAP-v2-FREEZE.md` stays untouched (frozen).
