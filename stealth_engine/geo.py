"""Standalone reusable GeoIP resolution layer.

Complements :mod:`stealth_engine.proxy` with a browser-independent resolver:
direct-IP lookup, host-IP lookup, country policy filters, TTL caching, and
batched concurrent resolution.  No camoufox/playwright dependency — safe to
use from any project that installs ``stealth_engine``.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import aiohttp
from pydantic import BaseModel, ConfigDict, Field

from .config import ProfileConfig, ProxyConfig
from .exceptions import ConfigError, ProxyError
from .proxy import GeoInfo, ProxyManager, parse_geo_data
from .utils.logging import get_logger

_log = get_logger(__name__)

# ISO 3166-1 alpha-2 codes for the European Union + EEA-adjacent set used by
# the built-in "eu" policy preset.
_EU_COUNTRIES: tuple[str, ...] = (
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
)


class GeoPolicy(BaseModel):
    """Named geo-filtering policy for proxy/geo selection.

    Attributes:
        name: Human-readable policy identifier.
        allowed_countries: ISO alpha-2 allow list (empty = any).
        blocked_countries: ISO alpha-2 block list.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    allowed_countries: list[str] = Field(default_factory=list)
    blocked_countries: list[str] = Field(default_factory=list)

    def matches(self, geo: GeoInfo) -> bool:
        """Return True when ``geo`` satisfies this policy."""
        return matches_geo_policy(
            geo,
            allowed_countries=self.allowed_countries,
            blocked_countries=self.blocked_countries,
        )

    @classmethod
    def preset(cls, name: str) -> "GeoPolicy":
        """Return a built-in policy preset by name.

        Available presets: ``"any"``, ``"us-strict"``, ``"eu"``.

        Raises:
            ConfigError: If ``name`` is not a known preset.
        """
        key = name.strip().lower()
        if key == "any":
            return cls(name="any")
        if key == "us-strict":
            return cls(name="us-strict", allowed_countries=["US"])
        if key == "eu":
            return cls(name="eu", allowed_countries=list(_EU_COUNTRIES))
        raise ConfigError(
            f"unknown geo policy preset: {name!r}",
            details={"stage": "geo_policy", "preset": name},
        )


def _norm_countries(countries: list[str] | set[str] | tuple[str, ...] | None) -> frozenset[str] | None:
    """Normalise a country-code iterable to an uppercase frozenset."""
    if not countries:
        return None
    return frozenset(str(c).strip().upper() for c in countries if str(c).strip())


def matches_geo_policy(
    geo: GeoInfo,
    *,
    allowed_countries: list[str] | set[str] | tuple[str, ...] | None = None,
    blocked_countries: list[str] | set[str] | tuple[str, ...] | None = None,
) -> bool:
    """Check ``geo.country`` against allow/block country lists.

    Args:
        geo: Resolved geolocation.
        allowed_countries: When non-empty, country must be in this set.
        blocked_countries: When non-empty, country must NOT be in this set.

    Returns:
        ``True`` when the geo passes all configured filters.
    """
    country = geo.country.upper()
    allowed = _norm_countries(allowed_countries)
    blocked = _norm_countries(blocked_countries)
    if allowed is not None and country not in allowed:
        return False
    if blocked is not None and country in blocked:
        return False
    return True


def validate_geo_consistency(geo: GeoInfo, config: ProfileConfig) -> dict[str, Any]:
    """Compare a :class:`GeoInfo` against a :class:`ProfileConfig`.

    Pure check tool — returns a report dict, never raises.  Only fields the
    config explicitly sets are compared; unset fields are reported as
    ``skipped``.

    Args:
        geo: Resolved geolocation (e.g. from the profile's proxy).
        config: Profile configuration to check against.

    Returns:
        Report dict with ``consistent`` (bool), ``checks`` (per-field detail),
        and ``mismatches`` (list of field names that differ).
    """
    checks: dict[str, Any] = {}
    mismatches: list[str] = []

    for field, geo_value, cfg_value in (
        ("locale", geo.locale, config.locale),
        ("timezone_id", geo.timezone_id, config.timezone),
    ):
        if cfg_value is None:
            checks[field] = {"status": "skipped", "reason": "config unset"}
            continue
        # 'auto' requests the resolved GeoIP value, not a literal persona.
        # Compare against the effective value rather than against 'auto'.
        effective = geo_value if isinstance(cfg_value, str) and cfg_value.strip().lower() == "auto" else cfg_value
        match = geo_value == effective
        checks[field] = {
            "status": "match" if match else "mismatch",
            "geo": geo_value,
            "config": cfg_value,
            "resolved": effective,
        }
        if not match:
            mismatches.append(field)

    return {
        "consistent": not mismatches,
        "country": geo.country,
        "checks": checks,
        "mismatches": mismatches,
    }


