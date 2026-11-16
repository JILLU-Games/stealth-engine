# Feature I: Importable installable package

**Status:** Implemented (v0.1.0)
**Primary module(s):** `pyproject.toml`

## Description

`pip install -e .` installs the `stealth_engine` package. The build uses `setuptools.build_meta` and explicitly discovers `stealth_engine*`, excluding documentation and local notes directories. Public API: `from stealth_engine import StealthEngine, BulkRunner, ProfileConfig`.

## Location in codebase

See project/modules/ for the detailed module documentation.

## Change History

| Version | Change                                                                                        |
| ------- | --------------------------------------------------------------------------------------------- |
| 0.1.0   | Feature defined and documented                                                                |
| 0.1.0   | Fixed PEP 517 backend selection and restricted package discovery so editable installs succeed |
