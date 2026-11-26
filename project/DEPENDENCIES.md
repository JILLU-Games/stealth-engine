# Project Dependencies

| Package | Purpose | Status |
|---------|---------|--------|
| camoufox | Camoufox browser runtime | Required |
| playwright | Browser automation API | Required |
| browserforge | Browser fingerprint generation | Required |
| pydantic | Configuration models and validation | Required |
| aiohttp<4 | Async proxy/GeoIP requests | Required |
| loguru | Structured logging | Required |
| tzlocal>=5.0 | Host IANA timezone detection, including Windows registry mapping | Added in PH-02 |
| pyyaml>=6.0 | YAML serialisation for `ProfileConfig.load_yaml`/`save_yaml` (lazy import) | Added in PH-06 |

## FINAL-DEV-01 CI dependency policy

Five native x64 CI locks under `requirements/ci-*.lock` preserve exact PyPI wheel hashes. CI creates fresh environments, verifies wheel bytes, installs offline and uses no build isolation for project builds. Independent wheel/sdist acceptance on five platforms; Twine remains on Python 3.12; all matrix versions are audited from the locked 3.12 auditor. OS/browser assets are not locked; no byte-identical build guarantee. The aiohttp public requirement is constrained to <4 due to the documented deprecated API; runtime migration is deferred. Candidate acceptance pending exact CI.
