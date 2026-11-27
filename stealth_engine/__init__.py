"""stealth_engine — a reusable stealth browser runtime for browser automation.

Provides engine-level fingerprint spoofing, proxy rotation, persistent sessions,
and bounded-concurrency bulk orchestration as a single drop-in package.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Version — must match pyproject.toml exactly.
# ---------------------------------------------------------------------------
__version__: str = "0.4.0"

# ---------------------------------------------------------------------------
# Eager imports: lightweight modules with no heavy transitive dependencies.
# ---------------------------------------------------------------------------
from .config import ProfileConfig, ProxyConfig, preset_names
from .exceptions import (
    AutomationError,
    ConfigError,
    IdentityError,
    LaunchError,
    ProxyError,
    SessionError,
    StealthEngineError,
)

# ---------------------------------------------------------------------------
# Lazy imports (PEP 562): engine and orchestrator pull in camoufox/playwright
# indirectly.  Resolving them only on first attribute access means that
# `import stealth_engine` stays fast and succeeds even when the heavy
# dependencies are not yet installed.
# ---------------------------------------------------------------------------
_LAZY: dict[str, str] = {
    "StealthEngine": ".engine",
    "BrowserSession": ".engine",
    "BulkRunner": ".orchestrator",
    "ProfileResult": ".orchestrator",
    "ProfileStatus": ".orchestrator",
    "IdentityProvider": ".identity",
    "BrowserForgeIdentityProvider": ".identity",
    "GeoResolver": ".geo",
    "GeoPolicy": ".geo",
    "StickyGeoStore": ".geo",
    "GeoDriftMonitor": ".geo",
    "GeoInfo": ".proxy",
    "load_proxies": ".proxy",
    "BehaviorProfile": ".behavior",
    "ban_risk_score": ".risk",
    "validate_fingerprint": ".identity",
    "matches_geo_policy": ".geo",
    "validate_geo_consistency": ".geo",
}

# Cache resolved objects here so repeated accesses are O(1).
_LAZY_CACHE: dict[str, object] = {}


def __getattr__(name: str) -> object:
    """Resolve lazy public names on first access (PEP 562).

    Args:
        name: Attribute name requested on the package.

    Returns:
        The resolved class or object.

    Raises:
        AttributeError: If ``name`` is not a known public name.
    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    if name in _LAZY:
        import importlib

        module_path = _LAZY[name]
        # module_path is a relative import string like ".engine"
        module = importlib.import_module(module_path, package=__name__)
        obj = getattr(module, name)
        # Cache in the module globals so subsequent attribute lookups skip
        # __getattr__ entirely (Python checks globals before __getattr__).
        globals()[name] = obj
        _LAZY_CACHE[name] = obj
        return obj

    _public = list(__all__)
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}. "
        f"Public names are: {_public}"
    )


# ---------------------------------------------------------------------------
# Public API surface — 29 names.
# ---------------------------------------------------------------------------
__all__: list[str] = [
    "__version__",
    # config
    "ProfileConfig",
    "ProxyConfig",
    # engine
    "StealthEngine",
    "BrowserSession",
    # orchestrator
    "BulkRunner",
    "ProfileResult",
    "ProfileStatus",
    # exceptions
    "StealthEngineError",
    "ConfigError",
    "IdentityError",
    "ProxyError",
    "SessionError",
    "LaunchError",
    "AutomationError",
    # identity providers
    "IdentityProvider",
    "BrowserForgeIdentityProvider",
    # geoip
    "GeoResolver",
    "GeoPolicy",
    "GeoInfo",
    "BehaviorProfile",
    "ban_risk_score",
    "StickyGeoStore",
    "GeoDriftMonitor",
    "load_proxies",
    "validate_fingerprint",
    "preset_names",
    "matches_geo_policy",
    "validate_geo_consistency",
]
