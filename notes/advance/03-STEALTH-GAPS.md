# 01 — STEALTH GAPS (forensic: what leaks identity today)

Ordered by detection risk. Each gap = potential feature.

## Critical (high detection risk)

| ID | Gap | Where it leaks | Feature candidate |
|---|---|---|---|
| G-01 | DNS leak | Proxy DNS vs host DNS mismatch reveals real ISP | N21 DNS-over-proxy config |
| G-02 | IPv6 leak | AAAA queries bypass IPv4 proxy | N22 IPv6 disable/verify |
| G-03 | Header order | Browser header sequence fingerprintable | N24 (hard — browser-controlled) |
| G-04 | TLS/JA3/JA4 | Firefox TLS fingerprint must match claimed version | N23 verify-only |
| G-05 | HTTP/2 fingerprint | SETTINGS frame order/window sizes | N23 verify-only |
| G-06 | WebRTC complete mask | `webrtc:ipv4` covers IPv4; IPv6/STUN may leak | N20 UDP associate |

## High (fingerprint inconsistency)

| ID | Gap | Detail | Feature |
|---|---|---|---|
| G-07 | Canvas pixel noise | `canvas:seed` passed; actual noise unverified | N26 verify+wire |
| G-08 | Audio fingerprint | `audio:seed` passed; oscillator output unverified | N27 verify+wire |
| G-09 | WebGL renderer | Host GPU string may leak via WebGL | N28 `webgl_config` |
| G-10 | Font metrics | Text measurement vs claimed OS | N29 `fonts` config |
| G-11 | Screen consistency | resolution/colorDepth/pixelRatio vs UA | N34 `screen` config |
| G-12 | Hardware fields | `hardware_concurrency`/`device_memory` in fp dict but not passed | N35 wire to config |
| G-13 | Media devices | camera/mic enumeration empty or host-real | N30 `media_devices` |
| G-14 | Battery API | `getBattery()` absent/host value | N31 mock |
| G-15 | Sensor data | accel/gyro absent | N32 mock |

## Medium (behavioral/session)

| ID | Gap | Feature |
|---|---|---|
| G-16 | Mouse = jittered linear, not bezier | N36 |
| G-17 | Typing = fixed random cadence | N37 per-profile rhythm |
| G-18 | Scroll = chunked, no inertia | N38 physics scroll |
| G-18b | No dwell/focus patterns | N39-N41 attention profile |
| G-19 | Cookie/storage cross-profile leak risk | N42 audit |
| G-20 | Empty localStorage = bot signal | N43 seeded storage |
| G-21 | Permission states inconsistent | N48-N49 |
| G-22 | Gamepad/WebUSB/WebSerial empty arrays | N51-N52 verify consistent |

## Low (orchestration/meta)

| ID | Gap | Feature |
|---|---|---|
| G-23 | Same profile = same fingerprint every launch | N53 diversity option |
| G-24 | No ban-risk scoring | N55 |
| G-25 | No fingerprint drift tracking | N9 |

## Out of scope (impossible/frozen)

- JS-level patches (Feature N violation)
- Per-page geo (Camoufox infeasible)
- BrowserForge full wiring (frozen non-goal)
- Header-order tampering (browser controls; tampering = new fingerprint)
- "Total identity hide" — asymptotic; layers above reduce surface
