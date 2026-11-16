"""Custom exception types for the stealth engine."""

from __future__ import annotations


class StealthEngineError(Exception):
    """Base exception for all stealth_engine errors.

    Args:
        message: Human-readable description of the error.
        details: Optional mapping of additional diagnostic context.
    """

    def __init__(
        self,
        message: str = "An unexpected stealth engine error occurred.",
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.details: dict | None = details

    def __str__(self) -> str:
        """Return message with compact details repr when present."""
        if self.details:
            return f"{self.message} | details={self.details!r}"
        return self.message


class ConfigError(StealthEngineError):
    """Raised when profile or proxy configuration is invalid.

    Args:
        message: Human-readable description of the configuration error.
        details: Optional mapping of additional diagnostic context.
    """


class IdentityError(StealthEngineError):
    """Raised when fingerprint or identity generation fails.

    Args:
        message: Human-readable description of the identity error.
        details: Optional mapping of additional diagnostic context.
    """


class ProxyError(StealthEngineError):
    """Raised when proxy validation, health check, or rotation fails.

    Args:
        message: Human-readable description of the proxy error.
        details: Optional mapping of additional diagnostic context.
    """


class SessionError(StealthEngineError):
    """Raised when session creation, restoration, or export fails.

    Args:
        message: Human-readable description of the session error.
        details: Optional mapping of additional diagnostic context.
    """


class LaunchError(StealthEngineError):
    """Raised when the browser engine fails to launch or initialize.

    Args:
        message: Human-readable description of the launch error.
        details: Optional mapping of additional diagnostic context.
    """


class AutomationError(StealthEngineError):
    """Raised when a browser automation action fails at runtime.

    Args:
        message: Human-readable description of the automation error.
        details: Optional mapping of additional diagnostic context.
    """
