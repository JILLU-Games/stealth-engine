# Module: exceptions.py

**File:** `stealth_engine/exceptions.py`  
**Status:** ✅ Implemented (v0.1.0)  
**Public names:** `StealthEngineError`, `ConfigError`, `IdentityError`, `ProxyError`, `SessionError`, `LaunchError`, `AutomationError`

## Purpose
Single exception hierarchy for all stealth_engine errors. No logging or logic — pure exception classes.

## Hierarchy
```
StealthEngineError (base)
├── ConfigError
├── IdentityError
├── ProxyError
├── SessionError
├── LaunchError
└── AutomationError
```

## Base class: StealthEngineError
- `message: str` — human-readable error description
- `details: dict | None` — optional diagnostic context
- `__str__` — returns message + compact details repr when present

## Change History
| Version | Change |
|---------|--------|
| 0.1.0 | Initial implementation |