class GeoResolver:
    """Reusable GeoIP resolver — proxy, direct IP, or host IP.

    Args:
        endpoint: Geo endpoint URL.  Default ``https://ipinfo.io/json``
            (ipinfo-style ``{endpoint}/{ip}/json`` is used for
            :meth:`resolve_ip`).
        timeout_s: Per-request timeout in seconds.
        cache_ttl_s: Cache GeoIP results per target for this many seconds;
            ``0`` disables caching.
        allowed_countries: Optional ISO alpha-2 allow list; non-matching
            results raise :class:`ProxyError`.
        blocked_countries: Optional ISO alpha-2 block list.

    Raises:
        ProxyError: If ``cache_ttl_s`` is negative.
    """

    def __init__(
        self,
        *,
        endpoint: str | list[str] | None = None,
        endpoints: list[str] | None = None,
        timeout_s: float = 8.0,
        cache_ttl_s: float = 300.0,
        allowed_countries: list[str] | set[str] | tuple[str, ...] | None = None,
        blocked_countries: list[str] | set[str] | tuple[str, ...] | None = None,
    ) -> None:
        if cache_ttl_s < 0:
            raise ProxyError(
                "cache_ttl_s must be >= 0",
                details={"stage": "init", "cache_ttl_s": cache_ttl_s},
            )
        if endpoints is not None:
            raw: list[str] | str = endpoints
        elif endpoint is None:
            raw = ["https://ipinfo.io/json"]
        else:
            raw = endpoint
        if isinstance(raw, str):
            raw = [raw]
        cleaned = [str(e).strip().rstrip("/") for e in raw if str(e).strip()]
        if not cleaned:
            raise ProxyError(
                "at least one geo endpoint is required",
                details={"stage": "init"},
            )
        self._endpoints: list[str] = cleaned
        self._timeout_s: float = timeout_s
        self._cache_ttl_s: float = cache_ttl_s
        self._allowed: frozenset[str] | None = _norm_countries(allowed_countries)
        self._blocked: frozenset[str] | None = _norm_countries(blocked_countries)
        self._cache: dict[str, tuple[float, GeoInfo]] = {}
        self._session: aiohttp.ClientSession | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def resolve(self, target: ProxyConfig | None = None) -> GeoInfo:
        """Resolve geolocation for a proxy exit IP, or the host IP.

        Args:
            target: :class:`ProxyConfig` to route through, or ``None`` for
                a direct (host IP) request.

        Returns:
            Populated :class:`GeoInfo`.

        Raises:
            ProxyError: On network/HTTP/parse failure or geo-policy rejection.
        """
        cache_key = self._cache_key(target)
        if self._cache_ttl_s > 0:
            cached = self._cache.get(cache_key)
            if cached is not None and (time.time() - cached[0]) < self._cache_ttl_s:
                return cached[1]

        session = await self._get_session()
        proxy_url = proxy_auth = None
        masked: dict | None = None
        if target is not None:
            proxy_url = ProxyManager._build_proxy_url(target)
            proxy_auth = ProxyManager._build_proxy_auth(target)
            masked = {"server": proxy_url}

        data, _ = await self._fetch_with_fallback(
            session,
            [e for e in self._endpoints],
            proxy_url=proxy_url,
            proxy_auth=proxy_auth,
            masked=masked,
            stage="resolve",
        )

        geo = parse_geo_data(data, masked_proxy=masked)
        self._check_policy(geo, masked)

        if self._cache_ttl_s > 0:
            self._cache[cache_key] = (time.time(), geo)
        return geo

    async def resolve_ip(self, ip: str) -> GeoInfo:
        """Look up geolocation for an explicit IP address.

        Uses the ipinfo-style ``{endpoint}/{ip}/json`` path — endpoints that
        do not support per-IP lookup will return an HTTP error surfaced as
        :class:`ProxyError`.

        Args:
            ip: IPv4/IPv6 address string.

        Returns:
            Populated :class:`GeoInfo`.
        """
        cache_key = f"ip:{ip}"
        if self._cache_ttl_s > 0:
            cached = self._cache.get(cache_key)
            if cached is not None and (time.time() - cached[0]) < self._cache_ttl_s:
                return cached[1]

        session = await self._get_session()
        # BF-02/B-17: endpoints are full URLs (e.g. "https://ipinfo.io/json").
        # Per-IP lookup needs the bare host — strip a trailing "/json"
        # (or any last path segment that looks like a format suffix) and
        # try BOTH common provider path shapes via the fallback chain:
        #   ipinfo style:  {base}/{ip}/json
        #   ip-api style:  {base}/json/{ip}
        urls: list[str] = []
        for e in self._endpoints:
            base = e.rstrip("/")
            if base.endswith("/json"):
                base = base[: -len("/json")]
            urls.append(f"{base}/{ip}/json")
            urls.append(f"{base}/json/{ip}")
        data, _ = await self._fetch_with_fallback(
            session,
            urls,
            proxy_url=None,
            proxy_auth=None,
            masked={"ip": ip},
            stage="resolve_ip",
        )

        geo = parse_geo_data(data)
        self._check_policy(geo, {"ip": ip})

        if self._cache_ttl_s > 0:
            self._cache[cache_key] = (time.time(), geo)
        return geo

    async def resolve_many(
        self,
        targets: list[ProxyConfig | None],
        *,
        concurrency: int = 5,
    ) -> list[GeoInfo | ProxyError]:
        """Resolve multiple targets concurrently with bounded concurrency.

        Args:
            targets: List of :class:`ProxyConfig` or ``None`` (host IP).
            concurrency: Max simultaneous requests (>= 1).

        Returns:
            List aligned with ``targets``; each element is :class:`GeoInfo`
            on success or the :class:`ProxyError` raised for that target.
        """
        if concurrency < 1:
            raise ProxyError(
                "concurrency must be >= 1",
                details={"stage": "resolve_many", "concurrency": concurrency},
            )
        sem = asyncio.Semaphore(concurrency)

        async def _one(target: ProxyConfig | None) -> GeoInfo | ProxyError:
            async with sem:
                try:
                    return await self.resolve(target)
                except ProxyError as exc:
                    return exc

        return list(await asyncio.gather(*(_one(t) for t in targets)))

    async def aclose(self) -> None:
        """Close the aiohttp session and clear the cache. Idempotent."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None
        self._cache.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_key(target: ProxyConfig | None) -> str:
        if target is None:
            return "__host__"
        return f"proxy:{target.server}"

    def _check_policy(self, geo: GeoInfo, details: dict | None) -> None:
        """Raise :class:`ProxyError` when ``geo`` violates the filters."""
        if matches_geo_policy(
            geo, allowed_countries=self._allowed, blocked_countries=self._blocked
        ):
            return
        raise ProxyError(
            "geo result rejected by country policy",
            details={
                "stage": "geo_policy",
                "country": geo.country,
                "allowed": sorted(self._allowed) if self._allowed else None,
                "blocked": sorted(self._blocked) if self._blocked else None,
                **(details or {}),
            },
        )

    async def _fetch_with_fallback(
        self,
        session: aiohttp.ClientSession,
        urls: list[str],
        *,
        proxy_url: str | None,
        proxy_auth: "aiohttp.BasicAuth | None",
        masked: dict | None,
        stage: str,
    ) -> tuple[dict[str, Any], ProxyError | None]:
        """Try each URL in order; return ``(data, None)`` on first success.

        On total failure raises the last :class:`ProxyError` with an
        ``attempts`` detail listing every endpoint that failed.
        """
        errors: list[dict[str, Any]] = []
        last_exc: ProxyError | None = None
        timeout = aiohttp.ClientTimeout(total=self._timeout_s)

        for url in urls:
            try:
                async with session.get(
                    url,
                    proxy=proxy_url,
                    proxy_auth=proxy_auth,
                    timeout=timeout,
                ) as resp:
                    if resp.status != 200:
                        raise ProxyError(
                            f"geo endpoint returned HTTP {resp.status}",
                            details={"stage": stage, "url": url},
                        )
                    try:
                        data: dict[str, Any] = await resp.json(content_type=None)
                    except Exception as exc:
                        raise ProxyError(
                            "geo endpoint returned non-JSON response",
                            details={"stage": stage, "url": url, "reason": str(exc)},
                        ) from exc
                return data, None
            except ProxyError as exc:
                last_exc = exc
                errors.append({"url": url, "error": str(exc)})
                _log.debug("geo endpoint failed, trying next", url=url, error=str(exc))
            except asyncio.TimeoutError:
                last_exc = ProxyError(
                    "geo endpoint timed out",
                    details={"stage": stage, "url": url},
                )
                errors.append({"url": url, "error": "timeout"})
            except aiohttp.ClientError as exc:
                last_exc = ProxyError(
                    "geo endpoint connection error",
                    details={"stage": stage, "url": url, "reason": str(exc)},
                )
                errors.append({"url": url, "error": str(exc)})

        assert last_exc is not None
        last_exc.details["attempts"] = errors
        if masked:
            last_exc.details.update(masked)
        raise last_exc

    async def _get_session(self) -> aiohttp.ClientSession:
        """Return the shared aiohttp session, creating it lazily."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session


