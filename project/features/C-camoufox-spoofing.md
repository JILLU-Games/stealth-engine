# Feature C: Camoufox engine-level fingerprint spoofing

**Status:** Partially implemented — camoufox C++ layer used; device seeds passed; full BrowserForge→Camoufox fingerprint wiring is a documented non-goal/limitation  
**Primary module(s):** `engine.py + identity.py`

## Description

Device-level fingerprint overrides (Canvas/Audio/Fonts seeds) are applied inside the camoufox engine via launch kwargs (`canvas:seed`, `audio:seed`, `fonts:spacing_seed` from `seeds.json`). No JavaScript `page.evaluate` patches are used. The complete BrowserForge fingerprint dict is intentionally NOT passed to Camoufox's `fingerprint` option (proven incompatible in Stage 4A; frozen non-goal).

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — seeds consumed at launch (PH-03/04); full fingerprint dict wiring remains a documented limitation |
