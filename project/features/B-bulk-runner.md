# Feature B: Bulk runner with bounded concurrency

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `orchestrator.py`

## Description

`BulkRunner` uses an `asyncio.Semaphore` to cap the number of simultaneously running browser contexts, preventing resource exhaustion on the host machine. Results are returned in input order regardless of completion order.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-07 | Status synced — implemented since initial orchestrator phase |
