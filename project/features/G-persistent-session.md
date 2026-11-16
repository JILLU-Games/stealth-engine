# Feature G: Isolated persistent sessions

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `session.py + engine.py`

## Description

Each profile runs in its own resolved profile root with a dedicated `user_data/` browser directory, `storage_state.json`, and `.lock` file. Cookies, local storage, and cache are isolated between profiles; state is exported on close via `BrowserSession.save_state_async()`/`aclose()`.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — implemented since initial session phase |
