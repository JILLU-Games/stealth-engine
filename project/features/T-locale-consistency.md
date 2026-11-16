# Feature T: Timezone/locale/currency consistency

**Status:** Partially implemented — locale/timezone consistent in both modes; `GeoInfo.currency` is metadata only and not applied to the browser  
**Primary module(s):** `proxy.py + identity.py + engine.py`

## Description

Mode A (no proxy): locale/timezone_id come from `seeds.json` (config → host → fallback). Mode B (proxy + `geoip=True`): locale/timezone_id come from proxy GeoIP. `ProxyManager.GeoInfo.currency` is resolved but currently informational only — no browser-level currency override exists.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-02 | Added host locale/timezone detection for seed values |
| PH-07 | Status synced — engine application live; currency remains metadata-only |
| PH-10 | `locale`/`timezone="auto"` sentinel resolves values from GeoIP at launch (proxy geo preferred, host fallback); seeds never persist `"auto"` |
