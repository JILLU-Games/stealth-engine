# TEST BASELINE AUDIT — stealth_engine

## 0. Metadata

- Audit date: 2026-10-19
- Files scanned: 168 source/evidence files in the requested groups: `stealth_engine/**/*.py` (10), `tests/**/*.py` (3), `notes/**/*.md` (10), `docs/**/*.md` (8), root `README.md` / `MEMORY.md` / `CHANGELOG.md` (3), `project/**/*.md` (36), `.github/**/*.md` (1), and JSON/TXT/YAML/YML files recursively (98). Counts are source-group counts; test and Markdown/structured-text extensions do not overlap.
- Sources consulted: all 13 Python files under `stealth_engine/` and `tests/`; all Markdown in `notes/`, `docs/`, `project/`, `.github/`, and the three named root files; all 98 `.json`, `.txt`, `.yaml`, `.yml` files, including `.venv` data. `notes/FORENSIC-AUDIT.md` was searched only as a hint; every claim relevant to test count and coverage was independently verified against the test source and runtime output.
- Runtime command used: `py -B -m unittest discover -s tests -v` from `BrowserRuntime/` after activating `.venv`. An unactivated `py` invocation failed to import `browserforge`; the activated-environment run below is the passing discovery result.

## 1. Executive Summary

- Actual test count (from unittest discovery): 5 tests run, 5 passed, using the activated project `.venv`.
- Actual test method count: 5 methods in `tests/test_forensic_regressions.py`; `tests/test_placeholder.py` and `tests/__init__.py` declare no test methods.
- Whether a documented 22-check list exists: NO. Search found references to a 22-check count, but no enumerated checks 1–22.
- Number of the 22 checks that are formally covered today: UNVERIFIED — there is no concrete 22-check list to map to tests.
- Number of the 22 checks that are NOT covered: UNVERIFIED — there is no concrete 22-check list to map to tests.
- Number of checks 23–26 that are absent: 3 absent (#23, #25, #26); #24 has partial/behavioral coverage but does not assert the named `geo.locale` expression directly.
- Number of new tests required before Step 5 is safe: UNVERIFIED for a full 22+4 baseline. At least 3 of checks 23–26 have no current test coverage; #24 is partially covered.
- Verdict: BASELINE UNKNOWN (no 22-check list exists)

## 2. Actual Tests Present

| File                                 | Line range | Test method name                                           | What it asserts (≤2 lines)                                                                                                                       |
| ------------------------------------ | ---------: | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `tests/test_forensic_regressions.py` |      23–44 | `test_embedded_credentials_are_separated_and_redacted`     | Proxy URLs omit embedded credentials in generated request/browser values; auth is separated; masking and `to_public_dict()` redact the password. |
| `tests/test_forensic_regressions.py` |      46–64 | `test_proxy_logs_do_not_include_embedded_password`         | Captured health-check and proxy-pick logs do not contain the embedded password.                                                                  |
| `tests/test_forensic_regressions.py` |      66–93 | `test_geo_request_keeps_tls_verification_enabled`          | Mocked `resolve_geo()` request uses TLS verification by default (`ssl` absent or true).                                                          |
| `tests/test_forensic_regressions.py` |     95–157 | `test_geoip_setting_controls_launch_and_overrides`         | With mocked proxy/GeoIP, launch kwargs reflect the `geoip` flag and choose the expected locale for each flag value.                              |
| `tests/test_forensic_regressions.py` |    159–188 | `test_sync_close_rejects_running_loop_before_side_effects` | Sync `close()` in a running event loop raises before state save/context close and leaves the lock present.                                       |
| `tests/test_placeholder.py`          |          1 | No test method                                             | The file contains only a placeholder comment.                                                                                                    |
| `tests/__init__.py`                  |          1 | No test method                                             | The file contains only a module docstring.                                                                                                       |

## 3. Runtime Discovery Output

Command (default launcher, unactivated): `py -B -m unittest discover -s tests -v`

Exact output:

```text
test_forensic_regressions (unittest.loader._FailedTest.test_forensic_regressions) ... ERROR

======================================================================
ERROR: test_forensic_regressions (unittest.loader._FailedTest.test_forensic_regressions)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_forensic_regressions
Traceback (most recent call last):
  File "C:\Python312\Lib\unittest\loader.py", line 382, in _find_test_path
    module = self._get_module_from_name(name)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python312\Lib\unittest\loader.py", line 325, in _get_module_from_name
    __import__(name)
  File "C:\Users\Administrator\Desktop\Projects\Engine\BrowserRuntime\tests\test_forensic_regressions.py", line 16, in <module>
    from stealth_engine.engine import BrowserSession, StealthEngine
  File "C:\Users\Administrator\Desktop\Projects\Engine\BrowserRuntime\stealth_engine\engine.py", line 14, in <module>
    from .identity import IdentityGenerator
  File "C:\Users\Administrator\Desktop\Projects\Engine\BrowserRuntime\stealth_engine\identity.py", line 11, in <module>
    from browserforge.fingerprints import FingerprintGenerator
ModuleNotFoundError: No module named 'browserforge'

----------------------------------------------------------------------
Ran 1 test in 0.001s

FAILED (errors=1)
```

Command (activated project venv): `py -B -m unittest discover -s tests -v`

Exact output:

```text
test_geoip_setting_controls_launch_and_overrides (test_forensic_regressions.EngineRegressionTests.test_geoip_setting_controls_launch_and_overrides) ... 2026-10-19 22:40:38.236 | DEBUG    | stealth_engine.session:_try_acquire_lock:237 - lock acquired
2026-10-19 22:40:38.237 | INFO     | stealth_engine.engine:alaunch:189 - stealth session launched
2026-10-19 22:40:38.239 | DEBUG    | stealth_engine.session:export_state:370 - storage state exported
2026-10-19 22:40:38.240 | DEBUG    | stealth_engine.session:release_lock:288 - lock released
2026-10-19 22:40:38.241 | INFO     | stealth_engine.engine:aclose:547 - session closed
2026-10-19 22:40:38.246 | DEBUG    | stealth_engine.session:_try_acquire_lock:237 - lock acquired
2026-10-19 22:40:38.247 | INFO     | stealth_engine.engine:alaunch:189 - stealth session launched
2026-10-19 22:40:38.248 | DEBUG    | stealth_engine.session:export_state:370 - storage state exported
2026-10-19 22:40:38.250 | DEBUG    | stealth_engine.session:release_lock:288 - lock released
2026-10-19 22:40:38.254 | INFO     | stealth_engine.engine:aclose:547 - session closed
Executing <Task finished name='Task-2' coro=<EngineRegressionTests.test_geoip_setting_controls_launch_and_overrides() done, defined at C:\Users\Administrator\Desktop\Projects\Engine\BrowserRuntime\tests\test_forensic_regressions.py:95> result=None created at C:\Python312\Lib\asyncio\runners.py:100> took 1.265 seconds
ok
test_sync_close_rejects_running_loop_before_side_effects (test_forensic_regressions.EngineRegressionTests.test_sync_close_rejects_running_loop_before_side_effects) ... 2026-10-19 22:40:38.281 | DEBUG    | stealth_engine.session:_try_acquire_lock:237 - lock acquired
2026-10-19 22:40:38.290 | DEBUG    | stealth_engine.session:release_lock:288 - lock released
ok
test_embedded_credentials_are_separated_and_redacted (test_forensic_regressions.ProxyCredentialTests.test_embedded_credentials_are_separated_and_redacted) ... C:\Users\Administrator\Desktop\Projects\Engine\BrowserRuntime\stealth_engine\proxy.py:407: DeprecationWarning: BasicAuth is deprecated and will be removed in aiohttp 4.0; use aiohttp.encode_basic_auth() with headers={'Authorization': ...} instead
  return aiohttp.BasicAuth(username, password)
ok
test_geo_request_keeps_tls_verification_enabled (test_forensic_regressions.ProxyCredentialTests.test_geo_request_keeps_tls_verification_enabled) ... ok
test_proxy_logs_do_not_include_embedded_password (test_forensic_regressions.ProxyCredentialTests.test_proxy_logs_do_not_include_embedded_password) ... 2026-10-19 22:40:38.340 | DEBUG    | stealth_engine.proxy:health_check:256 - proxy health_check
2026-10-19 22:40:38.345 | INFO     | stealth_engine.proxy:pick_healthy:289 - picked healthy proxy
ok

----------------------------------------------------------------------
Ran 5 tests in 1.364s

OK
```

Total tests run (activated venv): 5. PASS: 5, FAIL: 0. The default, unactivated launcher run failed at import collection before the test methods executed.

## 4. Search for "22" and "F6-Final" references

| Source file                              | Line | Snippet (≤100 chars)                                           | Interpretation                                                                          |
| ---------------------------------------- | ---: | -------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `docs/ROADMAP-v2-FREEZE.md`              |  138 | `Step 5 — Verification (F6-Final extended to 26 checks)`       | Step label/count reference; no checks 1–22 listed.                                      |
| `docs/ROADMAP-v2-FREEZE.md`              |  140 | `All 22 existing checks must still PASS.`                      | Count-only statement; no itemized baseline.                                             |
| `docs/ROADMAP-v2-FREEZE.md`              |  218 | `## 8. Freeze Checklist`                                       | Generic checklist heading, not the 22 baseline.                                         |
| `docs/ROADMAP-v2-FREEZE.md`              |  224 | `[ ] Step 5: F6-Final — 26 checks, REGRESSION-FREE`            | Step label/count reference; no checks 1–22 listed.                                      |
| `notes/FORENSIC-AUDIT.md`                |   86 | `...storage_state_path(self) -> str`, 131–138, ...`            | Incidental `22` substring inside line number `122`; prior audit note, not ground truth. |
| `notes/FORENSIC-AUDIT.md`                |  164 | `122:        fp = self.generate()`                             | Source-line citation contains `22`; not a checklist.                                    |
| `notes/FORENSIC-AUDIT.md`                |  174 | `...identity.py:122`. Constructors occur...`                   | Source-line citation contains `22`; not a checklist.                                    |
| `notes/FORENSIC-AUDIT.md`                |  249 | `- Check 23 is absent: ...`                                    | Prior note mentions a new check; independently compared with test source.               |
| `notes/FORENSIC-AUDIT.md`                |  250 | `- Check 24 is partially covered...`                           | Prior note mentions a new check; independently compared with test source.               |
| `notes/FORENSIC-AUDIT.md`                |  251 | `- Check 25 is absent: ...`                                    | Prior note mentions a new check; independently compared with test source.               |
| `notes/FORENSIC-AUDIT.md`                |  252 | `- Check 26 is absent: ...`                                    | Prior note mentions a new check; independently compared with test source.               |
| `notes/FORENSIC-AUDIT.md`                |  253 | `...not 22 separate check methods.`                            | Prior note claim; test source independently contains five methods.                      |
| `notes/FORENSIC-AUDIT.md`                |  255 | `The inline requirement that 22 previous checks remain...`     | Prior note claim; independently verified as a count-only roadmap statement.             |
| `notes/FORENSIC-AUDIT.md`                |  311 | `UNVERIFIED — whether the named 22-check F6-Final baseline...` | Prior note flags uncertainty; treated only as a search hint.                            |
| `README.md`, `MEMORY.md`, `CHANGELOG.md` |    — | —                                                              | Zero hits for the requested terms.                                                      |
| `project/**/*.md`, `.github/**/*.md`     |    — | —                                                              | Zero hits for the requested terms.                                                      |

Search performed across 10 `notes/**/*.md`, 8 `docs/**/*.md`, 3 root Markdown files, 36 `project/**/*.md`, and 1 `.github/**/*.md`. The prior forensic note was not accepted as ground truth.

## 5. Reconstructed 22-Check List

NO LIST EXISTS in the scanned project sources. `docs/ROADMAP-v2-FREEZE.md:138–140` contains a `F6-Final` label and the statement “All 22 existing checks must still PASS,” but provides no numbered checks 1–22. Lines 218 and 224 provide only a freeze checklist and a 26-check step label. The five source test methods and their runtime discovery output are independently enumerated in Sections 2 and 3; package/test Python search found no 22/F6/numbered-check inventory. The prior audit note at `notes/FORENSIC-AUDIT.md:255,311` was treated as a hint only.

Evidence searches:

- Markdown search command: `Select-String -SimpleMatch -Pattern '22','twenty-two','F6','F6-Final','checklist','check 23','check 24','check 25','check 26'` over notes, docs, root Markdown, project Markdown, and `.github` Markdown. Result: the count/step references tabulated in Section 4; no list of checks 1–22. Root, project, and `.github` groups had zero hits.
- Python search command: `Select-String -Pattern '\b22\b|twenty-two|F6-Final|\bF6\b|checklist|\bcheck\s+(?:[1-9]|[12][0-9]|30)\b'` over `stealth_engine/**/*.py` and `tests/**/*.py`. Output: `ZERO CHECKLIST/22/F6 HITS IN PACKAGE AND TEST PYTHON`.
- Structured-file search: 98 `.json`, `.txt`, `.yaml`, `.yml` files searched for `F6-Final|twenty-two|22 existing checks|checklist|check 23|check 24|check 25|check 26|check [1-9]`. Output: `ZERO CHECKLIST MARKER HITS`. A broader raw `22` search returned numeric IDs/dates in installed `.venv` datasets, not a check inventory.

## 6. Coverage Matrix

SKIPPED — check list unknown.

## 7. Gap Analysis

- Missing checks: the 22 baseline checks cannot be enumerated or counted as covered/missing because no concrete list was found.
- Checks 23–26: #23 has no no-proxy seeded-locale assertion; #25 has no cross-launch seed persistence/hash assertion; #26 has no no-proxy launch test. #24 has behavioral coverage in `test_geoip_setting_controls_launch_and_overrides` (lines 95–157), but its expected locale is compared to a literal rather than directly to `geo.locale`.
- Orphan tests relative to the unknown 22-check list: UNVERIFIED. The five test methods’ assertions are enumerated in Section 2, but the baseline list needed to map them does not exist in the scanned sources.
- Estimated new tests required before Step 5: UNVERIFIED for the full 22+4 baseline. At least 3 of the four explicitly numbered new checks are uncovered; #24 is partial. A total for the missing 22 checks cannot be calculated.

## 8. Step 5 Impact

- Can Step 5 proceed as originally scoped? NO.
- Evidence: the requirement to retain/pass 22 baseline checks has no enumerated check list in the searched sources; default `py` discovery also depends on interpreter environment, while the activated project venv runs five tests. Coverage against 22 unknown checks cannot be established from the current baseline.
- Step 5 scope status: the “all 22 existing checks” baseline and its coverage count are unverified; checks 23–26 have the coverage status listed in Section 7.

## 9. Unverified Items

- Whether the 22 checks were ad-hoc terminal commands, uncommitted tests, or an estimate: UNVERIFIED; no concrete list or artifact was found in the specified project sources.
- Whether the five existing test methods map to any entries in an external 22-check list: UNVERIFIED; the list is unavailable in scanned sources.
- The unactivated `py` interpreter lacks `browserforge`; the passing discovery result is from the activated project `.venv`.

## 10. Attestation

I did not modify any existing .py, .toml, .json, or .md file. I ran no state-mutating commands. Files written: notes/TEST-BASELINE-AUDIT.md only.
