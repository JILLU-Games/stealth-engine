"""Logging setup and configuration using loguru."""

from __future__ import annotations

import sys

from loguru import logger

# Single allowed module-level mutable state: idempotency guard.
_configured: bool = False


def configure_logging(level: str = "INFO", json_mode: bool = False) -> None:
    """Configure the loguru logger for stealth_engine.

    Removes loguru's default handler and registers a single stderr handler.
    Calling this function more than once is a no-op after the first call.

    Args:
        level: Minimum log level to emit (e.g. "DEBUG", "INFO", "WARNING").
        json_mode: When True, emit structured JSON lines via loguru serialisation.
    """
    global _configured  # noqa: PLW0603
    if _configured:
        return

    logger.remove()
    logger.add(
        sys.stderr,
        level=level.upper(),
        serialize=json_mode,
        enqueue=False,
    )
    _configured = True


def get_logger(name: str) -> "logger.__class__":
    """Return a loguru logger bound with a module context field.

    Does not create a new logger instance; uses loguru's process-global
    logger with an additional ``module`` binding.

    Args:
        name: Logical module name attached to every log record as ``module``.

    Returns:
        A bound loguru logger that includes ``module=name`` in every record.
    """
    return logger.bind(module=name)


# Profile-scoped records never alter the process-global loguru handlers.
# Engine-owned records can be filtered independently even when two profiles
# coexist in the same interpreter. Third-party and legacy module-level
# records are intentionally outside this scoped logger's control.
_PROFILE_LEVELS = {"TRACE": 5, "DEBUG": 10, "INFO": 20, "SUCCESS": 25,
                   "WARNING": 30, "ERROR": 40, "CRITICAL": 50}


class ProfileLogger:
    """Local severity gate for records *emitted through this instance*."""

    def __init__(self, name: str, profile: str, level: str, secrets: tuple[str, ...] = ()) -> None:
        canonical = level.upper()
        if canonical not in _PROFILE_LEVELS:
            raise ValueError(f"unsupported profile log_level: {level!r}")
        self._limit = _PROFILE_LEVELS[canonical]
        self._bound = logger.bind(module=name, profile=profile)
        self._secrets = tuple(value for value in secrets if value and value != "***")

    def log(self, severity: str, message: str, *args, **kwargs) -> None:
        canonical = severity.upper()
        if _PROFILE_LEVELS[canonical] < self._limit:
            return
        # Only scrub *this* profile's values; do not globally mutate logs.
        for secret in self._secrets:
            message = message.replace(secret, "***")
        args = tuple(self._scrub(arg) for arg in args)
        kwargs = {key: self._scrub(value) for key, value in kwargs.items()}
        self._bound.log(canonical, message, *args, **kwargs)

    def _scrub(self, value):
        """Recursively sanitize the values stored in Loguru's structured extras.

        Replacing only the human-readable message leaves passwords in
        record["extra"], especially when JSON logging is enabled.
        """
        if isinstance(value, str):
            for secret in self._secrets:
                value = value.replace(secret, "***")
            return value
        if isinstance(value, dict):
            return {self._scrub(k): self._scrub(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._scrub(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self._scrub(item) for item in value)
        if isinstance(value, (set, frozenset)):
            return type(value)(self._scrub(item) for item in value)
        return value

    def debug(self, message: str, *args, **kwargs):
        self.log("DEBUG", message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self.log("INFO", message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self.log("WARNING", message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self.log("ERROR", message, *args, **kwargs)


def get_profile_logger(name: str, profile: str, level: str, *, secrets: tuple[str, ...] = ()) -> ProfileLogger:
    """Create a profile-local severity gate without reconfiguring loguru."""
    return ProfileLogger(name, profile, level, secrets)
