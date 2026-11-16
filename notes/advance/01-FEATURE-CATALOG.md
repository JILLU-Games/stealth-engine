# 01 — FEATURE CATALOG (decision menu)

Every candidate feature for the next phase(s). Pick IDs and I'll implement.

Scoring: **Value** (1-5, user impact) · **Effort** (S/M/L) · **Risk** (low/med/high)

---

## A. Already implemented ✅ (for reference — do not re-pick)

| ID | Feature | Status |
|---|---|---|
| A1-A26 | All A-Z frozen features | ✅ done |
| G1 | GeoResolver (proxy/IP/host, fallback, cache, batch) | ✅ PH-09 |
| G2 | Country filters + GeoPolicy presets | ✅ PH-09/10 |
| G3 | Extended GeoInfo (region/city/lat/lon) | ✅ PH-10 |
| G4 | `locale`/`timezone="auto"` sentinel | ✅ PH-10 |
| G5 | Geo retries + health threshold | ✅ PH-11 |
| G6 | Async human hooks | ✅ PH-11 |
| G7 | BulkRunner task timeout | ✅ PH-11 |
| G8 | Mode A timezone fix | ✅ PH-11 |
| G9 | Smoke test + v0.2.0 release | ✅ PH-11/12 |

---

## B. Tier 1 — High value, feasible (RECOMMENDED)

| ID | Feature | Value | Effort | Risk | Description |
|---|---|---|---|---|---|
| **N1** | **Proxy pool file import** | 5 | S | low | Load `ProxyConfig` list from text file (host:port:user:pass — standard provider format). `ProxyManager.from_file()` / `load_proxies(path)`. Instant real-world usability. |
| **N2** | **Fingerprint audit/validator** | 5 | M | low | `validate_fingerprint(fp) -> report` — checks UA↔screen↔hardware↔locale↔timezone consistency score before launch. Anti-detect QA tool. |
| **N3** | **Sticky geo binding** | 4 | M | low | Persist `account_id → (proxy, geo)` mapping; same account always same exit. Account-safety feature, natural geoip extension. |
| **N4** | **Geo drift monitor** | 3 | S | low | Compare cached vs fresh geo; proxy exit changed → warning field in result. Silent-swap detection. |
| **N5** | **Session warmup flows** | 3 | M | med | Pre-defined flow templates: homepage → scroll → dwell → target. Human-like session building block. |
| **N6** | **Request/response hooks** | 4 | M | med | `on_request`/`on_response` callbacks per session — header inject, tracker block, logging. App flexibility. |
| **N7** | **Config profile presets** | 3 | S | low | `ProfileConfig.preset("us-mobile")` named presets + YAML save/load (Feature Y already there). |
| **N8** | **Storage state selective export** | 2 | S | low | Export cookies/storage for specific domains only. Multi-account session mgmt. |

## C. Tier 2 — Medium value, needs verification

| ID | Feature | Value | Effort | Risk | Blocker |
|---|---|---|---|---|---|
| **N9** | Fingerprint drift detection | 3 | M | med | Track `fingerprint_hash()` across launches; needs real-browser verify |
| **N10** | Captcha/turnstile hooks | 3 | L | med | Camoufox addons support verify needed |
| **N11** | Multi-tab orchestration | 3 | M | med | Same context N pages parallel — Playwright supports, logic needed |
| **N12** | Download/upload wrappers | 2 | S | low | `expect_download`/`set_input_files` helpers — niche |
| **N13** | Locale deep-override | 3 | S | med | Camoufox `config` keys `locale:language`/`region`/`script` — verify |
| **N14** | Header-order consistency | 2 | L | high | Network-layer fingerprint — hard, low ROI |

## D. Tier 3 — Risky / contradicts frozen principles (NOT recommended)

| ID | Feature | Why risky |
|---|---|---|
| ~~N15~~ | BrowserForge→Camoufox wiring | Frozen non-goal (Stage 4A incompatible) |
| ~~N16~~ | JS-level fingerprint patches | Feature N violation |
| ~~N17~~ | Per-page geo override | Infeasible in Camoufox |
| ~~N18~~ | Currency injection | No reliable browser signal |
| ~~N19~~ | Telemetry/metrics dashboard | App-level concern, not engine |

## E. Infrastructure (not features, but useful)

| ID | Item | Value | Effort | Notes |
|---|---|---|---|---|
| **I1** | GitHub Actions CI | 4 | S | `.github/workflows/test.yml` — auto-run 67 tests on push |
| **I2** | Pre-commit hooks | 2 | S | lint/format check before commit |
| **I3** | Type stubs / py.typed | 2 | S | Better IDE support for consumers |

---

## Recommended shortlists

### Option A — "Practical pack" (my top pick)
**N1 + N2 + N3** — proxy file import, fingerprint audit, sticky geo.
All high-value, low-risk, cohesive (proxy+identity+geo theme).

### Option B — "Safety pack"
**N3 + N4 + N9** — sticky binding, drift monitor, fingerprint drift.
Account-safety focused.

### Option C — "UX pack"
**N5 + N6 + N7** — warmup flows, request hooks, config presets.
Developer-experience focused.

### Option D — "Infra first"
**I1 + N1** — CI setup + proxy file import.
Foundation before features.

---

## Decision needed from owner

Pick one option (A/B/C/D) or specific IDs. I'll write scope-locked plan
and implement.
