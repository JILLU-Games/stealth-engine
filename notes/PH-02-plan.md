# PH-02 Plan — identity.py seed persistence

Date: 2026-10-20
Phase: PH-02

## Preconditions and inventory

- `AGENTS.md` was read first; notes are local-only, need a plan before changes, and need a phase log during work. `project/` and `docs/` must be updated with code changes.
- PH-01 is complete: `ProfileConfig.proxy` is optional and `target_ip` is present.
- Notes inventory: `2026-10-19-engine-implementation.md`, `2026-10-19-forensic-audit.md`, `2026-10-19-init-implementation.md`, `2026-10-19-orchestrator-implementation.md`, `2026-10-19-project-memory-setup.md`, `2026-10-19-proxy-implementation.md`, `2026-10-19-session-implementation.md`, `FORENSIC-AUDIT.md`, `MANIFEST.md`, `README.md`, `TEST-BASELINE-AUDIT.md`. No PH-02 plan or log existed.
- `project/` contains `modules/identity.md` and feature records E/S/T; no `project/DEPENDENCIES.md` exists.
- `docs/` contains `FEATURES.md` and `MODULES.md` plus other references; only FEATURES and MODULES are in this phase's documentation scope.
- `stealth_engine/identity.py` currently has `IdentityGenerator.__init__`, `generate`, `fingerprint_hash`, and BrowserForge helper methods; `get_or_create_seeds` and host locale/timezone helpers are absent.
- `pyproject.toml` has six runtime dependencies and does not list tzlocal. The existing `.venv` reports tzlocal absent.

## What changes and why

- Add `os`, `secrets`, and `Path` imports to `stealth_engine/identity.py`.
- Add `_detect_host_locale()` and `_detect_host_timezone()`; tzlocal is imported lazily inside the timezone helper.
- Validate detected locale tags: this Windows host returns `English_United States` from `locale.getlocale()`, which normalizes to `English-United States`, not the documented `xx-XX` form. Reject that result so the specified `en-US` fallback applies.
- Add `IdentityGenerator.get_or_create_seeds()` to load or atomically persist per-profile `seeds.json` with deterministic canvas/audio/fonts values and config → host → fallback locale/timezone values plus source metadata.
- Add only `"tzlocal>=5.0"` to project dependencies, as the owner-authorized Windows IANA timezone detection amendment.
- Preserve `generate()` signature/output and `fingerprint_hash()` behavior.

## Files/modules affected

- `stealth_engine/identity.py` — implementation.
- `pyproject.toml` — add exactly one dependency.
- `project/modules/identity.md` and `project/DEPENDENCIES.md` — document method and dependency.
- `project/MANIFEST.md` — index newly created dependency documentation.
- `project/features/E-deterministic-seed.md`, `project/features/S-seed-reproducibility.md`, `project/features/T-locale-consistency.md` — update actual PH-02 status/behavior.
- `docs/FEATURES.md` and `docs/MODULES.md` — document persisted seeds and tzlocal host-timezone detection.
- `MEMORY.md` — record verified PH-02 and frozen-roadmap status.
- `notes/PH-02-plan.md`, `notes/PH-02-log.md`, and `notes/MANIFEST.md` — private plan/log/index.

## Expected outcome

- Seeds persist at `<config.user_data_dir>/seeds.json`.
- Host timezone detection uses tzlocal, including Windows IANA mapping.
- `generate()` and `fingerprint_hash()` remain unchanged.
- All 5 existing tests continue to pass.

## Rollback

- Planned command from phase instructions: `git checkout -- stealth_engine/identity.py pyproject.toml`.
- This workspace currently has no `.git` directory; that command is not available here.

## Explicit non-goals

- No changes to `config.py`, `engine.py`, `proxy.py`, `session.py`, `orchestrator.py`, `exceptions.py`, `__init__.py`, or `utils/*`.
- No test changes; checks are grouped into PH-05.
- No unrelated feature work or marketing copy.
- No renaming of `pick_healthy()`.
