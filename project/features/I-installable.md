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

## CI packaging acceptance (FINAL-DEV-01 candidate)

Five native x64 CI locks under `requirements/ci-*.lock` preserve exact PyPI wheel hashes. CI creates fresh environments, verifies wheel bytes, installs offline and uses no build isolation for project builds. Independent wheel/sdist acceptance on five platforms; Twine remains on Python 3.12; all matrix versions are audited from the locked 3.12 auditor. OS/browser assets are not locked; no byte-identical build guarantee. The aiohttp public requirement is constrained to <4 due to the documented deprecated API; runtime migration is deferred. Candidate acceptance pending exact CI. See `.github/ci/package_gate.py` and `notes/FINAL-DEVELOPMENT-AUDIT.md`.
