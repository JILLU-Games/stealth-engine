"""Browser session creation, management, and teardown."""

from __future__ import annotations

import asyncio
import hashlib
from contextlib import contextmanager
import json
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from .config import ProfileConfig
from .exceptions import SessionError
from .utils.logging import get_logger

_log = get_logger(__name__)

# Lock age is NOT a stale-owner signal: long-running live sessions must remain owned.


def _pid_alive(pid: int) -> bool:
    """Return True if a process with the given PID is currently running.

    POSIX: ``os.kill(pid, 0)`` probe.  Windows (BF-02): ``os.kill`` with
    signal 0 would call ``TerminateProcess`` and KILL the process —
    replaced with ``OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)``
    which only queries, never signals.

    Args:
        pid: Process ID to check.

    Returns:
        ``True`` if the process is alive, ``False`` otherwise.
    """
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(  # type: ignore[attr-defined]
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not handle:
                # Access denied means we cannot inspect this PID; fail closed.
                return ctypes.windll.kernel32.GetLastError() != 87
            ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]
            return True
        except Exception:
            # Missing Windows privileges/indeterminate liveness is NOT a dead PID.
            return True
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        # EPERM does not mean the process is dead.
        return True
    except ProcessLookupError:
        return False
    except OSError:
        # Unknown liveness is not evidence that stealing the lock is safe.
        return True


