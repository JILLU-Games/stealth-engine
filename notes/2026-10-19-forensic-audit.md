# Forensic audit and installation fix

Date: 2026-10-19

## Plan and scope

- Audit current package metadata, runtime modules, project contracts, and available diagnostics.
- Confirm the reported editable-install failure from `pyproject.toml` and pip's build-backend traceback.
- Locked code scope: `pyproject.toml` packaging metadata; `config.py` / `proxy.py` credential normalization and redaction plus HTTPS certificate verification; `engine.py` honoring `geoip=False` and rejecting sync close inside a running loop before side effects.
- Add focused regression tests for proxy credentials (including `to_public_dict()`), TLS verification, GeoIP configuration, and close guard ordering. Update `MEMORY.md`, matching `project/` module/feature records, and directly affected `docs/` reference claims.
- Do not change identity generation: browserforge samples through process-global `random.random()` and offers no public per-instance seed hook; current feature E is explicitly marked partially implemented.
- Do not refactor or change unrelated behavior.

## Phase log

- Audit: Python 3.12 and editor diagnostics checked. `get_errors` reports no editor diagnostics. Global Python lacks build/runtime dependencies; a project `.venv` exists.
- Root cause: `pyproject.toml` selects `setuptools.backends.legacy:build`; pip's isolated build reports `ModuleNotFoundError: No module named 'setuptools.backends'`. This is the reported editable-install blocker.
- Confirmed: proxy embedded password leaks through `_build_proxy_url()`, `mask()`, and `ProfileConfig.to_public_dict()`; GeoIP HTTP requests explicitly disable TLS verification; identical seeds across generator instances differ; identity generation mutates process-global random state; `geoip=False` still yields Camoufox `geoip=True`; sync close inside an event loop closes the context before raising and leaves the lock.
- Seed scope decision: not changing browserforge sampling because it consumes process-global randomness and has no supported isolated seed API; preserve as explicit partial limitation.
- Implementation: Corrected setuptools backend and package discovery; centralized and redacted proxy URL credentials including public config serialization; restored TLS verification; honored `geoip=False`; moved sync-close event-loop rejection before side effects. Added focused tests and updated relevant permanent memory/reference docs.
- Verification: Editable install succeeds in `.venv` with `pip install -e <project> --no-deps`; all 5 available unittest tests pass; exact 15-name public API/version and lazy import pass; touched-file editor diagnostics report no errors. Browser launch and external live-proxy checks were not run.
- Remaining findings: browserforge generation mutates process-global `random`, identical seeds do not reproduce whole identities, and the generated BrowserForge dict is not passed into Camoufox's custom fingerprint option. No safe isolated seed or verified conversion was found, so these remain explicit limitations rather than speculative fixes.
