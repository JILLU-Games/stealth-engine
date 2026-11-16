# Release Gate — Eight Test Failures and Exact Root-Cause Boundaries

**Repository:** [`ivibtools/stealth-engine`](https://gitlab.com/ivibtools/stealth-engine)  
**Audited immutable GitLab commit:** `e3688ea6cab936b17b65f761fc2049bbeb50cad2` (`main` at audit start)  
**Audit date:** 2026-11-16 UTC  
**Permission / Scope:** read-only source analysis and isolated tests; **only `notes/productions/` audit Markdown may be committed**. No source change, bug fix, dependency installation, browser launch, external proxy, build, tag or release.  
**Provenance:** GitLab tree and source blob hash compared with isolated local checkout; 14 representative source/test/config blobs matched exactly. Line numbers below refer to the immutable SHA; prior P-01–P-05 evidence reports were inspected only as corroboration, never substituted for source.  


## How the result was reproduced

1. **Without replacement dependencies** (no `browserforge`/`camoufox`): `python -m pytest -q -p no:cacheprovider --disable-warnings` returned **exit 2, 11 collection errors**, predominantly at `stealth_engine/identity.py:14` (`from browserforge.fingerprints import FingerprintGenerator`). This result does **not** produce 8 runtime test failures; collection aborts first.
2. **With the same minimal dependency-stub strategy as previous patch-phase audits** (fake import modules; no real browser launch): `PYTHONPATH=<audited-root> python <external-audit-harness>/run_p05_full.py` returned **exit 1: 8 failed, 235 passed, 4 skipped, 32 subtests passed**. Results were freshly reproduced against the SHA-verified source. The harness lives **outside** the repository, creates `browserforge.fingerprints.FingerprintGenerator` that raises a diagnostic error, and exposes a stub `camoufox.async_api`; it must **never** be mistaken for a real-browser runtime.
3. With that same harness, focused `run_p05_tests.py` returned **exit 0, 71 tests OK**. This is controlled offline coverage only.

## Exact failed tests (8 unique failures)

| ID | Test | Direct failure | Classification | Gate |
|---|---|---|---|---|
| T-01 | `tests/test_feature_p_y.py::FeatureY_Tests::test_json_round_trip` | Redacted exported `proxy.server` differs from credential-bearing input | **Confirmed compatibility/test expectation conflict**, not proof of broken redaction | BLOCKED |
| T-02 | `tests/test_feature_p_y.py::FeatureY_Tests::test_yaml_round_trip` | Same original credential equality expectation | **Confirmed compatibility/test expectation conflict** | BLOCKED |
| T-03 | `tests/test_forensic_regressions.py::PH05_VerificationTests::test_check_25_seed_persistence_fingerprint_consistency` | `IdentityError` from stub browserforge generator | **No real provider; production behavior unknown** | UNVERIFIED |
| T-04 | `tests/test_geo.py::AutoSentinelEngineTests::test_auto_locale_uses_proxy_geo_even_when_geoip_false` | Same `IdentityError` from stub browserforge generator | **No real provider; production behavior unknown** | UNVERIFIED |
| T-05 | `tests/test_hardening.py::FingerprintDepthTests::test_screen_bounds_builds_screen_obj` | `ModuleNotFoundError: camoufox.fingerprints` | **Stub lacks Camoufox's Screen module; real dependency not checked** | UNVERIFIED |
| T-06 | `tests/test_meta.py::DriftDetectionTests::test_first_record_no_drift` | Expected history file absent after failed `_record_fingerprint()` | **Provider/setup-sensitive test; source defect not established** | UNVERIFIED |
| T-07 | `tests/test_meta.py::DriftDetectionTests::test_history_capped_at_50` | Prefilled 60 entries stayed 60 because record step returned without writing | **Provider/setup-sensitive test; source defect not established** | UNVERIFIED |
| T-08 | `tests/test_meta.py::DriftDetectionTests::test_tampered_history_reports_drift` | History file absent, `FileNotFoundError` | **Provider/setup-sensitive test; source defect not established** | UNVERIFIED |

## T-01, T-02 — Verified config export behavior/test conflict

**Source:** [`tests/test_feature_p_y.py:L115-L134`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/tests/test_feature_p_y.py#L115-134)

```python
 115 |     def test_json_round_trip(self) -> None:
 116 |         with tempfile.TemporaryDirectory() as d:
 117 |             cfg = self._sample_config()
 118 |             path = Path(d) / "profile.json"
 119 |             cfg.save_json(path)
 120 |             loaded = ProfileConfig.load_json(path)
 121 |             self.assertEqual(loaded, cfg)
 122 |             # Embedded proxy credentials survive the round trip in server.
 123 |             self.assertEqual(
 124 |                 loaded.proxy.server, "http://user:secret@1.2.3.4:8080"
 125 |             )
 126 | 
 127 |     def test_yaml_round_trip(self) -> None:
 128 |         with tempfile.TemporaryDirectory() as d:
 129 |             cfg = self._sample_config()
 130 |             path = Path(d) / "profile.yaml"
 131 |             cfg.save_yaml(path)
 132 |             loaded = ProfileConfig.load_yaml(path)
 133 |             self.assertEqual(loaded, cfg)
 134 |             self.assertEqual(loaded.proxy.server, "http://user:secret@1.2.3.4:8080")
```

**Source:** [`stealth_engine/config.py:L259-L274`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/config.py#L259-274)

```python
 259 |     def _export_data(self, include_secrets: bool) -> dict:
 260 |         """Prepare an export without altering this in-memory configuration.
 261 | 
 262 |         A default export omits proxy authentication and redacts sensitive
 263 |         headers. The loaded default export requires the user to provide
 264 |         secrets again; use include_secrets=True only for private backups.
 265 |         """
 266 |         data = self.model_dump(mode="json")
 267 |         if include_secrets:
 268 |             return data
 269 |         if data["proxy"] is not None:
 270 |             safe_server, _, _ = _split_proxy_credentials(data["proxy"]["server"])
 271 |             data["proxy"]["server"] = safe_server
 272 |             data["proxy"]["username"] = None
 273 |             data["proxy"]["password"] = None
 274 |         for name in list(data.get("extra_headers", {})):
```


**Observed:** `cfg.save_json(path)` and `cfg.save_yaml(path)` omit the embedded proxy user/password by default; the tests assert equality with a credential-bearing original config. Production intent (safe default export) and the tests disagree. `[`stealth_engine/config.py:L313-L349`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/config.py#L313-349)` documents the explicit `include_secrets=True` private-backup contract. This audit did not change tests, defaults, or security policy.

## T-03, T-04, T-05 — Missing real browser dependencies in audit environment

**Source:** [`stealth_engine/identity.py:L181-L190`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/identity.py#L181-190)

```python
 181 |         os_name: str = config.os  # "windows" | "macos" | "linux"
 182 | 
 183 |         try:
 184 |             gen = FingerprintGenerator(os=os_name)
 185 |             raw = gen.generate(os=os_name)
 186 |         except Exception as exc:
 187 |             raise IdentityError(
 188 |                 "browserforge fingerprint generation failed",
 189 |                 details={"stage": "generate", "reason": str(exc)},
 190 |             ) from exc
```

**Source:** [`stealth_engine/engine.py:L801-L810`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L801-810)

```python
 801 |             if cfg.custom_fonts_only:
 802 |                 kwargs["custom_fonts_only"] = True
 803 |         if cfg.screen_bounds is not None:
 804 |             from camoufox.fingerprints import Screen  # lazy import
 805 | 
 806 |             min_w, max_w, min_h, max_h = cfg.screen_bounds
 807 |             kwargs["screen"] = Screen(
 808 |                 min_width=min_w, max_width=max_w,
 809 |                 min_height=min_h, max_height=max_h,
 810 |             )
```


Tests T-03/T-04 enter `IdentityGenerator` and call `BrowserForgeIdentityProvider.build()`; the offline harness is explicitly configured to raise `RuntimeError('stub: browserforge not installed')` instead of generating any fingerprint. T-05 reaches lazy `from camoufox.fingerprints import Screen`; the harness does not provide that module. These are **definite failures in this environment**, not independently established bugs in the installed real dependencies. Exact test references: [`tests/test_forensic_regressions.py:L334-L415`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/tests/test_forensic_regressions.py#L334-415), [`tests/test_geo.py:L375-L396`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/tests/test_geo.py#L375-396), [`tests/test_hardening.py:L334-L354`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/tests/test_hardening.py#L334-354).

## T-06, T-07, T-08 — Why the history tests currently fail

**Source:** [`tests/test_meta.py:L44-L81`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/tests/test_meta.py#L44-81)

```python
  44 | class DriftDetectionTests(unittest.TestCase):
  45 |     def _engine(self, **kw):
  46 |         return StealthEngine(_cfg(**kw))
  47 | 
  48 |     def test_first_record_no_drift(self):
  49 |         engine = self._engine()
  50 |         drifted = engine._record_fingerprint()
  51 |         self.assertFalse(drifted)
  52 |         hist_path = Path(engine._session.profile_dir) / "fingerprint_history.json"
  53 |         self.assertTrue(hist_path.exists())
  54 |         data = json.loads(hist_path.read_text())
  55 |         self.assertEqual(len(data), 1)
  56 |         self.assertEqual(data[0]["hash"], engine._identity.fingerprint_hash())
  57 | 
  58 |     def test_same_hash_no_drift_second_time(self):
  59 |         engine = self._engine()
  60 |         engine._record_fingerprint()
  61 |         drifted = engine._record_fingerprint()
  62 |         self.assertFalse(drifted)
  63 | 
  64 |     def test_tampered_history_reports_drift(self):
  65 |         engine = self._engine()
  66 |         engine._record_fingerprint()
  67 |         hist_path = Path(engine._session.profile_dir) / "fingerprint_history.json"
  68 |         data = json.loads(hist_path.read_text())
  69 |         data[-1]["hash"] = "0" * 64  # pretend previous launch differed
  70 |         hist_path.write_text(json.dumps(data))
  71 |         drifted = engine._record_fingerprint()
  72 |         self.assertTrue(drifted)
  73 | 
  74 |     def test_history_capped_at_50(self):
  75 |         engine = self._engine()
  76 |         hist_path = Path(engine._session.profile_dir) / "fingerprint_history.json"
  77 |         hist_path.parent.mkdir(parents=True, exist_ok=True)
  78 |         hist_path.write_text(json.dumps([{"hash": "x"}] * 60))
  79 |         engine._record_fingerprint()
  80 |         data = json.loads(hist_path.read_text())
  81 |         self.assertEqual(len(data), 50)
```

**Source:** [`stealth_engine/engine.py:L507-L520`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L507-520)

```python
 507 |         try:
 508 |             import json as _json
 509 |             import math as _math
 510 |             import os as _os
 511 |             import time as _time
 512 |             from pathlib import Path
 513 | 
 514 |             fp_hash = self._identity.fingerprint_hash()
 515 |             path = Path(self._session.profile_dir) / self._FP_HISTORY_FILE
 516 |             meta_path = path.with_name(self._FP_HISTORY_META_FILE)
 517 |             history: list[dict[str, Any]] = []
 518 |             if path.exists():
 519 |                 history = _json.loads(path.read_text(encoding="utf-8"))
 520 |                 if not isinstance(history, list) or any(not isinstance(h, dict) for h in history):
```

**Source:** [`stealth_engine/engine.py:L552-L568`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/engine.py#L552-568)

```python
 552 |             drifted = bool(history) and history[-1].get("hash") != fp_hash
 553 |             if drifted and not self._config.fingerprint_diversity:
 554 |                 _log.warning("fingerprint drift detected across launches",
 555 |                              profile=self._config.profile_name,
 556 |                              previous=str(history[-1].get("hash", ""))[:12],
 557 |                              current=fp_hash[:12])
 558 |             history.append({"ts": now, "hash": fp_hash,
 559 |                             "diversity": self._config.fingerprint_diversity})
 560 |             history = history[-self._FP_HISTORY_MAX:]
 561 |             path.parent.mkdir(parents=True, exist_ok=True)
 562 |             tmp = path.with_suffix(".json.tmp")
 563 |             tmp.write_text(_json.dumps(history, indent=2), encoding="utf-8")
 564 |             _os.replace(tmp, path)
 565 |             return drifted
 566 |         except Exception as exc:
 567 |             _log.warning("fingerprint history write failed", reason=str(exc))
 568 |             return False
```

**Source:** [`stealth_engine/identity.py:L462-L482`](https://gitlab.com/ivibtools/stealth-engine/-/blob/e3688ea6cab936b17b65f761fc2049bbeb50cad2/stealth_engine/identity.py#L462-482)

```python
 462 |     def fingerprint_hash(self) -> str:
 463 |         """Return a stable SHA-256 hex digest of the generated fingerprint.
 464 | 
 465 |         If :meth:`generate` has not yet been called, it is invoked once
 466 |         and the result is cached on the instance.  The hash is derived
 467 |         from a deterministic JSON serialisation (sorted keys) so the same
 468 |         fingerprint always produces the same digest.
 469 | 
 470 |         Returns:
 471 |             64-character lowercase hex string.
 472 | 
 473 |         Raises:
 474 |             IdentityError: Propagated from :meth:`generate` on failure.
 475 |         """
 476 |         if self._cached_hash is not None:
 477 |             return self._cached_hash
 478 | 
 479 |         fp = self.generate()
 480 |         serialised = json.dumps(fp, sort_keys=True, ensure_ascii=True)
 481 |         self._cached_hash = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
 482 |         return self._cached_hash
```


- Each `test_meta.py` case calls `_record_fingerprint()` without first supplying a working identity fingerprint provider/generator. That method calls `self._identity.fingerprint_hash()` **before writing any history**.
- `fingerprint_hash()` calls `generate()` if no cached fingerprint exists, which enters the unavailable/stubbed browserforge provider. The exception is caught by `_record_fingerprint`, which warns and returns `False`; the test's file/diff assertions therefore fail. This is verified source control flow, not speculation about filesystem state.
- **Independent control probe (no source edit):** with `engine._identity.fingerprint_hash` replaced by a deterministic 64-character test digest in a temporary profile: first record created the history file and metadata, **61 writes left 50 recent history entries**, and changing the last stored hash caused `drifted=True` on the next call. This control demonstrates that a provider-ready persistence path can work; it does not certify production or prove that all legacy metadata cases are correct.

## Tests outside the failure count

- `4 skipped` are separate from `8 failed` and must not be promoted to passing.
- The 11 no-stub collection errors are **not an additional count of proven bugs**; they represent the clean-environment dependency blocker.
- The 71 focused passes are controlled fake-browser/proxy tests and **do not negate** the full-suite failures.

## Exit classification

**Release gate is failed/blocked.** T-01/T-02 require an explicit documented compatibility/test acceptance decision, not a silent return to plaintext passwords. T-03–T-08 require a real dependency/test-fixture environment before the actual engine behavior can be responsibly classified. This is an audit finding, not implementation approval or a proposed patch.