class SessionManager:
    """Manages per-profile browser session directories, lock files, and storage state.

    Each ``SessionManager`` instance owns exactly one profile directory::

        <base_dir>/<profile_name>/
            user_data/          ← browser profile data root
            storage_state.json  ← exported Playwright storage state
            .lock               ← PID lock file

    The class does **not** launch browsers or make network calls.  It
    only manages filesystem paths and JSON state files.

    Args:
        config: Validated profile configuration.
        base_dir: Root directory that contains all profile folders.
            Defaults to ``"./profiles"`` relative to the current
            working directory when ``None``.

    Raises:
        SessionError: If ``config.profile_name`` contains path
            separators or ``".."``.
    """


    def __init__(
        self,
        config: ProfileConfig,
        base_dir: str | None = None,
    ) -> None:
        resolved_base = Path(base_dir or "./profiles").resolve()

        # Guard against path-traversal in profile_name.
        name = config.profile_name
        if os.sep in name or (os.altsep and os.altsep in name) or ".." in name.split("/"):
            raise SessionError(
                "profile_name must not contain path separators or '..'",
                details={"stage": "init", "profile_name": name},
            )
        # Also reject forward/backslash explicitly (covers Windows altsep gap).
        if "/" in name or "\\" in name:
            raise SessionError(
                "profile_name must not contain path separators",
                details={"stage": "init", "profile_name": name},
            )

        # B-018: Resolved-path prefix check — additional defence against edge cases
        # (e.g. Unicode normalisation tricks, case-insensitive FS, unusual symlinks)
        # that bypass the string-based guards above.
        try:
            resolved_prof = (resolved_base / name).resolve()
            expected_prefix = str(resolved_base) + os.sep
            if not str(resolved_prof).startswith(expected_prefix):
                raise SessionError(
                    "profile_name would escape the base directory (path traversal)",
                    details={"stage": "init", "reason": "path traversal", "profile_name": name},
                )
        except SessionError:
            raise
        except (OSError, RuntimeError):
            # Resolution failed (e.g. dangling symlink in base_dir, unusual FS).
            # Fall back to the string guards already applied above and continue.
            _log.warning(
                "path traversal resolved-check skipped (resolve() failed); "
                "relying on string guards",
                profile_name=name,
            )

        self._config: ProfileConfig = config
        self._profile_dir: Path = resolved_base / name
        self._user_data_dir: Path = self._profile_dir / "user_data"
        self._storage_state_path: Path = self._profile_dir / "storage_state.json"
        self._lock_path: Path = self._profile_dir / ".lock"
        # Guard lives OUTSIDE the profile dir, so force_reset cannot remove it
        # while another instance is waiting to inspect this profile's lock.
        self._lock_guard_path: Path = resolved_base / f".{name}.lock.guard"
        self._lock_token: str | None = None
        self._lock_pid: int | None = None

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def user_data_dir(self) -> str:
        """Absolute path to the browser user-data directory for this profile.

        Returns:
            String path (no trailing separator).
        """
        return str(self._user_data_dir)

    @property
    def storage_state_path(self) -> str:
        """Absolute path to the Playwright storage-state JSON file.

        Returns:
            String path.
        """
        return str(self._storage_state_path)

    @property
    def profile_dir(self) -> str:
        """Root directory of this profile (parent of ``user_data``).

        Returns:
            Absolute path string of the profile directory.
        """
        return str(self._profile_dir)

    @property
    def lock_path(self) -> str:
        """Absolute path to the PID lock file.

        Returns:
            String path.
        """
        return str(self._lock_path)

    # ------------------------------------------------------------------
    # Directory management
    # ------------------------------------------------------------------

    def ensure_dirs(self) -> None:
        """Create the profile directory tree if it does not yet exist.

        Sets permissions to ``0o700`` on the profile root (best-effort;
        silently ignores ``PermissionError`` on non-POSIX systems).
        Idempotent — safe to call multiple times.

        Raises:
            SessionError: If directory creation fails (e.g. read-only
                filesystem or disk full).
        """
        try:
            self._profile_dir.mkdir(parents=True, exist_ok=True)
            self._user_data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise SessionError(
                "failed to create profile directories",
                details={
                    "stage": "ensure_dirs",
                    "path": str(self._profile_dir),
                    "reason": str(exc),
                },
            ) from exc

        try:
            os.chmod(self._profile_dir, 0o700)
        except PermissionError:
            _log.warning(
                "ensure_dirs: could not set 0o700 on profile dir (best-effort)",
                path=str(self._profile_dir),
            )
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Lock management
    # ------------------------------------------------------------------

    @contextmanager
    def _profile_lock_guard(self):
        """Serialize all lock inspection, stale recovery, release and reset.

        The guard file stays in the base directory even after force_reset:
        removing a locked guard file would allow a second instance to use a
        different inode and enter the same critical section.
        """
        try:
            self._lock_guard_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(str(self._lock_guard_path), os.O_CREAT | os.O_RDWR, 0o600)
            with os.fdopen(fd, "r+b") as guard:
                if guard.seek(0, os.SEEK_END) == 0:
                    guard.write(b"\0")
                    guard.flush()
                guard.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(guard.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl

                    fcntl.flock(guard.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    if os.name == "nt":
                        guard.seek(0)
                        msvcrt.locking(guard.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(guard.fileno(), fcntl.LOCK_UN)
        except OSError as exc:
            raise SessionError(
                "profile lock guard is unavailable",
                details={"stage": "lock_guard", "reason": str(exc)},
            ) from exc

    def _read_lock_owner(self) -> dict[str, Any]:
        """Read a lock while holding the guard; malformed locks fail closed."""
        try:
            owner = json.loads(self._lock_path.read_text(encoding="utf-8"))
            if not isinstance(owner, dict):
                raise ValueError("not an object")
            pid = owner.get("pid")
            if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
                raise ValueError("missing valid PID")
            token = owner.get("owner_token")
            if token is not None and (not isinstance(token, str) or not token):
                raise ValueError("invalid owner token")
            # Old {pid, ts} records remain readable; any live PID blocks reset.
            return owner
        except (OSError, ValueError, UnicodeError) as exc:
            raise SessionError(
                "profile lock metadata cannot be safely verified",
                details={"stage": "lock_owner", "lock": str(self._lock_path)},
            ) from exc

    def acquire_lock(self) -> None:
        """Acquire an atomic, instance-owned PID lock; never steal a live PID.

        A lock is reclaimable only when PID liveness is *proven false*.
        Creation, stale-file removal and ownership checks are serialized
        between processes using a persistent OS-level guard file.
        """
        with self._profile_lock_guard():
            # Reset may have removed a just-created directory while we
            # waited for the guard; create it *inside* the critical section.
            self.ensure_dirs()
            if self._lock_token is not None:
                raise SessionError(
                    "this instance already owns the profile lock",
                    details={"stage": "acquire_lock"},
                )
            if self._lock_path.exists():
                owner = self._read_lock_owner()
                if _pid_alive(owner["pid"]):
                    raise SessionError(
                        "profile is locked by a live process",
                        details={"stage": "acquire_lock", "lock": str(self._lock_path)},
                    )
                # Only a dead PID is evidence of staleness. Guard eliminates
                # the check/unlink/recreate race among current-version clients.
                self._lock_path.unlink()
                _log.warning("removed dead-owner profile lock", profile=self._config.profile_name)
            token = uuid.uuid4().hex
            payload = {"schema": 2, "pid": os.getpid(), "ts": time.time(), "owner_token": token}
            created = False
            try:
                with open(self._lock_path, "x", encoding="utf-8") as handle:
                    created = True
                    handle.write(json.dumps(payload))
                    handle.flush()
                    os.fsync(handle.fileno())
            except OSError as exc:
                # Only clean up a partial file that THIS attempt created.
                if created:
                    try:
                        self._lock_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                raise SessionError(
                    "failed to acquire profile lock",
                    details={"stage": "acquire_lock", "lock": str(self._lock_path)},
                ) from exc
            self._lock_token = token
            self._lock_pid = os.getpid()
            _log.debug("lock acquired", profile=self._config.profile_name)

    def release_lock(self) -> None:
        """Idempotent owner-only release; cannot unlink another instance's lock."""
        if self._lock_token is None:
            return
        with self._profile_lock_guard():
            if not self._lock_path.exists():
                self._lock_token = None
                self._lock_pid = None
                return
            owner = self._read_lock_owner()
            if (
                self._lock_pid != os.getpid()
                or owner.get("pid") != self._lock_pid
                or owner.get("owner_token") != self._lock_token
            ):
                raise SessionError(
                    "profile lock ownership changed; refusing to release",
                    details={"stage": "release_lock", "lock": str(self._lock_path)},
                )
            self._lock_path.unlink()
            self._lock_token = None
            self._lock_pid = None
            _log.debug("lock released", profile=self._config.profile_name)

    # ------------------------------------------------------------------
    # Profile reset
    # ------------------------------------------------------------------

    def force_reset(self) -> None:
        """Reset an idle profile only; never delete a live or unknown owner.

        A legacy {pid, ts} lock is blocked if its PID is live, regardless of
        timestamp. Unreadable locks also block reset (fail closed).
        """
        with self._profile_lock_guard():
            if self._lock_token is not None and self._lock_pid == os.getpid():
                raise SessionError(
                    "cannot reset a profile still owned by this instance",
                    details={"stage": "force_reset", "lock": str(self._lock_path)},
                )
            if self._lock_path.exists():
                owner = self._read_lock_owner()
                if _pid_alive(owner["pid"]):
                    raise SessionError(
                        "cannot reset a profile held by a live process",
                        details={"stage": "force_reset", "lock": str(self._lock_path)},
                    )
                self._lock_path.unlink()
            if self._profile_dir.exists():
                _log.warning("force_reset: deleting idle profile directory", profile=self._config.profile_name)
                try:
                    shutil.rmtree(self._profile_dir)
                except OSError as exc:
                    raise SessionError(
                        "failed to reset idle profile directory",
                        details={"stage": "force_reset", "reason": str(exc)},
                    ) from exc
            self._lock_token = None
            self._lock_pid = None

    # ------------------------------------------------------------------
    # Storage state export / import
    # ------------------------------------------------------------------

    def export_state(
        self, storage_state: dict, domains: list[str] | None = None
    ) -> None:
        """Persist a Playwright storage-state dict to disk atomically.

        Validates that ``storage_state`` contains at least ``"cookies"``
        (list) and ``"origins"`` (list).  Writes to a temporary file and
        uses :func:`os.replace` so the operation is atomic on all
        supported platforms.

        Args:
            storage_state: Dict produced by Playwright's
                ``context.storage_state()`` call.  Must contain
                ``"cookies"`` and ``"origins"`` list keys.
            domains: Optional allow-list of domains (PH-18, N8).  When
                provided, only cookies whose ``domain`` ends with one of
                the listed domains and origins whose ``origin`` host
                matches are exported — useful for multi-account storage
                splitting.

        Raises:
            SessionError: If ``storage_state`` is not a dict or is
                missing/wrong-typed required keys.
        """
        if not isinstance(storage_state, dict):
            raise SessionError(
                "storage_state must be a dict",
                details={"stage": "export_state", "type": type(storage_state).__name__},
            )
        for key in ("cookies", "origins"):
            val = storage_state.get(key)
            if not isinstance(val, list):
                raise SessionError(
                    f"storage_state missing required list field: {key!r}",
                    details={"stage": "export_state", "missing_key": key},
                )

        if domains is not None:
            from urllib.parse import urlparse

            allowed = {d.lower().lstrip(".") for d in domains if d.strip()}

            def _host_of(url_or_domain: str) -> str:
                s = url_or_domain.lower()
                if "://" in s:
                    s = urlparse(s).hostname or ""
                return s.lstrip(".")

            def _domain_match(host: str, domain: str) -> bool:
                # BF-02/B-04: dot-boundary suffix match — "notexample.com"
                # must NOT match "example.com".  Bidirectional so a
                # parent-domain cookie (.example.com) still exports when
                # filtering a subdomain (sub.example.com), which is
                # semantically correct since the cookie applies there.
                if not host:
                    return False
                return (
                    host == domain
                    or host.endswith("." + domain)
                    or domain.endswith("." + host)
                )

            filtered_cookies = [
                c for c in storage_state["cookies"]
                if any(
                    _domain_match(_host_of(str(c.get("domain", ""))), d)
                    for d in allowed
                )
            ]
            filtered_origins = [
                o for o in storage_state["origins"]
                if any(
                    _domain_match(_host_of(str(o.get("origin", ""))), d)
                    for d in allowed
                )
            ]
            storage_state = {
                "cookies": filtered_cookies,
                "origins": filtered_origins,
            }

        self.ensure_dirs()

        serialised = json.dumps(storage_state, sort_keys=True)
        tmp_path = self._storage_state_path.with_suffix(".json.tmp")

        wrote = False
        try:
            tmp_path.write_text(serialised, encoding="utf-8")
            os.replace(str(tmp_path), str(self._storage_state_path))
            wrote = True
        except OSError as exc:
            raise SessionError(
                "failed to write storage state",
                details={"stage": "export_state", "reason": str(exc)},
            ) from exc
        finally:
            # Clean up temp file ONLY on failure (wrote=False means
            # os.replace did not complete and the tmp file may still exist).
            if not wrote:
                try:
                    tmp_path.unlink(missing_ok=True)
                except OSError:
                    pass

        _log.debug(
            "storage state exported",
            profile=self._config.profile_name,
            size_bytes=len(serialised),
        )

    def import_state(self) -> dict | None:
        """Load and return the stored Playwright storage-state dict.

        Returns:
            The parsed dict, or ``None`` if the file does not exist.

        Raises:
            SessionError: If the file exists but contains malformed JSON.
        """
        path = self._storage_state_path
        if not path.exists():
            return None

        try:
            raw = path.read_text(encoding="utf-8")
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SessionError(
                "storage state file contains malformed JSON",
                details={"stage": "import_state", "path": str(path), "reason": str(exc)},
            ) from exc
        except OSError as exc:
            raise SessionError(
                "failed to read storage state",
                details={"stage": "import_state", "path": str(path), "reason": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # State introspection
    # ------------------------------------------------------------------

    def has_state(self) -> bool:
        """Return whether a valid storage-state file exists for this profile.

        Performs a lightweight check: the file must exist, be larger than
        2 bytes, and contain parseable JSON with a ``"cookies"`` key.

        Returns:
            ``True`` iff all three conditions hold; ``False`` otherwise.
        """
        path = self._storage_state_path
        try:
            if not path.exists() or path.stat().st_size <= 2:
                return False
            data = json.loads(path.read_text(encoding="utf-8"))
            return "cookies" in data
        except (OSError, json.JSONDecodeError, ValueError):
            return False

    def state_metadata(self) -> dict[str, Any]:
        """Return filesystem metadata for the storage-state file.

        Returns a dict with the following keys:

        - ``"exists"`` (:class:`bool`): whether the file is present
        - ``"size_bytes"`` (:class:`int`): file size, or ``0`` if absent
        - ``"mtime_epoch"`` (:class:`int`): last-modified timestamp
          (integer seconds), or ``0`` if absent
        - ``"sha256"`` (:class:`str` or ``None``): hex digest of file
          contents when the file exists; ``None`` otherwise

        No secrets are included in the output.

        Returns:
            Metadata dict as described above.
        """
        path = self._storage_state_path
        if not path.exists():
            return {"exists": False, "size_bytes": 0, "mtime_epoch": 0, "sha256": None}

        try:
            stat = path.stat()
            raw = path.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            return {
                "exists": True,
                "size_bytes": stat.st_size,
                "mtime_epoch": int(stat.st_mtime),
                "sha256": sha,
            }
        except OSError as exc:
            raise SessionError(
                "failed to read storage state metadata",
                details={"stage": "state_metadata", "path": str(path), "reason": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "SessionManager":
        """Prepare the session: create directories and acquire the lock.

        Returns:
            This :class:`SessionManager` instance.

        Raises:
            SessionError: If the lock cannot be acquired.
        """
        self.ensure_dirs()
        self.acquire_lock()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        """Release the lock unconditionally on context exit.

        Exceptions from the ``with`` block are never suppressed.

        Args:
            exc_type: Exception type, or ``None``.
            exc: Exception instance, or ``None``.
            tb: Traceback, or ``None``.
        """
        self.release_lock()
