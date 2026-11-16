# Architecture

## Layer Diagram

```
┌─────────────────────────────────────────────────────┐
│                  Caller / User Script                │
│         from stealth_engine import StealthEngine,    │
│                  BulkRunner, ProfileConfig           │
└───────────────────────────┬─────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────┐
│                     Public API Layer                 │
│   StealthEngine (engine.py)  BulkRunner (orchestrator.py) │
│   ProfileConfig (config.py)                         │
└──────┬───────────────┬──────────────────┬───────────┘
       │               │                  │
┌──────▼──────┐ ┌──────▼──────┐ ┌────────▼────────┐
│ identity.py │ │  session.py │ │    proxy.py      │
│ browserforge│ │ user_data_  │ │ rotation, health │
│ fingerprint │ │ dir, export │ │ check, geoip     │
└──────┬──────┘ └──────┬──────┘ └────────┬────────┘
       │               │                  │
┌──────▼───────────────▼──────────────────▼────────┐
│                  camoufox + playwright             │
│         (C++-level browser engine substrate)      │
└───────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────┐
│   Cross-cutting: exceptions.py, utils/logging.py │
└─────────────────────────────────────────────────┘
```

---

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `config.py` | Defines `ProfileConfig` and `ProxyConfig` Pydantic models; validates and serialises profile configuration |
| `identity.py` | Generates coherent browser fingerprints via browserforge; supports seed-based determinism and pluggable providers |
| `engine.py` | Implements `StealthEngine`; manages camoufox/playwright launch, fingerprint injection at engine level, yields browser context |
| `session.py` | Manages persistent `user_data_dir` per profile; exports cookies and storage state |
| `proxy.py` | Handles proxy rotation, per-context assignment, health checks, failover, and GeoIP matching |
| `geo.py` | Standalone reusable GeoIP layer: `GeoResolver` (proxy/direct-IP/host-IP resolution, multi-endpoint fallback, TTL cache, country filters, batch), `GeoPolicy` presets, `matches_geo_policy`, `validate_geo_consistency` |
| `orchestrator.py` | Implements `BulkRunner`; drives bounded-concurrency asyncio task queue with retry and backoff |
| `behavior.py` | Per-profile persisted human-interaction parameters (typing cadence, scroll physics, mouse style) |
| `risk.py` | `ban_risk_score` heuristic scorer over probe/geo/config signals |
| `exceptions.py` | Defines the unified exception hierarchy for all stealth_engine errors |
| `utils/logging.py` | Configures loguru sinks and structured log format for all modules |

---

## Data Flow

```
ProfileConfig (config.py)
        │
        ├──► identity.py ──► fingerprint dict
        │
        ├──► proxy.py ──► validated proxy URL
        │
        └──► engine.py
                │
                ├── camoufox launch (fingerprint applied at C++ level)
                ├── playwright BrowserContext created
                ├── session.py ──► user_data_dir attached
                └── yields context to caller
                        │
                        └──► orchestrator.py (BulkRunner wraps N contexts)
```

---

## Public API Surface

```python
from stealth_engine import StealthEngine, BulkRunner, ProfileConfig
```

| Symbol | Source module | Role |
|--------|--------------|------|
| `StealthEngine` | `engine.py` | Session factory — `alaunch()`/`launch()` return a `BrowserSession` |
| `BulkRunner` | `orchestrator.py` | Multi-profile concurrent task runner |
| `ProfileConfig` | `config.py` | Pydantic model for profile + proxy configuration |

The full public API surface is 29 names — see `stealth_engine/__init__.py` `__all__` for the exact list (includes `GeoResolver`, `GeoPolicy`, `GeoInfo`, `BehaviorProfile`, `ban_risk_score`, `IdentityProvider`, `BrowserForgeIdentityProvider`, `ProfileResult`, `ProfileStatus`, exception types, and config models).
