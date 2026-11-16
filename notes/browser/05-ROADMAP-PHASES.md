# 05 — ROADMAP: Ghost Engine Phases

Continuation numbering: PH-19+. Owner approved "build everything feasible".
Each phase scope-locked; verify-first items marked.

Legend: ⬜ pending · ✅ complete · 🔶 verify-first

## Reality anchor (locked)

- Goal: maximal feasible stealth (~85-90% surface), NOT 100% — TLS/HTTP2,
  IP reputation, server-side ML are outside code control (documented).
- Engine stays camoufox+playwright (swap = downgrade).
- Feature N: C++-level spoofing preferred; JS-level only as opt-in,
  clearly-marked experimental.

---

## PH-19 — Engine Depth Core (M1–M4)

### M1 — `verify_stealth(page)` composite audit
- **Scope lock:** `engine.py` (BrowserSession method), tests, docs.
- **Deliverable:** async one-call report composing
  `probe_fingerprint` + `ban_risk_score` + optional
  `validate_geo_consistency` + optional `validate_fingerprint`.
  Returns `{risk, geo, fp, probe, consistent, summary}`.
- **Non-goals:** no new scoring logic.

### M2 — CDP session passthrough 🔶 verify-first
- **Scope lock:** `engine.py`, tests, docs.
- **Deliverable:** `session.cdp_session(page)` → raw CDP session via
  `context.new_cdp_session`; graceful `AutomationError` if unsupported
  (Firefox/Juggler may not implement full CDP).
- **Non-goals:** no CDP wrapper abstractions.

### M3 — HAR/video recording
- **Scope lock:** `config.py` (`record_har_path`, `record_video_dir`,
  `record_har_content`), `engine.py` launch kwargs, tests, docs.
- **Deliverable:** paths resolved under profile dir when relative;
  passed through to `launch_persistent_context` context options.

### M4 — `new_context()` 🔶 verify-first
- **Scope lock:** `engine.py`, `session.py` (doc only), tests, docs.
- **Deliverable:** `session.new_context(**kwargs)` → camoufox
  `AsyncNewContext` (per-context fpgen identity) when browser object
  reachable; graceful error otherwise. Raw context returned — caller
  owns lifecycle.
- **Non-goals:** no persistence wiring for spawned contexts (documented).

---

## PH-20 — Ghost Layer (js_noise + request normalization + warmup + aging)

| Item | Scope | Notes |
|---|---|---|
| G1 | `js_noise` opt-in | Seeded canvas/WebGL readback noise via init script — **experimental, documented detectable-risk trade-off** (camoufox adds none) |
| G2 | Request normalization | `add_route` presets: header order/lang consistency helpers |
| G3 | Warmup templates | `warmup(url, template="social"|"commerce"|"search")` flows |
| G4 | Session aging | time-based cookie/storage rotation hints + `session_age_days` report |

## PH-21 — Verification & Hardening

| Item | Scope |
|---|---|
| V1 | Expanded STEALTH_SMOKE suite (probe+verify_stealth real-browser) |
| V2 | Fingerprint canary tests (env-gated) |
| V3 | `examples/ghost_example.py` full-stack demo |
| V4 | Final docs sweep + version bump consideration |

## Dependency notes

- PH-19 items independent; M2/M4 verify-first (graceful fallback)
- PH-20 depends on PH-19 (esp. M2 for G2 deep hooks)
- PH-21 last — verifies everything

## Out of scope (locked)

- Engine replacement, TLS/JA3 customization, per-page geo, app-level
  scrapers/dashboards, any claim of 100% untrackability
