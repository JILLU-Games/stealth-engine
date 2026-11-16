# 04 — RECOMMENDED SCOPE (decision doc)

## Recommendation: implement M1–M4 as "PH-19 Engine Depth"

| Item | Effort | Risk | Value |
|---|---|---|---|
| M1 verify_stealth | S | none | High — safety audit one-call |
| M2 CDP passthrough | M | low | High — unlocks advanced control |
| M3 HAR/video recording | S | none | Medium-high — debugging essential |
| M4 new_context | M | med | Medium — verify camoufox feasibility first |

## Explicitly NOT doing

- No engine swap (camoufox stays — proven best)
- No JS-level spoofing (Feature N)
- No premature abstraction (BrowserBackend deferred)
- No app-level features (scrapers, trackers, dashboards)

## Open verification needed during implementation

1. Does camoufox persistent context expose `new_cdp_session`? (Firefox
   CDP/Juggler support — verify before M2 commit)
2. Does `record_har_path`/`record_video_dir` work through
   AsyncCamoufox kwargs? (playwright context options passthrough)
3. Can a persistent context spawn additional contexts, or does M4 need
   `browser.new_context()` on a non-persistent launch?

## Decision needed from owner

- Approve M1–M4 as PH-19? Or subset?
- M4 feasibility risk acceptable (may need design adjustment)?
