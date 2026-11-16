# PH-06 Plan — Feature P (pluggable identity) + Feature Y (YAML/JSON import-export)

Date: 2026-11-15
Owner-approved scope: implement remaining unimplemented A–Z features P and Y.
These are OUTSIDE the frozen 5-step roadmap; owner explicitly approved.

## Preconditions

- Forensic audit `notes/2026-11-15-forensic-audit-resume.md` confirmed P and Y
  have zero implementation in `stealth_engine/`.
- `pyyaml 6.0.3` already present in `.venv` (transitive); must be declared in
  `pyproject.toml` since config.py will import it directly.
- Frozen non-goals still apply: no BrowserForge→Camoufox fingerprint wiring,
  no global random.seed, no public API breakage (additive only).

## What changes and why

### Feature Y — `stealth_engine/config.py`

Add file IO to `ProfileConfig` (Pydantic v2 native for JSON; PyYAML safe_load/
safe_dump for YAML):

- `save_json(path)`, `load_json(path)` classmethod
- `save_yaml(path)`, `load_yaml(path)` classmethod
- Accept `str | Path`; serialise via `model_dump(mode="json")`;
  validate on load via `cls.model_validate(...)` / `model_validate_json`.
- `import yaml` lazily inside YAML methods (mirrors tzlocal lazy-import
  convention in identity.py).

### Feature P — `stealth_engine/identity.py`, `engine.py`, `orchestrator.py`, `__init__.py`

- New `IdentityProvider` `typing.Protocol`: `build(config, rng) -> dict`
  returning the complete fingerprint dict (same shape as `generate()` output,
  pre config-override/validation).
- New `BrowserForgeIdentityProvider` — default implementation; absorbs the
  current `FingerprintGenerator` call, `_extract`, and `_derive_timezone`
  (moved off `IdentityGenerator`, behaviour identical).
- `IdentityGenerator(config, provider=None)` — optional provider, defaults to
  `BrowserForgeIdentityProvider()`. `_build_fingerprint` delegates raw
  generation to provider, then applies `config.locale`/`config.timezone`
  overrides and `_validate` unchanged. `generate()`/`fingerprint_hash()`
  signatures and caching unchanged.
- `StealthEngine(config, *, identity_provider=None)` — optional kwarg passed
  to `IdentityGenerator`. Backward compatible.
- `BulkRunner(..., identity_provider=None)` — optional kwarg forwarded to each
  `StealthEngine(profile, ...)` so bulk runs can share a custom provider.
- `__init__.py`: lazy-map + `__all__` += `IdentityProvider`,
  `BrowserForgeIdentityProvider` (15 → 17 names, additive only).

### `pyproject.toml`

- Add `"pyyaml>=6.0"` to dependencies.

## Files affected

- `stealth_engine/config.py` — add 4 methods
- `stealth_engine/identity.py` — provider protocol + default provider,
  refactor `_build_fingerprint`
- `stealth_engine/engine.py` — `identity_provider` kwarg
- `stealth_engine/orchestrator.py` — `identity_provider` kwarg forwarded
- `stealth_engine/__init__.py` — 2 new lazy exports
- `pyproject.toml` — +1 dependency
- `tests/test_feature_p_y.py` — new focused tests
- `project/modules/{config,identity,engine,orchestrator}.md`,
  `project/features/{P,Y,J}.md`, `project/MANIFEST.md`,
  `project/DEPENDENCIES.md`
- `docs/MODULES.md`, `docs/FEATURES.md`, `docs/MANIFEST.md` (status col)
- `MEMORY.md`, `CHANGELOG.md`
- `notes/PH-06-plan.md`, `notes/PH-06-log.md`, `notes/MANIFEST.md`

## Expected outcome

- `ProfileConfig` round-trips through `.json` and `.yaml` files losslessly.
- Custom identity providers plug in via `StealthEngine(config,
  identity_provider=...)` / `BulkRunner(..., identity_provider=...)`.
- Default behaviour (browserforge) byte-identical; all 9 existing tests pass.
- Public API grows additively to 17 names.

## Explicit non-goals

- No change to `generate()`/`fingerprint_hash()` signatures or output shape.
- No provider registry / entry-points machinery (keep it a simple Protocol).
- No change to frozen roadmap steps or `docs/ROADMAP-v2-FREEZE.md`.
- No YAML aliases/anchors support beyond `yaml.safe_load`.
- BulkRunner provider is a single shared instance across profiles (documented).
