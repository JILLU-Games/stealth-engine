# RELEASE-04 — v0.4.0 Core Preview prerelease preparation

## Approved pre-change scope
Baseline GitHub main 3bfdbcb74d1ad8447273938bdaf6a3bed1df6188, tree 0c0cab836b053104a32aa1e031d89db52fa36c5e; GitLab main f78977d2d2ac6c3f26d85e71df0b67016cb07853. Core CI #45918602866 completed SUCCESS. Main protection disabled. Pre-change plan recorded in tree 7c40e2986e239ca77dda3cf9779c48458e148c86.
Exact paths (16): pyproject.toml; stealth_engine/__init__.py (version only); CHANGELOG.md; README.md; MEMORY.md; .github/ci/package_gate.py (version only); .github/ci/core_release.py (release contract/metadata/integrity); .github/workflows/production-validation.yml (release contract label only); new .github/workflows/release-v040.yml; new tests/test_release_04_contract.py; docs/MODULES.md; project/modules/engine.md; project/features/I-installable.md; new notes/releases/v0.4.0.md; this note; notes/MANIFEST.md.
All other paths read-only. Preserve historical publisher and v0.3.0 tag/release, MIT, runtime behavior, dependencies and existing assertions. GitHub Actions only. No publication dispatch, tag, release, PyPI, deployment, personal PC or VPS. Approved S01–S05 only; S06–S07 separate approval.

## Implementation ledger
- S01: exact parent, GitLab baseline and successful main CI verified.
- S02: version metadata, current documentation and explicit prerelease limitations synchronized.
- S03: separate manual-only publisher, confirmation and exact same-repo main push CI evidence; job-set and aggregate verification, authenticated duplicate rejection, existing hash-locked build/clean install, provenance, draft upload and independent remote byte verification. Historical publisher unchanged. Nine offline release contract tests. Python 3.10 can import the helper for pure tests; metadata validation uses Python 3.12 tomllib.
- S04: one candidate commit and PR CI pending; preserve all old regression assertions and gates. S05: conditional merge/main CI pending. Terminal evidence in PR; no second source commit for notes.
- Known limits: dedicated GUI close/native restore E2E, external proxy, deprecated API, disabled main protection, historical CI archive bytes unverified; no signed attestation/byte-identical build claim. New manual workflow execution and remote publication are NOT RUN in preparation.
