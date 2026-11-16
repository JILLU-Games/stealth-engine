# Feature Q: Proxy health check + failover

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `proxy.py`

## Description

`ProxyManager.health_check()` performs an async liveness check via aiohttp before use; `pick_healthy()` selects among proxies that pass health + GeoIP resolution and fails over to the next available proxy on failure. Proxy credentials are stripped from request URLs and passed via `aiohttp.BasicAuth`; TLS verification stays enabled.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — implemented since initial proxy phase |
