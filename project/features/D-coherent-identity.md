# Feature D: Coherent identity via browserforge

**Status:** Partially implemented — coherent dict generated and validated by browserforge; not fully applied to the browser (see Feature C limitation)  
**Primary module(s):** `identity.py`

## Description

UA string, navigator fields, screen/viewport, locale, timezone, hardware fields, color scheme, and reduced-motion are generated as a consistent set by browserforge (via `BrowserForgeIdentityProvider`, Feature P) and validated before use. The dict currently feeds launch `locale` and diagnostics; full application to Camoufox remains the documented Feature C limitation.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — generation/validation implemented; browser application partial |
