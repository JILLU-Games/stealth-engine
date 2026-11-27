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

## CI packaging acceptance (FINAL-DEV-01 accepted)

Five native x64 CI locks under `requirements/ci-*.lock` preserve exact PyPI wheel hashes. CI creates fresh environments, verifies wheel bytes, installs offline and uses no build isolation for project builds. Independent wheel/sdist acceptance on five platforms; Twine remains on Python 3.12; all matrix versions are audited from the locked 3.12 auditor. OS/browser assets are not locked; no byte-identical build guarantee. The aiohttp public requirement is constrained to <4 due to the documented deprecated API; runtime migration is deferred. Frozen baseline acceptance: #45918602866. See `.github/ci/package_gate.py` and `notes/FINAL-DEVELOPMENT-AUDIT.md`.

## RELEASE-04 — v0.4.0 candidate

The frozen main baseline passed CI #45918602866. Version-only runtime metadata changes and locked packaging/publication contract are prepared for v0.4.0. Candidate acceptance is pending. Publication is manual-only, requires an exact successful main push CI run and separate authorization, refuses duplicate tags/releases, uses locked build dependencies and verifies downloaded release assets. No new runtime behavior is introduced in this phase. Manual-close final capture remains best effort; dedicated GUI close, native restore and external proxy E2E remain unverified. See notes/RELEASE-04.md and notes/releases/v0.4.0.md.
