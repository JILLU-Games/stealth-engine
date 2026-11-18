# Current Project Baseline Freeze

**Audit date:** 2026-11-18
**Repository:** `JILLU-Games/stealth-engine` (GitHub)
**Package:** `stealth_engine` 0.3.0, Core Preview prerelease
**Purpose:** Freeze the exact project state from which future production-readiness work must resume. This is a baseline record, not a code-change authorization.

## Immutable Starting Point

| Item                       | Frozen value                               |
| -------------------------- | ------------------------------------------ |
| Local branch               | `main`                                     |
| Local HEAD / `origin/main` | `58c87e2b4de27e5a0510b628a623fcf6f1a1a96b` |
| Published tag              | `v0.3.0`                                   |
| Tag/source commit          | `b695b2c6eee3c207132c6a58e2ea8993a50ad921` |
| Start-of-audit worktree    | Clean; local `main` matched `origin/main`  |
| Public package API         | 29 names in `stealth_engine.__all__`       |

The current `main` commit is a post-release documentation update. Comparing the release tag with `main` showed only `README.md` and the three release-evidence/index Markdown files changed; `stealth_engine/`, `tests/`, `pyproject.toml`, and `.github/` had no delta. Do not treat the tag SHA and current main SHA as interchangeable: use the tag for the published artifact and the frozen main SHA for this planning snapshot.

## Release Evidence Boundary

- GitHub v0.3.0 is a published **prerelease**, not a full external-proxy GA. The release API confirms the tag and release; [publication evidence](18-CORE-RELEASE-PUBLICATION-EVIDENCE.md) records seven verified assets and successful release-trigger CI/publisher runs.
- [Core acceptance evidence](16-CORE-PRODUCTION-ACCEPTANCE.md) records GitHub Actions Run #8 on source `e94b4f613d856ff62bb7c2699e29ecdfc9694955`: Ubuntu Python 3.10–3.13 each 245 passed / 4 expected skips; Windows 2022 Python 3.12 244 passed / 5 expected skips; real Camoufox 9/9 on each OS; direct-host 1/1; controlled local HTTP proxy 2/2; packaging, filesystem, and dependency-audit gates passed.
- Run #8 is not the release-tag commit. The separate release-triggering CI recorded in [publication evidence](18-CORE-RELEASE-PUBLICATION-EVIDENCE.md) passed for the release source. Do not transfer Run #8's exact test counts to the release tag without its own artifact report.
- External third-party proxy authentication/egress, remote DNS, and proxy-specific WebRTC leakage remain explicitly **UNVERIFIED**. No anti-detection guarantee or arbitrary-host certification is established.

## Local Verification Snapshot

- Initial environment: Windows system Python 3.12.0. `python -m compileall -q stealth_engine tests examples` passed; initial system-interpreter `python -m pytest -q` stopped during collection because `aiohttp` and `browserforge` were absent.
- PR-01 subsequently created an ignored `.venv/` and installed the editable project plus pytest; exact result is recorded below. No source, tests, build config, workflows, runtime profiles, release/tag, or Git history were changed.

## PR-01 Recheck (2026-11-18; after the frozen commit)

- Environment: Windows, Python 3.12.0 in ignored `.venv/`; package/test dependencies installed from project metadata without modifying `pyproject.toml` or creating a lockfile.
- Versions: `stealth_engine 0.3.0`, pytest `9.2.0`, Camoufox `0.5.9`, Playwright `1.62.0`, BrowserForge `1.2.4`, aiohttp `3.14.5`, Pydantic `2.14.3`, Loguru `0.8.0`, tzlocal `5.4.5`, PyYAML `6.0.3`.
- `python -m pip check`: passed, no broken requirements. `python -m compileall -q stealth_engine tests examples`: passed.
- `python -m pytest -q -rs`: **245 passed, 5 skipped, 4 warnings, 32 subtests passed; exit 0**. Skips: one POSIX-only permissions test, two `STEALTH_SMOKE` tests, and two `STEALTH_CANARY` tests. The browser/canary flags were not enabled; no browser binary was fetched or launched.
- Four `DeprecationWarning`s came from `aiohttp.BasicAuth` at `stealth_engine/proxy.py:718`; aiohttp 3.14.5 reports this API as deprecated for aiohttp 4.0. Tests still pass; no code change is included in PR-01.
- No external proxy/network acceptance or profile mutation was performed.

## Product Surface

This repository is a Python library, not a GUI/admin application. The source package contains configuration, identity generation, Camoufox/Playwright session handling, GeoIP/proxy helpers, orchestration, behavior helpers, risk scoring, and typed exceptions. Its 26 A–Z labels are a feature catalog, not proof that every capability is fully wired or live-certified; see [the current A–Z ledger](24-ACTUAL-WORKING-LEDGER.md).

## Repository-Note Integrity Finding

The checked-in guidance says `notes/` is local-only, but 89 note files were tracked at baseline and `.gitignore` did not exclude `notes/`. `notes/MANIFEST.md` had 34 entries, 56 existing files not indexed, and one entry for a missing file. This policy/index mismatch is documented for an owner decision; this baseline task does not untrack notes or change `.gitignore`.

## Freeze Rules

1. Keep this starting SHA immutable. Any later source work records a new pre-change SHA and a separate phase entry.
2. Keep historical audit files and release evidence intact; add dated/current overlays instead of rewriting evidence as though it happened on this baseline.
3. Planning documents do not start an implementation phase and do not count as a production acceptance pass.
4. No change to frozen `docs/ROADMAP-v2-FREEZE.md`, published release/tag, dependencies, public API, or product source without explicit owner approval and a phase-specific Scope Lock.
5. Test, platform, browser, and network outcomes must be recorded with exact environment and evidence. `NOT RUN` is never `PASS`.
