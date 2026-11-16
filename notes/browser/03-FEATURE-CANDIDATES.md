# 03 — FEATURE CANDIDATES (browser-depth scope)

## MUST-HAVE (recommended)

| ID | Feature | What it does | Why must |
|---|---|---|---|
| M1 | `verify_stealth(page)` | One-call composite audit: probe_fingerprint + ban_risk_score + validate_geo_consistency + validate_fingerprint → unified report | Without it, stealth claims are unverifiable |
| M2 | CDP session passthrough | `session.cdp_session(page)` → raw CDP for network intercept, cookie control, console, metrics | Unlocks advanced automation impossible via playwright API |
| M3 | HAR/video recording | ProfileConfig or session options: `record_har_path`, `record_video_dir` | Production debugging/replay essential |
| M4 | `new_context()` | Spawn additional isolated BrowserContexts in same browser process | Multi-account resource efficiency; pairs with BulkRunner |

## NICE-TO-HAVE (defer unless needed)

| ID | Feature | Note |
|---|---|---|
| N1 | BrowserBackend adapter protocol | Premature — camoufox is best; revisit only if 2nd engine needed |
| N2 | Tracing (playwright trace) | Subset of HAR/debug; cheap to add later |
| N3 | Mobile deep emulation (touch/geo sensors) | camoufox os="android" partial; niche demand |
| N4 | WebSocket/frame capture via CDP | Covered by M2 once CDP exposed |
| N5 | Session video auto-attach to ProfileResult | App-level concern |

## SKIP (wrong layer / violates constraints)

| I
