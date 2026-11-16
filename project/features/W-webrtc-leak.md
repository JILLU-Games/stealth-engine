# Feature W: WebRTC leak prevention

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `engine.py`

## Description

Mode A (no proxy): `webrtc:ipv4` launch option advertises `config.target_ip` or the resolved host IP intentionally (matches real network — avoids IP↔JS inconsistency). Mode B (proxy): WebRTC IP is handled by camoufox's `geoip` mechanism when `cfg.geoip` is enabled. No JS patching is used.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — implemented since PH-03/04 |
