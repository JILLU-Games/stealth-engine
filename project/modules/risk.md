# Module: `stealth_engine.risk` (PH-17)

**Status:** Implemented
**Verification:** tests/test_meta.py — all PASS

## Purpose

`ban_risk_score(probe, geo=None, config=None)` — pure heuristic scoring
(0-100) of detection/ban risk from `BrowserSession.probe_fingerprint`
output plus optional GeoIP/config signals. No I/O.

## Levels

| Score | Level | Meaning |
|---|---|---|
| 0-30 | low | Looks like a real consumer browser |
| 31-60 | medium | Suspicious signals — review before scale |
| 61-100 | high | Likely detectable — do not use for sensitive work |

## Signals weighed

Software WebGL renderer (+65 — strong headless tell), missing canvas
readback (+15), missing UA (+20), empty languages (+10), unusual/missing
hardwareConcurrency (+10), missing deviceMemory (+5), gamepad/USB/serial
presence (+3-5), timezone-vs-geo mismatch (+15), `fingerprint_diversity`
(+5), `disable_ipv6` (+2). Score capped at 100.

## Change History

| Phase | Change |
|---|---|
| PH-17 | Module created |
