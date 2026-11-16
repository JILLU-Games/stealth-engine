# Feature H: Human-like behavior hooks

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `engine.py`

## Description

`BrowserSession` exposes async interaction primitives — `ahuman_move`, `ahuman_type`, `ahuman_scroll`, `adwell` — with jittered steps and per-keystroke delays driven by an isolated `random.Random` seeded from `config.seed`. PF-02/B-25: the sync `human_*` variants were removed-functionality (unawaited coroutines on the always-async context) and now raise `AutomationError` directing callers to the `ahuman_*`/`adwell` API.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PF-02 | Sync variants raise clear errors; async API is canonical |
| PH-07 | Status synced — implemented since initial engine phase |
