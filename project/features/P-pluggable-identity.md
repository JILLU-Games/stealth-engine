# Feature P: Pluggable identity providers

**Status:** Implemented (PH-06)  
**Primary module(s):** `identity.py`, `engine.py`, `orchestrator.py`

## Description

browserforge is the default fingerprint provider via
`BrowserForgeIdentityProvider`. Custom generators plug in through the
`IdentityProvider` protocol (`build(config, rng) -> dict`); the provider
returns the raw fingerprint dict and `IdentityGenerator` applies
`ProfileConfig.locale`/`timezone` overrides plus final validation uniformly
for every provider.

## Location in codebase

- `stealth_engine/identity.py` — `IdentityProvider` (Protocol),
  `BrowserForgeIdentityProvider` (default), `IdentityGenerator(provider=...)`
- `stealth_engine/engine.py` — `StealthEngine(config, *, identity_provider=None)`
- `stealth_engine/orchestrator.py` — `BulkRunner(..., identity_provider=None)`
  shares one provider instance across all profiles in the run
- `stealth_engine/__init__.py` — both names exported lazily (17 public names)

## Usage

```python
from stealth_engine import StealthEngine, ProfileConfig

class MyProvider:
    def build(self, config, rng):
        return {...}  # same shape as IdentityGenerator.generate() output

engine = StealthEngine(config, identity_provider=MyProvider())
```

## Change History

| Version | Change |
|---------|--------|
| 0.1.0 | Feature defined and documented |
| PH-06  | Implemented: Protocol + default provider + engine/BulkRunner wiring |
