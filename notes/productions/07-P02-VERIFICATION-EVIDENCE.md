# P-02 — Verified Patch Evidence (Source Proof + Focused Test Results)

**Status:** `PATCH APPLIED / LINUX OFFLINE 35/35 PASS; WINDOWS + REAL BROWSER NOT VERIFIED`  
**Date:** 2026-11-16 (UTC)  
**Immutable project baseline:** `a6c1260d01c22e2233eb698685f5f7f1d7c8e0c5`  
**Pre-P02 HEAD:** `c1c838252052ba09be9863d5e6241ff8d3fcb1a2`  
**P02 logic commit:** [`cb06b63b10130e99c28747a95837ab901ae42dfc`](https://gitlab.com/ivibtools/stealth-engine/-/commit/cb06b63b10130e99c28747a95837ab901ae42dfc)  
**Final code commit / formatting correction:** [`e4c60c11c62d4fcef0f8892ae484014f4324659f`](https://gitlab.com/ivibtools/stealth-engine/-/commit/e4c60c11c62d4fcef0f8892ae484014f4324659f)  
**Scope:** Only F-07, F-08, F-09, F-18; allowed `SessionManager` lock/reset code, `StealthEngine._record_fingerprint`, `BrowserSession.session_age_days` and `tests/test_forensic_regressions.py`.

## Baseline and final hashes

| File | Pre-P02 Git blob | Post-P02 Git blob | Allowed change |
|---|---|---|---|
| `stealth_engine/session.py` | `fe06fe08196d9dbc2cb84a60a8f44b687dcbf629` | `c0124af602e38a560f458afb9c48f91c86f13d44` | `_pid_alive`, session lock owner fields, guard/lock/release/reset |
| `stealth_engine/engine.py` | `6b78d90259ebf71fde65c3d8dd0c5f6811837dae` | `8059a36fe89ed89799880b06e66adf08303b9393` | `_record_fingerprint`, `session_age_days` only |
| `tests/test_forensic_regressions.py` | `1305b5bfdc2dac88a1a663db3f114a307a23de55` | `0200bde5cfcd7bad0bcb88177bd6a606190ccd8b` | Append P02 test cases only |

**Line-ending correction:** The initial P-02 GitLab patch (`cb06b63b`) inadvertently converted CRLF→LF in `engine.py` and tests, inflating per-commit diff statistics. `e4c60c11` restored original CRLF; combined final post-P02 function-level AST review found no P-01 launch/close or unrelated source method change. `session.py` retained LF. No git force-push/rewrite was used.

## Exact source proof — current GitLab final SHA

### F-07 — age does not preempt a live owner

**[stealth_engine/session.py:289-334](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L289-334)**

```python
 289 |     def acquire_lock(self) -> None:
 290 |         """Acquire an atomic, instance-owned PID lock; never steal a live PID.
 291 | 
 292 |         A lock is reclaimable only when PID liveness is *proven false*.
 293 |         Creation, stale-file removal and ownership checks are serialized
 294 |         between processes using a persistent OS-level guard file.
 295 |         """
 296 |         with self._profile_lock_guard():
 297 |             # Reset may have removed a just-created directory while we
 298 |             # waited for the guard; create it *inside* the critical section.
 299 |             self.ensure_dirs()
 300 |             if self._lock_token is not None:
 301 |                 raise SessionError(
 302 |                     "this instance already owns the profile lock",
 303 |                     details={"stage": "acquire_lock"},
 304 |                 )
 305 |             if self._lock_path.exists():
 306 |                 owner = self._read_lock_owner()
 307 |                 if _pid_alive(owner["pid"]):
 308 |                     raise SessionError(
 309 |                         "profile is locked by a live process",
 310 |                         details={"stage": "acquire_lock", "lock": str(self._lock_path)},
 311 |                     )
 312 |                 # Only a dead PID is evidence of staleness. Guard eliminates
 313 |                 # the check/unlink/recreate race among current-version clients.
 314 |                 self._lock_path.unlink()
 315 |                 _log.warning("removed dead-owner profile lock", profile=self._config.profile_name)
 316 |             token = uuid.uuid4().hex
 317 |             payload = {"schema": 2, "pid": os.getpid(), "ts": time.time(), "owner_token": token}
 318 |             created = False
 319 |             try:
 320 |                 with open(self._lock_path, "x", encoding="utf-8") as handle:
 321 |                     created = True
 322 |                     handle.write(json.dumps(payload))
 323 |                     handle.flush()
 324 |                     os.fsync(handle.fileno())
 325 |             except OSError as exc:
 326 |                 # Only clean up a partial file that THIS attempt created.
 327 |                 if created:
 328 |                     try:
 329 |                         self._lock_path.unlink(missing_ok=True)
 330 |                     except OSError:
 331 |                         pass
 332 |                 raise SessionError(
 333 |                     "failed to acquire profile lock",
 334 |                     details={"stage": "acquire_lock", "lock": str(self._lock_path)},
```

**Targeted tests:** `test_f07_live_legacy_pid_older_than_24h_is_not_stolen`, `test_f07_same_pid_other_manager_cannot_acquire`, `test_f07_dead_legacy_lock_can_be_reclaimed`, `test_f07_two_contenders_for_dead_lock_have_one_winner`, `test_f07_unreadable_stale_metadata_cannot_be_stolen`, `test_f07_pid_permission_denied_is_not_considered_dead`.

### F-08 — owner-only lock release

**[stealth_engine/session.py:340-365](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L340-365)**

```python
 340 |     def release_lock(self) -> None:
 341 |         """Idempotent owner-only release; cannot unlink another instance's lock."""
 342 |         if self._lock_token is None:
 343 |             return
 344 |         with self._profile_lock_guard():
 345 |             if not self._lock_path.exists():
 346 |                 self._lock_token = None
 347 |                 self._lock_pid = None
 348 |                 return
 349 |             owner = self._read_lock_owner()
 350 |             if (
 351 |                 self._lock_pid != os.getpid()
 352 |                 or owner.get("pid") != self._lock_pid
 353 |                 or owner.get("owner_token") != self._lock_token
 354 |             ):
 355 |                 raise SessionError(
 356 |                     "profile lock ownership changed; refusing to release",
 357 |                     details={"stage": "release_lock", "lock": str(self._lock_path)},
 358 |                 )
 359 |             self._lock_path.unlink()
 360 |             self._lock_token = None
 361 |             self._lock_pid = None
 362 |             _log.debug("lock released", profile=self._config.profile_name)
 363 | 
 364 |     # ------------------------------------------------------------------
 365 |     # Profile reset
```

**Targeted tests:** `test_f08_nonowner_release_is_noop_and_owner_release_idempotent`, `test_f08_same_process_changed_token_cannot_release`, `test_f08_owner_does_not_delete_new_owner_after_replacement`.

### F-09 — force_reset refuses active/malformed owner

**[stealth_engine/session.py:368-402](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/session.py#L368-402)**

```python
 368 |     def force_reset(self) -> None:
 369 |         """Reset an idle profile only; never delete a live or unknown owner.
 370 | 
 371 |         A legacy {pid, ts} lock is blocked if its PID is live, regardless of
 372 |         timestamp. Unreadable locks also block reset (fail closed).
 373 |         """
 374 |         with self._profile_lock_guard():
 375 |             if self._lock_token is not None and self._lock_pid == os.getpid():
 376 |                 raise SessionError(
 377 |                     "cannot reset a profile still owned by this instance",
 378 |                     details={"stage": "force_reset", "lock": str(self._lock_path)},
 379 |                 )
 380 |             if self._lock_path.exists():
 381 |                 owner = self._read_lock_owner()
 382 |                 if _pid_alive(owner["pid"]):
 383 |                     raise SessionError(
 384 |                         "cannot reset a profile held by a live process",
 385 |                         details={"stage": "force_reset", "lock": str(self._lock_path)},
 386 |                     )
 387 |                 self._lock_path.unlink()
 388 |             if self._profile_dir.exists():
 389 |                 _log.warning("force_reset: deleting idle profile directory", profile=self._config.profile_name)
 390 |                 try:
 391 |                     shutil.rmtree(self._profile_dir)
 392 |                 except OSError as exc:
 393 |                     raise SessionError(
 394 |                         "failed to reset idle profile directory",
 395 |                         details={"stage": "force_reset", "reason": str(exc)},
 396 |                     ) from exc
 397 |             self._lock_token = None
 398 |             self._lock_pid = None
 399 | 
 400 |     # ------------------------------------------------------------------
 401 |     # Storage state export / import
 402 |     # ------------------------------------------------------------------
```

**Targeted tests:** `test_f09_live_reset_rejected_without_data_loss`, `test_f09_legacy_live_reset_and_malformed_reset_fail_closed`, `test_f09_idle_reset_succeeds_dead_lock_and_otherwise`, `test_f09_own_token_blocks_reset_even_if_lock_removed_externally`, `test_f09_filesystem_reset_failure_raises_typed_error`.

### F-18 — durable first-seen timestamp

**[stealth_engine/engine.py:485-552](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/engine.py#L485-552)**

```python
 485 |     def _record_fingerprint(self) -> bool:
 486 |         """Record recent fingerprints without losing immutable first-seen age.
 487 | 
 488 |         Existing history remains a JSON list (max 50). On first migration,
 489 |         copy the original history to a one-time backup before writing an
 490 |         atomic, versioned first-seen metadata sidecar. A previous, already
 491 |         truncated history cannot reconstruct an earlier unknown timestamp.
 492 |         """
 493 |         try:
 494 |             import json as _json
 495 |             import math as _math
 496 |             import os as _os
 497 |             import time as _time
 498 |             from pathlib import Path
 499 | 
 500 |             fp_hash = self._identity.fingerprint_hash()
 501 |             path = Path(self._session.profile_dir) / self._FP_HISTORY_FILE
 502 |             meta_path = path.with_name(self._FP_HISTORY_META_FILE)
 503 |             history: list[dict[str, Any]] = []
 504 |             if path.exists():
 505 |                 history = _json.loads(path.read_text(encoding="utf-8"))
 506 |                 if not isinstance(history, list) or any(not isinstance(h, dict) for h in history):
 507 |                     raise ValueError("invalid legacy fingerprint history; refusing to overwrite")
 508 | 
 509 |             now = round(_time.time(), 3)
 510 |             if meta_path.exists():
 511 |                 metadata = _json.loads(meta_path.read_text(encoding="utf-8"))
 512 |                 if not isinstance(metadata, dict) or metadata.get("schema_version") != 1:
 513 |                     raise ValueError("invalid first-seen metadata; refusing to overwrite")
 514 |                 first_seen = float(metadata["first_seen_ts"])
 515 |                 if not _math.isfinite(first_seen) or first_seen <= 0:
 516 |                     raise ValueError("invalid first-seen timestamp")
 517 |             else:
 518 |                 # Legacy histories have no separate first-seen record; use
 519 |                 # their oldest valid timestamp as the *known* lower bound.
 520 |                 known = [float(h["ts"]) for h in history
 521 |                          if isinstance(h.get("ts"), (int, float))
 522 |                          and _math.isfinite(float(h["ts"])) and float(h["ts"]) > 0]
 523 |                 first_seen = min(known) if known else now
 524 |                 path.parent.mkdir(parents=True, exist_ok=True)
 525 |                 if path.exists():
 526 |                     backup = path.with_name("fingerprint_history.legacy.json.bak")
 527 |                     if not backup.exists():
 528 |                         with open(backup, "xb") as handle:
 529 |                             handle.write(path.read_bytes())
 530 |                             handle.flush()
 531 |                             _os.fsync(handle.fileno())
 532 |                 metadata = {"schema_version": 1, "first_seen_ts": first_seen,
 533 |                             "origin": "legacy_oldest_known" if known else "first_record"}
 534 |                 meta_tmp = meta_path.with_suffix(".json.tmp")
 535 |                 meta_tmp.write_text(_json.dumps(metadata, indent=2), encoding="utf-8")
 536 |                 _os.replace(meta_tmp, meta_path)
 537 | 
 538 |             drifted = bool(history) and history[-1].get("hash") != fp_hash
 539 |             if drifted and not self._config.fingerprint_diversity:
 540 |                 _log.warning("fingerprint drift detected across launches",
 541 |                              profile=self._config.profile_name,
 542 |                              previous=str(history[-1].get("hash", ""))[:12],
 543 |                              current=fp_hash[:12])
 544 |             history.append({"ts": now, "hash": fp_hash,
 545 |                             "diversity": self._config.fingerprint_diversity})
 546 |             history = history[-self._FP_HISTORY_MAX:]
 547 |             path.parent.mkdir(parents=True, exist_ok=True)
 548 |             tmp = path.with_suffix(".json.tmp")
 549 |             tmp.write_text(_json.dumps(history, indent=2), encoding="utf-8")
 550 |             _os.replace(tmp, path)
 551 |             return drifted
 552 |         except Exception as exc:
```

**Targeted tests:** `test_f18_age_preserved_after_51_plus_history_records`, `test_f18_legacy_migration_backup_age_and_capping`, `test_f18_corrupt_meta_does_not_overwrite_or_invent_age`, `test_f18_legacy_read_still_supported_without_migration`.

### F-18 — session age reads sidecar first

**[stealth_engine/engine.py:1674-1706](https://gitlab.com/ivibtools/stealth-engine/-/blob/e4c60c11c62d4fcef0f8892ae484014f4324659f/stealth_engine/engine.py#L1674-1706)**

```python
1674 |     def session_age_days(self) -> float | None:
1675 |         """Age since immutable first-known launch, or legacy oldest record.
1676 | 
1677 |         A capped pre-migration history can only reveal its oldest *retained*
1678 |         timestamp. A malformed metadata sidecar returns None, not a guessed
1679 |         age derived from a later truncated entry.
1680 |         """
1681 |         import json as _json
1682 |         import math as _math
1683 | 
1684 |         path = Path(self._session.profile_dir) / "fingerprint_history.json"
1685 |         meta = path.with_name("fingerprint_history_meta.json")
1686 |         try:
1687 |             if meta.exists():
1688 |                 data = _json.loads(meta.read_text(encoding="utf-8"))
1689 |                 if not isinstance(data, dict) or data.get("schema_version") != 1:
1690 |                     return None
1691 |                 first_ts = float(data["first_seen_ts"])
1692 |             else:
1693 |                 if not path.exists():
1694 |                     return None
1695 |                 history = _json.loads(path.read_text(encoding="utf-8"))
1696 |                 if not isinstance(history, list) or not history:
1697 |                     return None
1698 |                 first_ts = float(history[0].get("ts", 0))
1699 |             if not _math.isfinite(first_ts) or first_ts <= 0:
1700 |                 return None
1701 |             return round((time.time() - first_ts) / 86400.0, 3)
1702 |         except (OSError, KeyError, ValueError, TypeError, OverflowError, IndexError, AttributeError):
1703 |             return None
1704 | 
1705 |     # ------------------------------------------------------------------
1706 |     # PH-19: engine depth — audit, CDP, contexts
```

**Targeted tests:** `test_f18_age_preserved_after_51_plus_history_records`, `tests.test_ghost.SessionAgeTests`.

## Focused offline verification and limitations

- **Command:** `cd /mnt/data/stealth_audit_workspace && PYTHONPATH=/mnt/data/stealth_audit_workspace python /mnt/data/stealth_phase01_test_shim/run_p02_tests.py` (temporary runner, not committed to GitLab).
- **Environment:** Linux Python 3.13; `camoufox` and `browserforge` not installed. Import-only test doubles for browserforge/Camoufox; mock Playwright contexts only in adjacent P-01 tests. No real browser or network effects executed.
- **Final result:** **35 tests run; 35 pass; 0 fail; process exit code 0**. Includes 18 new P-02 tests, plus 17 adjacent P-01 lifecycle/session age/state-save/close regression tests. The first invocation directly via unittest failed collection due to missing `browserforge`; an early harness run failed due to test-only mistake (`session_age_days` belongs to `BrowserSession`, not `StealthEngine`); corrected before final passing run. The first 30/30 pass was expanded by five negative cases to final 35/35.
- **Scope audit:** Python AST function inventory comparing exact pre-P02 GitLab blob content to final patched file: changes in `engine.py` only `StealthEngine._record_fingerprint`, `BrowserSession.session_age_days`; `session.py` only `_pid_alive`, `SessionManager.__init__` lock fields, `_profile_lock_guard`, `_read_lock_owner`, `acquire_lock`, `release_lock`, `force_reset`, removal of previous `_try_acquire_lock`. Regression test file only appended P-02 cases. Other `stealth_engine/`, UI, config, proxy, GeoIP and orchestration files unchanged. P-01 engine lifecycle methods unchanged by AST; CRLF restored so neighboring unmodified lines retain prior formatting.
- **Important behavioral changes:** A `.lock.guard` per-profile persistent guard file is created in the parent directory; it stays after `force_reset` to retain process coordination. `.lock` now contains `schema=2`, `pid`, `ts` and random `owner_token`. Old `{pid,ts}` lock records remain readable; live owner blocks; malformed/unknown locks fail closed; dead-PID recovery permits deletion. `force_reset` without active/unknown lock can still destructively remove an idle profile by design. `fingerprint_history_meta.json` and optional `fingerprint_history.legacy.json.bak` are new profile-local data files; the existing list format remains unchanged.
- **Known limits:** POSIX `fcntl` guard was exercised; **Windows `msvcrt.locking` not exercised**. Other running clients built from an older version do not honor the guard/owner-token protocol and require controlled migration to avoid interference. A pre-P02 capped history cannot recover first-seen records already discarded; the stored timestamp is the oldest observed legacy record, not guaranteed true creation date. Profile I/O failures retain existing `warn + return False` semantics; no real browser launch/persistence or user-admin UI test was run. No production-ready/real-stealth claim.
- **Acceptance:** P-02 **offline implementation verification passed**, but formal **production acceptance remains blocked** pending Windows, real browser and version migration checks. P-01 real-browser gate is separately still blocked.

## Next scope-locked phase — P-03 (NOT STARTED; requires approval)

F-05, F-11, F-12, F-14, F-15: correct SOCKS health-check transport, redact credential-related errors, reject invalid proxy authorities, resolve Geo `auto` correctly and avoid presenting private WebRTC IP as public. U-05 proxy-pool integration remains a documented conditional decision, not an authorized new feature. Only the paths/functions in `02-LOCKED-PHASE-ROADMAP.md` may change. No UI or P-01/P-02 code modifications authorized.
