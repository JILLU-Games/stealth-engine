# stealth_engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Production Validation](https://github.com/JILLU-Games/stealth-engine/actions/workflows/production-validation.yml/badge.svg)](https://github.com/JILLU-Games/stealth-engine/actions/workflows/production-validation.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A reusable Python browser-automation engine built on [Camoufox](https://github.com/daijro/camoufox) (a fingerprint-hardened Firefox build) and Playwright. It provides consistent browser identities, per-profile session isolation, GeoIP-aware proxy handling, human-like interaction helpers, and bulk orchestration — as an installable package you import into any automation script.

**Keywords:** browser automation, Playwright, Camoufox, Firefox fingerprinting, GeoIP, proxy rotation, session isolation, anti-detect browser, web scraping, bulk runner, Python library.

Maintained by **Vib Tools** — [vib.tools](https://vib.tools/) · GitHub: [@victorsteele](https://github.com/victorsteele) (Md Nurnobi) · hello@vibtools.io

## Features

- **Consistent identities** — browserforge-backed fingerprint generation with optional per-profile seeds and pluggable providers
- **GeoIP alignment** — timezone, locale, and WebRTC derived from proxy or host geolocation, with reusable `GeoResolver`/`GeoPolicy` helpers
- **Session isolation** — per-profile `user_data_dir`, atomic storage-state export, optional seeded `localStorage`
- **Human-like interaction** — bezier mouse paths, per-profile typing cadence, physics-based scrolling, dwell/attention helpers
- **Network hardening** — SOCKS remote-DNS and IPv6-leak guards, tracker-domain blocking, request/response hooks
- **Verification tools** — `probe_fingerprint`, `validate_fingerprint`, `ban_risk_score`, and a one-call `verify_stealth` audit
- **Bulk orchestration** — `BulkRunner` with bounded concurrency, retries, backoff, per-task timeouts, and shutdown support
- **Recording & debugging** — HAR capture where supported. Video recording and CDP-only/multi-context APIs are not supported for the Camoufox/Firefox backend.

## Install

```bash
pip install -e .
```

Requires Python 3.10+. The Camoufox browser binary is fetched separately (`camoufox fetch`); all non-browser tests run without it.

## Quickstart

```python
import asyncio
from stealth_engine import ProfileConfig, StealthEngine

async def main():
    config = ProfileConfig(
        profile_name="account_1",
        user_data_dir="./profiles/account_1",
        headless=True,
        seed=42,
    )
    engine = StealthEngine(config)
    session = await engine.alaunch()
    try:
        page = session.page           # initial page, or:
        # page = await session.new_page_async()
        await page.goto("https://example.com")
        report = await session.verify_stealth(page)
        print(report["summary"])
    finally:
        await session.aclose()        # persists storage state

asyncio.run(main())
```

GeoIP-aware proxy configuration:

```python
from stealth_engine import ProfileConfig, ProxyConfig

config = ProfileConfig(
    profile_name="account_2",
    user_data_dir="./profiles/account_2",
    proxy=ProxyConfig(server="http://user:pass@proxy.example:8080"),
    geoip=True,               # derive locale/timezone/WebRTC from exit IP
    locale="auto",            # "en-US", "auto", or None
    timezone="auto",          # "America/New_York", "auto", or None
)
```

Standalone GeoIP resolution (no browser required):

```python
import asyncio
from stealth_engine import GeoResolver, GeoPolicy

async def main():
    async with GeoResolver(
        endpoints=["https://ipinfo.io/json", "https://ip-api.com/json"],
        allowed_countries=["US", "DE"],
    ) as resolver:
        geo = await resolver.resolve()          # host IP
        print(geo.country, geo.locale, geo.city, geo.latitude)
        if GeoPolicy.preset("us-strict").matches(geo):
            print("US exit confirmed")

asyncio.run(main())
```

Runnable examples live in `examples/` — including `stealth_example.py`, a full-stack demo covering config, launch, warmup, probes, and verification.

## Feature List (A–Z)

| ID | Feature |
|----|---------|
| A | Async & sync launch API (`alaunch()` / `launch()`) |
| B | Bulk runner with bounded concurrency |
| C | Camoufox C++-level fingerprint spoofing |
| D | Coherent identity generation via browserforge |
| E | Deterministic identity via seed |
| F | GeoIP-aware proxy binding (timezone, locale, WebRTC) |
| G | Isolated persistent sessions per profile |
| H | Human-like behavior hooks (mouse, typing, scroll, dwell) |
| I | Importable, installable package |
| J | JSON-based profile config (Pydantic) |
| K | Loguru structured logging |
| L | Multi-profile isolation |
| M | Standalone proxy-pool selection; engine profile uses one configured proxy |
| N | Engine-level spoofing (no JS injection by default) |
| O | Orchestrator retries with backoff |
| P | Pluggable identity providers |
| Q | Proxy health check + failover |
| R | Reusable drop-in package |
| S | Seed-controlled reproducibility |
| T | Locale/timezone consistency with exit IP |
| U | Uniform error model |
| V | Versioned config schema |
| W | WebRTC configuration guards (not a network-leak guarantee) |
| X | Exportable session artifacts |
| Y | YAML/JSON profile import-export |
| Z | Isolated browser profiles; process-global Loguru handling remains a documented limitation |

Post-A–Z additions: GeoIP resolver/policies, behavioral biometrics, fingerprint diversity + drift detection, ban-risk scoring, proxy pool import, warmup templates, tracker blocking, `verify_stealth`, CDP passthrough, HAR/video recording, multi-context support.

## Project Structure

```
BrowserRuntime/
├── stealth_engine/
│   ├── __init__.py          # public API (29 names)
│   ├── config.py            # ProfileConfig / ProxyConfig (Pydantic)
│   ├── identity.py          # fingerprint generation + providers
│   ├── engine.py            # StealthEngine + BrowserSession
│   ├── session.py           # profile dirs, locks, storage state
│   ├── proxy.py             # proxy pool, health checks, rotation
│   ├── geo.py               # GeoResolver, GeoPolicy, drift monitoring
│   ├── behavior.py          # per-profile human-interaction profiles
│   ├── orchestrator.py      # BulkRunner
│   ├── risk.py              # ban-risk heuristic scoring
│   ├── exceptions.py        # unified error hierarchy
│   └── utils/logging.py     # loguru setup
├── examples/
│   ├── empty_example.py
│   ├── geoip_example.py
│   └── stealth_example.py
├── tests/                   # Regression tests; real-browser tests are env-gated
├── docs/                    # engine reference documentation
├── project/                 # per-module/feature specs (committed)
└── pyproject.toml
```

## Documentation

| Location | Contents |
|----------|----------|
| `docs/` | Architecture, features, modules, security model, roadmap |
| `project/` | Per-module and per-feature specifications |
| `examples/` | Runnable usage scripts |

## Scope & Limitations

- Fingerprint overrides are applied at the Camoufox engine layer; an opt-in experimental `js_noise` mode adds seeded canvas/WebGL readback noise and is documented as potentially detectable.
- TLS/HTTP2 fingerprinting, IP reputation, and server-side behavioural analysis are outside this package's control.
- `ban_risk_score()` is a heuristic scorer, not a detection guarantee.
- **Core release-candidate CI accepted (2026-11-16):** [GitHub Actions Run #8](https://github.com/JILLU-Games/stealth-engine/actions/runs/43948468121) passed the defined direct-host core scope on tested Windows/Linux runners. [Exact scope, results and exclusions](notes/productions/16-CORE-PRODUCTION-ACCEPTANCE.md). The **external third-party proxy + proxy DNS/WebRTC leak contract remains UNVERIFIED**; a local proxy test is not equivalent to an external proxy.
- **Security:** JSON/YAML config exports intentionally redact proxy credentials unless `include_secrets=True` is explicitly used for a controlled private backup. Windows NTFS ACL handling requires environment-specific validation.
- **Logging:** `ProfileLogger` sanitizes its structured payloads and filters profile-owned events. Legacy module-level Loguru records remain process-global and do not inherit profile log levels.
- **Compatibility:** Synchronous `launch()` is supported, but Playwright page methods remain asynchronous. Camoufox/Firefox video recording and CDP-only interfaces are explicitly unsupported.
- **Fingerprinting:** Camoufox chooses certain runtime/browser properties independently of browserforge suggestions; validate browser-visible values rather than assuming perfect generated-to-runtime parity.
- **JS noise:** `js_noise` is opt-in experimental JS patching, potentially detectable. Readback caching has bounded per-canvas memory and is not a guarantee of fingerprint invisibility.

## Development

```bash
python -m unittest discover -s tests
```

Env-gated real-browser tests: `STEALTH_SMOKE=1` (launch + `verify_stealth` on real Camoufox) and `STEALTH_CANARY=1` (fingerprint consistency canaries).

## Links

- Website: [vib.tools](https://vib.tools/)
- Author: [Md Nurnobi (@victorsteele)](https://github.com/victorsteele)
- Issues & contributions: see `CONTRIBUTING.md`
- Security reports: see `SECURITY.md`