# ---------------------------------------------------------------------------
# Sticky geo binding + drift monitor (PH-18, N3/N4)
# ---------------------------------------------------------------------------

class StickyGeoStore:
    """Persist ``account_id → (proxy_server, geo)`` bindings (N3).

    JSON-file backed so bindings survive process restarts.  Thread/async
    safe enough for single-writer usage; corrupt files reset to empty
    with a warning.

    Args:
        path: Filesystem path for the bindings JSON file.
    """

    def __init__(self, path: str) -> None:
        from pathlib import Path

        self._path = Path(path)
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        try:
            import json

            if self._path.exists():
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._data = raw
        except Exception as exc:
            _log.warning("sticky geo store unreadable — starting empty", reason=str(exc))
            self._data = {}

    def _save(self) -> None:
        import json

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
            tmp.replace(self._path)
        except Exception as exc:
            _log.warning("sticky geo store save failed", reason=str(exc))

    def get(self, account_id: str) -> dict[str, Any] | None:
        """Return the stored binding ``{"proxy": ..., "geo": {...}}`` or None."""
        return self._data.get(account_id)

    def put(
        self,
        account_id: str,
        proxy_server: str,
        geo: GeoInfo | dict[str, Any],
    ) -> None:
        """Bind ``account_id`` to a proxy server + resolved geo."""
        if isinstance(geo, GeoInfo):
            geo_dict = geo.model_dump() if hasattr(geo, "model_dump") else geo.__dict__
        else:
            geo_dict = dict(geo)
        self._data[account_id] = {"proxy": proxy_server, "geo": geo_dict}
        self._save()

    def remove(self, account_id: str) -> bool:
        """Remove a binding; returns True if one existed."""
        existed = self._data.pop(account_id, None) is not None
        if existed:
            self._save()
        return existed


