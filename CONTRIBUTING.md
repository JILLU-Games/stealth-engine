# Contributing to stealth_engine

Thanks for your interest in contributing.

## Getting started

```bash
git clone <repo-url>
cd BrowserRuntime
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e .
```

## Running tests

```bash
python -m unittest discover -s tests
```

188 tests run by default. Real-browser tests are environment-gated and skipped automatically:

- `STEALTH_SMOKE=1` — launches a real Camoufox browser and runs `verify_stealth`
- `STEALTH_CANARY=1` — fingerprint consistency canaries

## Project layout

| Path | Purpose |
|------|---------|
| `stealth_engine/` | Package source |
| `tests/` | Unit tests (`unittest`) |
| `examples/` | Runnable usage scripts |
| `docs/` | Engine reference documentation |
| `project/` | Per-module and per-feature specs |

## Rules for changes

1. Every code change must update the matching `project/` and `docs/` markdown in the same commit.
2. Keep the public API (`stealth_engine.__all__`, 29 names) backward compatible — additions only.
3. New features must be additive; do not weaken existing stealth, isolation, or error-handling guarantees (see `docs/SECURITY.md`).
4. Tests must pass: `python -m unittest discover -s tests`.

## Reporting issues

Open an issue describing the problem, expected behaviour, and a minimal reproduction. For security-sensitive reports, see `SECURITY.md`.
