# Feature K: Loguru structured logging

**Status:** Implemented (v0.1.0)  
**Primary module(s):** `utils/logging.py`

## Description

All engine events are emitted via loguru. configure_logging() sets up a single stderr sink. get_logger(name) returns a module-bound logger.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
