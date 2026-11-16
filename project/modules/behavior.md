# Module: `stealth_engine.behavior` (PH-15)

**Status:** Implemented
**Verification:** tests/test_behavior.py — all PASS

## Purpose

Per-profile persisted human-behavior parameters plus trajectory/scroll/dwell
primitives. Makes the same profile *behave* consistently across launches —
same typing cadence, scroll rhythm, mouse style — reducing behavioral
bot-detection surface.

## Public surface

| Symbol | Kind | Description |
|---|---|---|
| `BehaviorProfile` | class | Loaded/generated `behavior.json` params; `load_or_create(session, seed)`, `typing_delay`, `mouse_steps`, `mouse_total_s`, `scroll_plan` |
| `bezier_path(x0,y0,x1,y1,rng,steps)` | function | Cubic-bezier mouse waypoints with smoothstep easing + tremor jitter |
| `physics_scroll_chunks(dy,rng,profile)` | function | `(delta, pause_s)` chunks with exponential deceleration |
| `dwell_plan(rng,min_s,max_s)` | function | Attention-dwell segment schedule (`sleep`/`jiggle`) |

## Persistence

`behavior.json` written atomically (`.tmp` → `replace`) into the profile
directory (`SessionManager.profile_dir`). Generated once from
`ProfileConfig.seed`; corrupt/invalid files regenerate with a warning.
Fields: `typing` (base_delay_s, jitter_frac, word_pause_prob, word_pause_s),
`scroll` (chunks range, pause_s range, decay), `mouse` (steps range,
total_s range).

## Integration

`BrowserSession` lazily loads the profile on first human-hook use
(`_get_behavior()`). `human_move`/`ahuman_move` now follow bezier paths;
`human_type`/`ahuman_type` use per-profile cadence; `human_scroll`/
`ahuman_scroll` use physics chunks; new `human_dwell`/`adwell` simulate
attention with idle jiggle segments.

## Change History

| Phase | Change |
|---|---|
| PH-15 | Module created; hooks rewired from fixed ranges to persisted per-profile params |
