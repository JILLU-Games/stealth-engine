"""Bulk runner and task orchestration across multiple sessions."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Callable

from .config import ProfileConfig
from .engine import BrowserSession, StealthEngine
from .exceptions import AutomationError, IdentityError, SessionError
from .identity import IdentityProvider
from .utils.logging import get_logger

_log = get_logger(__name__)

# Exceptions that indicate a permanent failure for this profile run —
# retrying will not help, so the result is SKIPPED immediately.
_NON_RETRYABLE: tuple[type[Exception], ...] = (IdentityError, SessionError)


class ProfileStatus(str, Enum):
    """Outcome status for a single profile task execution.

    Attributes:
        SUCCESS: The task function completed without raising an exception.
        FAILED: All retry attempts were exhausted with errors.
        SKIPPED: A non-retryable condition was detected; no retry was attempted.
    """

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProfileResult:
    """Recorded outcome for a single profile after all attempts.

    Attributes:
        profile_name: Identifier from :attr:`ProfileConfig.profile_name`.
        status: Final :class:`ProfileStatus` of this run.
        attempts: Number of launch+task attempts made (0 if skipped before
            any attempt started).
        duration_ms: Wall-clock time from the first attempt start to
            completion, in milliseconds.
        error: Human-readable error message from the last failure, or
            ``None`` on success.
    """

    profile_name: str
    status: ProfileStatus
    attempts: int
    duration_ms: float
    error: str | None = None


class BulkRunner:
    """Runs an async task function against a pool of profiles concurrently.

    Controls concurrency with an :class:`asyncio.Semaphore`, applies
    exponential backoff between retries, and serialises staggered starts
    via an optional per-launch gap.  Results are returned in the same
    order as the input ``profiles`` list regardless of completion order.

    Args:
        profiles: Non-empty list of :class:`~stealth_engine.config.ProfileConfig`
            instances to run the task against.
        concurrency: Maximum number of simultaneously active browser sessions.
            Must be between 1 and ``len(profiles)`` inclusive.
        max_attempts: Maximum launch+task attempts per profile before
            marking it ``FAILED``.
        backoff_base_s: Base delay in seconds for exponential backoff.
            Must be > 0.
        backoff_max_s: Upper cap for backoff delay.  Must be >=
            ``backoff_base_s``.
        min_start_gap_s: Minimum seconds to wait between successive profile
            starts.  0 disables the gap.
        identity_provider: Optional custom
            :class:`~stealth_engine.identity.IdentityProvider` shared by all
            profiles in this run.  ``None`` uses the default
            browserforge-backed provider.
        task_timeout_s: Optional per-task timeout in seconds applied to
            ``task_fn`` via :func:`asyncio.wait_for`; ``None`` disables.
            Timed-out tasks count as failed attempts (retryable).

    Raises:
        AutomationError: If any validation constraint above is violated.
    """

    def __init__(
        self,
        profiles: list[ProfileConfig],
        *,
        concurrency: int = 3,
        max_attempts: int = 3,
        backoff_base_s: float = 1.0,
        backoff_max_s: float = 30.0,
        min_start_gap_s: float = 0.0,
        identity_provider: IdentityProvider | None = None,
        task_timeout_s: float | None = None,
    ) -> None:
        if not profiles:
            raise AutomationError(
                "profiles list must not be empty",
                details={"stage": "init", "reason": "empty profiles"},
            )
        if concurrency < 1 or concurrency > len(profiles):
            raise AutomationError(
                f"concurrency must be between 1 and {len(profiles)}; got {concurrency}",
                details={"stage": "init", "concurrency": concurrency},
            )
        if max_attempts < 1:
            raise AutomationError(
                f"max_attempts must be >= 1; got {max_attempts}",
                details={"stage": "init", "max_attempts": max_attempts},
            )
        if backoff_base_s <= 0:
            raise AutomationError(
                f"backoff_base_s must be > 0; got {backoff_base_s}",
                details={"stage": "init", "backoff_base_s": backoff_base_s},
            )
        if backoff_max_s < backoff_base_s:
            raise AutomationError(
                f"backoff_max_s must be >= backoff_base_s; got {backoff_max_s} < {backoff_base_s}",
                details={"stage": "init", "backoff_max_s": backoff_max_s},
            )
        if min_start_gap_s < 0:
            raise AutomationError(
                f"min_start_gap_s must be >= 0; got {min_start_gap_s}",
                details={"stage": "init", "min_start_gap_s": min_start_gap_s},
            )
        if task_timeout_s is not None and task_timeout_s <= 0:
            raise AutomationError(
                f"task_timeout_s must be > 0 when set; got {task_timeout_s}",
                details={"stage": "init", "task_timeout_s": task_timeout_s},
            )

        self._profiles: list[ProfileConfig] = list(profiles)  # defensive copy
        self._concurrency: int = concurrency
        self._max_attempts: int = max_attempts
        self._backoff_base_s: float = backoff_base_s
        self._backoff_max_s: float = backoff_max_s
        self._min_start_gap_s: float = min_start_gap_s
        self._identity_provider: IdentityProvider | None = identity_provider
        self._task_timeout_s: float | None = task_timeout_s

        # Semaphore and lock are created lazily inside run() where
        # an event loop is guaranteed to be running.
        self._semaphore: asyncio.Semaphore | None = None
        self._start_gap_lock: asyncio.Lock | None = None
        self._last_start_ts: float = 0.0

        # In-flight asyncio.Task references for cancellation via shutdown().
        self._inflight: set[asyncio.Task] = set()  # type: ignore[type-arg]
        self._shutting_down: bool = False
        self._run_active: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(
        self,
        task_fn: Callable[[BrowserSession], Awaitable[None]],
    ) -> list[ProfileResult]:
        """Execute ``task_fn`` for every profile, respecting concurrency limits.

        Each profile runs in its own :class:`asyncio.Task`.  Failed tasks
        are captured as :attr:`~ProfileStatus.FAILED` or
        :attr:`~ProfileStatus.SKIPPED` in the results; they never propagate
        as exceptions from this method.

        Args:
            task_fn: Async callable that accepts a live
                :class:`~stealth_engine.engine.BrowserSession` and returns
                ``None``.  Must be safe to call concurrently.

        Returns:
            List of :class:`ProfileResult` in the **same order** as the
            ``profiles`` passed to :meth:`__init__`.

        Raises:
            AutomationError: Only if the runner itself fails catastrophically
                (e.g. task gather raises an unexpected internal error).
        """
        if self._shutting_down:
            raise AutomationError(
                "BulkRunner has been shut down; create a new instance to run again",
                details={"stage": "run", "reason": "shutting_down=True"},
            )

        # BF-03/B-19: guard against concurrent/re-entrant run() calls —
        # each call would create a fresh semaphore and silently double
        # the effective concurrency limit.
        if self._run_active:
            raise AutomationError(
                "BulkRunner.run() is already in progress",
                details={"stage": "run", "reason": "re-entrant run()"},
            )
        self._run_active = True

        # Lazy initialisation of asyncio primitives (event loop now exists).
        self._semaphore = asyncio.Semaphore(self._concurrency)
        self._start_gap_lock = asyncio.Lock()

        # Pre-allocate results list to preserve input order.
        results: list[ProfileResult | None] = [None] * len(self._profiles)

        # Build one coroutine per profile; wrap in Task so shutdown can cancel.
        tasks: list[asyncio.Task] = []  # type: ignore[type-arg]
        for idx, profile in enumerate(self._profiles):
            coro = self._run_profile(task_fn, idx, profile, results)
            task: asyncio.Task = asyncio.create_task(coro, name=f"profile-{profile.profile_name}")  # type: ignore[type-arg]
            self._inflight.add(task)
            task.add_done_callback(self._inflight.discard)
            tasks.append(task)

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            self._run_active = False

        # B-008: Fill any slots still None (task was cancelled before it could
        # write a result) so the returned list always has the same length and
        # order as self._profiles.
        for i, profile in enumerate(self._profiles):
            if results[i] is None:
                results[i] = ProfileResult(
                    profile_name=profile.profile_name,
                    status=ProfileStatus.FAILED,
                    attempts=0,
                    duration_ms=0.0,
                    error="cancelled by shutdown",
                )

        final: list[ProfileResult] = [r for r in results if r is not None]  # type: ignore[misc]
        return final

    def run_sync(
        self,
        task_fn: Callable[[BrowserSession], Awaitable[None]],
    ) -> list[ProfileResult]:
        """Synchronous wrapper around :meth:`run`.

        Args:
            task_fn: Same async callable as :meth:`run`.

        Returns:
            List of :class:`ProfileResult` in input order.

        Raises:
            AutomationError: If an event loop is already running (caller
                must use :meth:`run` directly in that case).
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            raise AutomationError(
                "Cannot call run_sync() from a running event loop. "
                "Use 'await runner.run(task_fn)' instead.",
                details={"stage": "run_sync", "reason": "running event loop detected"},
            )

        return asyncio.run(self.run(task_fn))

    async def shutdown(self) -> None:
        """Cancel all in-flight tasks and mark the runner as shut down.

        Sets ``_shutting_down = True``, cancels every task currently
        tracked in :attr:`_inflight`, and awaits their completion.
        Subsequent calls to :meth:`run` will raise :class:`AutomationError`.

        Idempotent — safe to call multiple times even if :meth:`run` was
        never started.
        """
        self._shutting_down = True
        if not self._inflight:
            return

        tasks = list(self._inflight)
        for t in tasks:
            t.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)
        _log.info("BulkRunner shutdown complete", cancelled=len(tasks))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_profile(
        self,
        task_fn: Callable[[BrowserSession], Awaitable[None]],
        idx: int,
        profile: ProfileConfig,
        results: list[ProfileResult | None],
    ) -> None:
        """Lifecycle for a single profile: acquire semaphore, retry loop, record result.

        Args:
            task_fn: User-supplied async task callable.
            idx: Index into ``results`` for this profile (preserves order).
            profile: The :class:`~stealth_engine.config.ProfileConfig` to run.
            results: Shared pre-allocated result list (written at ``idx``).
        """
        assert self._semaphore is not None  # guaranteed by run()
        assert self._start_gap_lock is not None

        async with self._semaphore:
            # Enforce minimum gap between successive session starts.
            await self._enforce_start_gap()

            if self._shutting_down:
                results[idx] = ProfileResult(
                    profile_name=profile.profile_name,
                    status=ProfileStatus.SKIPPED,
                    attempts=0,
                    duration_ms=0.0,
                    error="runner was shut down before this profile started",
                )
                return

            results[idx] = await self._attempt_profile(task_fn, profile)

        _log.info(
            "profile complete",
            profile=results[idx].profile_name,  # type: ignore[union-attr]
            status=results[idx].status,  # type: ignore[union-attr]
            attempts=results[idx].attempts,  # type: ignore[union-attr]
            duration_ms=results[idx].duration_ms,  # type: ignore[union-attr]
        )

    async def _enforce_start_gap(self) -> None:
        """Sleep if needed so consecutive launches are at least ``min_start_gap_s`` apart.

        Uses the start-gap lock to serialise gap accounting across concurrent
        tasks.
        """
        if self._min_start_gap_s <= 0.0:
            return

        assert self._start_gap_lock is not None
        async with self._start_gap_lock:
            now = time.monotonic()
            elapsed = now - self._last_start_ts
            remainder = self._min_start_gap_s - elapsed
            if remainder > 0.0:
                await asyncio.sleep(remainder)
            self._last_start_ts = time.monotonic()

    async def _attempt_profile(
        self,
        task_fn: Callable[[BrowserSession], Awaitable[None]],
        profile: ProfileConfig,
    ) -> ProfileResult:
        """Run the task against a single profile with retry + backoff.

        Args:
            task_fn: User-supplied async task callable.
            profile: Profile configuration for this run.

        Returns:
            Populated :class:`ProfileResult` (SUCCESS, FAILED, or SKIPPED).
        """
        # Per-profile isolated RNG for jitter — no global random.
        rng = random.Random(profile.seed) if profile.seed is not None else random.Random()

        wall_start = time.perf_counter()
        last_error: str = ""
        attempts = 0

        for attempt in range(1, self._max_attempts + 1):
            attempts = attempt
            session: BrowserSession | None = None
            engine: StealthEngine | None = None

            try:
                engine = StealthEngine(
                    profile, identity_provider=self._identity_provider
                )
                session = await engine.alaunch()
                if self._task_timeout_s is not None:
                    await asyncio.wait_for(
                        task_fn(session), timeout=self._task_timeout_s
                    )
                else:
                    await task_fn(session)

                duration_ms = round((time.perf_counter() - wall_start) * 1000.0, 2)
                return ProfileResult(
                    profile_name=profile.profile_name,
                    status=ProfileStatus.SUCCESS,
                    attempts=attempts,
                    duration_ms=duration_ms,
                )

            except _NON_RETRYABLE as exc:
                # SessionError (locked) or IdentityError — not worth retrying.
                duration_ms = round((time.perf_counter() - wall_start) * 1000.0, 2)
                _log.warning(
                    "profile skipped (non-retryable)",
                    profile=profile.profile_name,
                    reason=str(exc),
                )
                return ProfileResult(
                    profile_name=profile.profile_name,
                    status=ProfileStatus.SKIPPED,
                    attempts=attempts,
                    duration_ms=duration_ms,
                    error=str(exc),
                )

            except asyncio.CancelledError:
                # Propagate cancellation immediately — do not swallow.
                raise

            except Exception as exc:
                last_error = str(exc) or type(exc).__name__
                _log.warning(
                    "profile attempt failed",
                    profile=profile.profile_name,
                    attempt=attempt,
                    max_attempts=self._max_attempts,
                    error=last_error,
                )

            finally:
                if session is not None:
                    try:
                        await session.aclose()
                    except Exception as close_exc:
                        _log.warning(
                            "session.aclose() failed during cleanup",
                            profile=profile.profile_name,
                            reason=str(close_exc),
                        )

            # Sleep before the next attempt (skip after the last attempt).
            if attempt < self._max_attempts and not self._shutting_down:
                delay = min(
                    self._backoff_max_s,
                    self._backoff_base_s * (2 ** (attempt - 1)),
                )
                # ±20% jitter
                jitter_factor = rng.uniform(0.8, 1.2)
                await asyncio.sleep(delay * jitter_factor)

        duration_ms = round((time.perf_counter() - wall_start) * 1000.0, 2)
        return ProfileResult(
            profile_name=profile.profile_name,
            status=ProfileStatus.FAILED,
            attempts=attempts,
            duration_ms=duration_ms,
            error=last_error or "unknown error",
        )
