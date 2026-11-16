# Feature N: No JS-injection fingerprint spoofing

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `engine.py`

## Description

Fingerprint overrides are applied at the camoufox C++ layer (device seeds + geoip launch options). `page.evaluate`/CDP are not used for spoofing **by default**. Exception: `ProfileConfig.js_noise=True` (PH-20) installs an opt-in init script adding deterministic seeded canvas/WebGL readback noise — experimental, documented as potentially detectable, disabled by default.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — implemented since initial engine phase |
| PH-20 | `js_noise` opt-in exception documented |
| BF-02 | toDataURL noise moved to offscreen clone (no live-canvas mutation) |
