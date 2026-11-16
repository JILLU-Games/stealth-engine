# Feature S: Seed-controlled reproducibility

**Status:** Partially implemented — device seeds + proxy order deterministic; complete fingerprint reproducibility limited by browserforge global `random`  
**Primary module(s):** `config.py + identity.py + proxy.py`

## Description

`get_or_create_seeds()` persists deterministic Canvas, audio, and font seed values per profile in the resolved profile root's `seeds.json`; locale/timezone follow config → host → fallback with source metadata. The engine consumes the device seeds at launch (PH-03/04). Proxy selection order is independently seeded in `ProxyManager`. Complete fingerprint reproducibility across generator instances is not guaranteed (browserforge uses process-global `random`).

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-02 | Added persistent per-profile seed values |
| PH-07 | Status synced — engine consumption live; reproducibility limitation documented |
