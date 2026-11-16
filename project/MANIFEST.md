# project/ — MANIFEST

Index of all planning and feature documentation files in this folder.

## Modules

| File | Module | Description |
|------|--------|-------------|
| modules/config.md | config.py | ProfileConfig & ProxyConfig Pydantic models |
| modules/exceptions.md | exceptions.py | Exception hierarchy |
| modules/logging.md | utils/logging.py | Loguru setup |
| modules/identity.md | identity.py | Fingerprint generation |
| modules/engine.md | engine.py | StealthEngine core |
| modules/session.md | session.py | Persistent session management |
| modules/behavior.md | behavior.py | Per-profile behavioral biometrics (PH-15) |
| modules/risk.md | risk.py | Ban-risk scoring heuristic (PH-17) |
| modules/proxy.md | proxy.py | Proxy rotation & health check |
| modules/orchestrator.md | orchestrator.py | BulkRunner concurrency |
| modules/geo.md | geo.py | Standalone GeoIP resolver, filters, cache, batch, validator |

## Dependencies

| File | Purpose |
|------|---------|
| DEPENDENCIES.md | External dependencies and their project-specific purpose |

## Features

| File | Feature ID | Feature Name |
|------|-----------|--------------|
| features/A-async-sync-api.md | A | Async & sync launch API |
| features/B-bulk-runner.md | B | Bulk runner with bounded concurrency |
| features/C-camoufox-spoofing.md | C | Camoufox engine-level fingerprint spoofing |
| features/D-coherent-identity.md | D | Coherent identity via browserforge |
| features/E-deterministic-seed.md | E | Deterministic identity via seed |
| features/F-geoip-proxy.md | F | GeoIP-aware proxy binding |
| features/G-persistent-session.md | G | Isolated persistent sessions |
| features/H-human-hooks.md | H | Human-like behavior hooks |
| features/I-installable.md | I | Importable installable package |
| features/J-json-config.md | J | JSON-based profile config |
| features/K-logging.md | K | Loguru structured logging |
| features/L-multi-profile.md | L | Multi-profile isolation |
| features/M-proxy-rotation.md | M | Native proxy rotation |
| features/N-no-js-spoofing.md | N | No JS-injection fingerprint spoofing |
| features/O-retry-backoff.md | O | Orchestrator retries with backoff |
| features/P-pluggable-identity.md | P | Pluggable identity providers |
| features/Q-proxy-health.md | Q | Proxy health check + failover |
| features/R-reusable.md | R | Reusable drop-in package |
| features/S-seed-reproducibility.md | S | Seed-controlled reproducibility |
| features/T-locale-consistency.md | T | Timezone/locale/currency consistency |
| features/U-error-model.md | U | Uniform error model |
| features/V-versioned-config.md | V | Versioned config schema |
| features/W-webrtc-leak.md | W | WebRTC leak prevention |
| features/X-session-export.md | X | eXportable session artifacts |
| features/Y-yaml-json-import.md | Y | YAML/JSON profile import-export |
| features/Z-zero-global-state.md | Z | Zero global state |

> Update this table whenever a new file is added to project/.
