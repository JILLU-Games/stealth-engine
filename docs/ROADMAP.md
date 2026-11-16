> ⚠️ SUPERSEDED: see docs/ROADMAP-v2-FREEZE.md for the authoritative, frozen plan.

# Implementation Roadmap

Historical phase plan — all phases complete; kept for reference.

---

## Guiding Principles

- Implement in dependency order: lower-layer modules before higher-layer consumers.
- No phase may introduce scope changes. A-Z features are final.
- Each phase ends with the listed module(s) fully implemented and tested.
- Optional Advanced Extensions are out of scope for all phases below.

---

## Phase 1 — Engine Foundation

**Modules:** `config.py`, `exceptions.py`, `utils/logging.py`

Deliverables:

- `ProfileConfig` and `ProxyConfig` Pydantic models with validation, JSON/YAML serialisation, and `schema_version`
- Full exception hierarchy under `StealthEngineError`
- Loguru setup helper; structured log format established

Features unlocked: I, J, K, U, V, Y

---

## Phase 2 — Identity Layer

**Module:** `identity.py`

Deliverables:

- Coherent fingerprint generation via browserforge
- Seed parameter wired to deterministic output
- Pluggable provider interface defined

Features unlocked: C, D, E, N, P, S

---

## Phase 3 — Session Management

**Module:** `session.py`

Deliverables:

- Isolated `user_data_dir` creation and lifecycle management per profile
- Cookie and storage state export to disk

Features unlocked: G, L, X

---

## Phase 4 — Proxy Layer

**Module:** `proxy.py`

Deliverables:

- Proxy rotation across contexts
- Async health check and failover via aiohttp
- GeoIP metadata fetch; timezone/locale/WebRTC derived from exit IP

Features unlocked: F, M, Q, T, W

---

## Phase 5 — Core Engine

**Module:** `engine.py`

Deliverables:

- `StealthEngine` class: `alaunch()`/`launch()` factory returning `BrowserSession` (which supports `with`/`async with`)
- camoufox launch with engine-level fingerprint injection
- Integration with `identity.py`, `session.py`, `proxy.py`
- Human-like behavior hook surface exposed

Features unlocked: A, C (applied), H, R, Z

---

## Phase 6 — Bulk Orchestration

**Module:** `orchestrator.py`

Deliverables:

- `BulkRunner` with asyncio semaphore-bounded concurrency
- Retry loop with exponential backoff per task
- Per-task structured logging

Features unlocked: B, O

---

## Completion Criteria

All 26 A-Z features implemented, unit tests passing, package installable via `pip install -e .`, and `from stealth_engine import StealthEngine, BulkRunner, ProfileConfig` works without error.
