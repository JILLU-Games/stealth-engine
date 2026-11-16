# Feature F: GeoIP-aware proxy binding

**Status:** Implemented (v0.1.0) — `geoip` is the designed per-app ON/OFF toggle  
**Primary module(s):** `proxy.py + engine.py`

## Description

When a proxy is configured and `ProfileConfig.geoip` is true, timezone/locale are derived from the proxy exit IP's GeoIP record (`ProxyManager.resolve_geo`/`pick_healthy`) and applied to the launch; Camoufox `geoip=True` handles WebRTC IP. `geoip=False` with a proxy is a first-class mode: seed locale/timezone are used and Camoufox gets `geoip=False`. Owner decision (2026-11-15): the engine is a generic reusable API — each consuming app sets this flag per use-case. This intentionally differs from the literal frozen Step-4 wording (`geoip=True` unconditional); owner-approved.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — implemented; geoip-gate deviation documented |
| PH-08 | Owner decision recorded — `geoip` gate is intentional per-app toggle, not a deviation |
| PH-10 | Extended: GeoInfo region/city/lat/lon, multi-endpoint fallback, GeoPolicy presets, `locale`/`timezone="auto"` sentinel |
