# Feature A: Async & sync launch API

**Status:** Implemented (v0.1.0)
**Primary module(s):** `engine.py`

## Description

`StealthEngine` provides `await engine.alaunch()` and `engine.launch()`. The sync entry point owns a background asyncio loop until the session is closed; it raises `LaunchError` when called inside a running event loop. `BrowserSession` supports `with`/`async with` context managers. Playwright page operations remain async: sync `new_page`, state-save, and human-hook methods raise `AutomationError` and direct callers to async alternatives.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version     | Change                                                                                                                                            |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0.1.0       | Feature defined and documented                                                                                                                    |
| PH-07       | Status synced — implemented since initial engine phase                                                                                            |
| BF-03/BF-04 | Corrected description — engine itself has no context manager; `BrowserSession` does; `new_page_async`/`save_state_async` added for async contexts |
