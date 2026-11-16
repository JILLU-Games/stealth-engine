# Feature E: Deterministic identity via seed

**Status:** Partially implemented — device seeds deterministic and engine-consumed; complete fingerprint reproducibility limited by browserforge global `random` usage  
**Primary module(s):** `identity.py + config.py`

## Description

`ProfileConfig.seed` is validated as non-negative. `get_or_create_seeds()` persists per-profile Canvas, audio, and font seeds deterministically derived from `config.seed` into `seeds.json`, and the engine consumes them at launch (PH-03/04). `generate()` retains its BrowserForge output; complete fingerprint reproducibility across generator instances is not guaranteed because browserforge samples via process-global `random`.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-02 | Persist deterministic per-profile device seeds |
| PH-07 | Status synced — engine consumption live; reproducibility limitation documented |
