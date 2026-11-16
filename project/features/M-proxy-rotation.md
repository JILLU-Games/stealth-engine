# Feature M: Native proxy rotation

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `proxy.py`

## Description

`ProxyManager` holds a proxy pool with seeded shuffle; each `pick_healthy()` selects a healthy proxy for a new context without restarting the engine process. Per-profile proxy assignment comes from `ProfileConfig.proxy`.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — implemented since initial proxy phase |