class GeoDriftMonitor:
    """Detect when a target's resolved geo changes over time (N4).

    Keeps the last resolved :class:`GeoInfo` per target key in memory;
    optionally persists to a JSON file for cross-process drift checks.
    """

    _DRIFT_FIELDS = ("country", "timezone_id", "city")

    def __init__(self, store_path: str | None = None) -> None:
        self._last: dict[str, dict[str, Any]] = {}
        self._path = store_path
        if store_path:
            self._load()

    def _load(self) -> None:
        try:
            import json
            from pathlib import Path

            p = Path(self._path)  # type: ignore[arg-type]
            if p.exists():
                raw = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._last = raw
        except Exception:
            pass

    def _save(self) -> None:
        if not self._path:
            return
        try:
            import json
            from pathlib import Path

            p = Path(self._path)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self._last, indent=2), encoding="utf-8")
            tmp.replace(p)
        except Exception as exc:
            _log.warning("geo drift store save failed", reason=str(exc))

    def check(self, target: str, geo: GeoInfo) -> dict[str, Any]:
        """Compare ``geo`` against the last seen geo for ``target``.

        Returns ``{"drifted": bool, "changes": {field: [old, new]},
        "first_seen": bool}`` and updates the stored baseline.
        """
        current = {f: getattr(geo, f, None) for f in self._DRIFT_FIELDS}
        previous = self._last.get(target)
        self._last[target] = current
        self._save()
        if previous is None:
            return {"drifted": False, "changes": {}, "first_seen": True}
        changes = {
            f: [previous.get(f), current.get(f)]
            for f in self._DRIFT_FIELDS
            if previous.get(f) != current.get(f)
        }
        return {"drifted": bool(changes), "changes": changes, "first_seen": False}
