# Feature W: WebRTC leak prevention

**Status:** Partially implemented; launch hints are guarded, but general leak prevention is not guaranteed.
**Primary module(s):** `engine.py`

## Description

Mode A (no proxy): the engine passes `webrtc:ipv4` only when `config.target_ip` or the best-effort host address is a globally routable IPv4; otherwise it omits the manual hint. Mode B: Camoufox GeoIP handles WebRTC when `cfg.geoip` is enabled. These configuration paths do not guarantee that DNS, STUN, NAT, or WebRTC candidates are leak-free on arbitrary networks; proxy-specific behavior remains unverified.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change                                     |
| ------- | ------------------------------------------ |
| 0.1.0   | Feature defined and documented             |
| PH-07   | Status synced — implemented since PH-03/04 |
