# Feature A: Async & sync launch API

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `engine.py`

## Description

`StealthEngine` provides `await engine.alaunch()` (async) and `engine.launch()` (sync, wraps `asyncio.run`, raises `LaunchError` inside a running loop). The returned `BrowserSession` supports `with`/`async with` context managers (`__exit__`→`close()`, `__aexit__`→`aclose()`, added BF-03).

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — implemented since initial engine phase |
| BF-03/BF-04 | Corrected description — engine itself has no context manager; `BrowserSession` does; `new_page_async`/`save_state_async` added for async contexts |
