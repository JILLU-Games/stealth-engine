# Module: utils/logging.py

**File:** `stealth_engine/utils/logging.py`  
**Status:** ✅ Implemented (v0.1.0)  
**Public names:** `configure_logging`, `get_logger`

## Purpose
Thin loguru wrapper. Provides a single setup entry point and a module-scoped logger factory.

## Functions

### configure_logging(level="INFO", json_mode=False) -> None
- Removes loguru default handler
- Adds one stderr handler
- Idempotent — safe to call multiple times
- `json_mode=True` enables loguru JSON serialisation

### get_logger(name: str) -> Logger
- Returns `loguru.logger.bind(module=name)`
- No new logger instances; uses loguru singleton

## Module state
- `_configured: bool = False` — the only allowed module-level mutable state

## Change History
| Version | Change |
|---------|--------|
| 0.1.0 | Initial implementation |
