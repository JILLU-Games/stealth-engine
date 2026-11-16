# Feature L: Multi-profile isolation

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `session.py + engine.py`

## Description

Running N profiles in parallel produces isolated state: each profile gets its own resolved profile root (`user_data/`, `storage_state.json`, `.lock`), its own `StealthEngine`/`IdentityGenerator`/`SessionManager` instances, and per-profile locks prevent concurrent launches of the same profile.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — implemented since initial session/engine phases |
