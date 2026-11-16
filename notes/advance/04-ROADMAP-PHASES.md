# 02 — ROADMAP: Next-Level Stealth Phases

Phases are scope-locked. Owner picks order/scope; each phase independent.
Continuation numbering: PH-13+.

Legend: ✅ planned · ⬜ pending · owner chooses

---

## PH-13 — Network/IP Hardening (G-01, G-02, G-06 partial)

**Scope lock:** `proxy.py`, `engine.py` (launch kwargs only), tests, docs.

| Item | Deliverable |
|---|---|
| N21 | Firefox pref `network.proxy.socks_remote_dns=1` when SOCKS proxy used |
| N22 | `network.dns.disableIPv6` / IPv6 leak guard config option |
| N20 | Document WebRTC IPv6/STUN limitation OR `webrtc:ipv6` kwarg if camoufox supports |
| N25 | `ProxyConfig` scheme validation extended (socks5h://) |

**Non-goals:** no TLS/HTTP2 changes, no new modules.

---

## PH-14 — Fingerprint Depth (G-07…G-15)

**Scope lock:** `engine.py` (`_build_launch_kwargs`), `config.py` (optional fields), tests, docs.

| Item | Deliverable |
|---|---|
| N26/N27 | Verify canvas/audio seeds reach camoufox pixel layer; document result |
| N28 | `webgl_config` pass-through when config sets vendor/renderer |
| N29 | `fonts`/`custom_fonts_only` pass-through option |
| N34 | `screen` config pass-through (resolution/depth/pixelRatio) |
| N35 | `hardware_concurrency`/`device_memory` → camoufox config keys |
| N30 | `media_devices` mock option |
| N31/N32 | Battery/sensor mocks — only if camoufox supports; else document |
| N12 | (optional) download/upload helpers |

**Non-goals:** no new spoofing mechanism; only wire existing camoufox options.

---

## PH-15 — Behavioral Biometrics (G-16…G-18b)

**Scope lock:** `engine.py` (BrowserSession hooks), tests, docs.

| Item | Deliverable |
|---|---|
| N36 | Bezier-curve `mouse.move` trajectory (replace jittered linear) |
| N37 | Per-profile typing cadence profile (persisted, seed-derived) |
| N38 | Physics-based scroll (inertia/easing) |
| N39-N41 | Attention profile: dwell times, focus/blur patterns, idle micro-moves |

**Non-goals:** no ML models; deterministic seeded randomness only.

---

## PH-16 — Session Hygiene (G-19…G-22)

**Scope lock:** `session.py`, `engine.py`, tests, docs.

| Item | Deliverable |
|---|---|
| N42 | Cross-profile storage_state leak audit + test |
| N43 | Optional seeded localStorage injection |
| N44 | Cache-header consistency check (verify-only) |
| N47 | Canvas/WebGL readback consistency self-check |
| N48/N49 | Permission API state consistency (notification/geolocation) |
| N51/N52 | Verify gamepad/USB/serial empty-state consistency |

---

## PH-17 — Orchestration/Meta (G-23…G-25)

**Scope lock:** `engine.py`, `orchestrator.py`, `identity.py`, tests, docs.

| Item | Deliverable |
|---|---|
| N53 | `fingerprint_diversity` option — same profile, varied identity per launch |
| N9 | Fingerprint drift detection across launches |
| N55 | Ban-risk scoring heuristic (aggregate signals → score) |
| N54 | (optional) time-based fingerprint rotation schedule |
| N56 | (optional) A/B fingerprint comparison harness |

---

## PH-18 — Practical UX pack (from catalog N1-N8)

Independent of stealth phases; can run anytime.

| Item | Deliverable |
|---|---|
| N1 | Proxy pool file import (`host:port:user:pass` parser) |
| N2 | `validate_fingerprint()` consistency scorer |
| N3 | Sticky geo binding persistence |
| N4 | Geo drift monitor |
| N5 | Session warmup flow templates |
| N6 | Request/response hooks |
| N7 | Config presets |
| N8 | Selective storage_state export |

---

## Dependency notes

- PH-14 depends on camoufox config-key verification (do first inside phase)
- PH-15 independent
- PH-16 partially depends on PH-14 (storage consistency needs fingerprint stable)
- PH-17 depends on PH-14 (drift detection needs stable baseline)
- PH-18 fully independent — can interleave

## Owner decision needed

Which phases/features? Options:
- "PH-13+14" (network + fingerprint depth — highest stealth impact)
- "PH-15" (behavior only)
- "PH-18" (practical UX pack)
- Specific feature IDs from catalog
