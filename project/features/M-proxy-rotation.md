# Feature M: Native proxy rotation

**Status:** Partially implemented — standalone pool selection exists; engine profile uses one configured proxy.
**Primary module(s):** `proxy.py`

## Description

`ProxyManager` can hold a proxy pool with seeded selection; each `pick_healthy()` selects a healthy proxy. This pool is available when using `ProxyManager` directly. `StealthEngine` currently constructs its manager from the single `ProfileConfig.proxy` configured for that profile, so an engine-level automatic pool/rotation interface is not exposed.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change                                                |
| ------- | ----------------------------------------------------- |
| 0.1.0   | Feature defined and documented                        |
| PH-07   | Status synced — implemented since initial proxy phase |
