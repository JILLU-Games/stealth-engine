"""Proxy configuration, rotation, and validation."""

from __future__ import annotations

import asyncio
import http.client
import json
import random
import socket
import ssl
import time
from typing import Any
from urllib.parse import urlsplit

import aiohttp
from pydantic import BaseModel

from .config import ProxyConfig, _split_proxy_credentials
from .exceptions import ProxyError
from .utils.logging import get_logger

_log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Static GeoIP derivation tables
# ---------------------------------------------------------------------------

# country_code -> BCP-47 locale
_COUNTRY_LOCALE: dict[str, str] = {
    "US": "en-US", "GB": "en-GB", "AU": "en-AU", "CA": "en-CA",
    "NZ": "en-NZ", "IE": "en-IE", "ZA": "en-ZA", "IN": "en-IN",
    "DE": "de-DE", "AT": "de-AT", "CH": "de-CH",
    "FR": "fr-FR", "BE": "fr-BE",
    "ES": "es-ES", "MX": "es-MX", "AR": "es-AR", "CO": "es-CO",
    "IT": "it-IT",
    "PT": "pt-PT", "BR": "pt-BR",
    "NL": "nl-NL",
    "PL": "pl-PL",
    "RU": "ru-RU",
    "TR": "tr-TR",
    "JP": "ja-JP",
    "CN": "zh-CN", "TW": "zh-TW",
    "KR": "ko-KR",
    "BD": "bn-BD",
    "PK": "ur-PK",
    "SE": "sv-SE",
    "NO": "nb-NO",
    "DK": "da-DK",
    "FI": "fi-FI",
    "HU": "hu-HU",
    "CZ": "cs-CZ",
    "RO": "ro-RO",
    "SK": "sk-SK",
    "BG": "bg-BG",
    "HR": "hr-HR",
    "UA": "uk-UA",
    "GR": "el-GR",
    "TH": "th-TH",
    "VN": "vi-VN",
    "ID": "id-ID",
    "MY": "ms-MY",
    "PH": "en-PH",
    "SA": "ar-SA", "AE": "ar-AE", "EG": "ar-EG",
    "IL": "he-IL",
    "NG": "en-NG",
    "KE": "en-KE",
    "GH": "en-GH",
}

# country_code -> ISO 4217 currency
_COUNTRY_CURRENCY: dict[str, str] = {
    "US": "USD", "AU": "AUD", "CA": "CAD", "NZ": "NZD", "SG": "SGD",
    "HK": "HKD", "MX": "MXN", "CO": "COP", "AR": "ARS",
    "GB": "GBP", "IE": "EUR",
    "DE": "EUR", "AT": "EUR", "BE": "EUR", "FR": "EUR", "ES": "EUR",
    "IT": "EUR", "PT": "EUR", "NL": "EUR", "FI": "EUR", "GR": "EUR",
    "CH": "CHF",
    "SE": "SEK", "NO": "NOK", "DK": "DKK",
    "PL": "PLN", "CZ": "CZK", "HU": "HUF", "RO": "RON",
    "RU": "RUB", "UA": "UAH",
    "TR": "TRY",
    "JP": "JPY",
    "CN": "CNY", "TW": "TWD",
    "KR": "KRW",
    "IN": "INR", "BD": "BDT", "PK": "PKR",
    "BR": "BRL",
    "ZA": "ZAR",
    "NG": "NGN", "KE": "KES", "GH": "GHS",
    "SA": "SAR", "AE": "AED", "EG": "EGP",
    "IL": "ILS",
    "TH": "THB", "VN": "VND", "ID": "IDR", "MY": "MYR", "PH": "PHP",
    "BG": "BGN", "HR": "HRK", "SK": "EUR",
}

_FALLBACK_LOCALE = "en-US"
_FALLBACK_CURRENCY = "USD"


def parse_geo_data(
    data: dict[str, Any], *, masked_proxy: dict | None = None
) -> "GeoInfo":
    """Parse a geo-endpoint JSON payload into a :class:`GeoInfo`.

    Shared by :class:`ProxyManager` and :class:`~stealth_engine.geo.GeoResolver`.

    Args:
        data: Parsed JSON dict from the geo endpoint.
        masked_proxy: Optional credential-redacted proxy dict included in
            error details.

    Returns:
        Populated :class:`GeoInfo`.

    Raises:
        ProxyError: If required fields are missing or empty.
    """
    # ip-api.com shape: status/countryCode/query/lat/lon/regionName/city
    if "countryCode" in data or data.get("status") == "success":
        ip = str(data.get("query", "")).strip()
        country = str(data.get("countryCode", "")).strip().upper()
        timezone_id = str(data.get("timezone", "")).strip()
        region = data.get("regionName")
        city = data.get("city")
        lat_raw, lon_raw = data.get("lat"), data.get("lon")
    else:
        # ipinfo.io shape: ip/country/timezone/region/city/loc ("lat,lon")
        ip = str(data.get("ip", "")).strip()
        country = str(data.get("country", "")).strip().upper()
        timezone_id = str(data.get("timezone", "")).strip()
        region = data.get("region")
        city = data.get("city")
        lat_raw = lon_raw = None
        loc = data.get("loc")
        if isinstance(loc, str) and "," in loc:
            try:
                lat_raw, lon_raw = (float(p) for p in loc.split(",", 1))
            except ValueError:
                lat_raw = lon_raw = None

    details = {"stage": "resolve_geo"}
    if masked_proxy is not None:
        details["proxy"] = masked_proxy

    if not ip:
        raise ProxyError("geo response missing ip field", details=details)
    if not country:
        raise ProxyError("geo response missing country field", details=details)
    if not timezone_id:
        raise ProxyError("geo response missing timezone field", details=details)

    locale: str = _COUNTRY_LOCALE.get(country, _FALLBACK_LOCALE)
    currency: str = _COUNTRY_CURRENCY.get(country, _FALLBACK_CURRENCY)

    def _f(v: Any) -> float | None:
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    return GeoInfo(
        ip=ip,
        country=country,
        timezone_id=timezone_id,
        locale=locale,
        currency=currency,
        region=str(region) if region else None,
        city=str(city) if city else None,
        latitude=_f(lat_raw),
        longitude=_f(lon_raw),
    )


class GeoInfo(BaseModel):
    """Geolocation metadata derived from a proxy exit IP.

    Attributes:
        ip: Public IP address seen by the endpoint.
        country: ISO 3166-1 alpha-2 country code (e.g. ``"US"``).
        timezone_id: IANA timezone string (e.g. ``"America/New_York"``).
        locale: BCP-47 locale tag derived from country (e.g. ``"en-US"``).
        currency: ISO 4217 currency code derived from country (e.g. ``"USD"``).
    """

    ip: str
    country: str
    timezone_id: str
    locale: str
    currency: str
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ProxyManager:
    """Manages a pool of proxies: health-checking, geo-resolution, and rotation.

    All network calls share a single ``aiohttp.ClientSession`` created lazily
    on the first request.  The session is closed by calling :meth:`aclose`.

    Args:
        proxies: Non-empty list of :class:`~stealth_engine.config.ProxyConfig`
            instances.
        geo_endpoint: URL used to resolve the exit IP's geolocation.
            Must respond with JSON containing at least ``ip``, ``country``,
            and ``timezone``.
        timeout_s: Per-request network timeout in seconds.
        seed: When set, proxy rotation order is deterministic across runs.
        allowed_countries: Optional list of ISO alpha-2 codes; when set,
            only proxies resolving to these countries are eligible.
        blocked_countries: Optional list of ISO alpha-2 codes; proxies
            resolving to these countries are skipped.
        cache_ttl_s: When > 0, GeoIP results are cached per proxy server
            URL for this many seconds (0 disables caching).
        geo_retries: Extra attempts for transient geo-endpoint failures
            inside :meth:`resolve_geo` (0 = single attempt).
        health_threshold_ms: Max acceptable geo round-trip latency for
            :meth:`pick_healthy` candidates.

    Raises:
        ProxyError: If ``proxies`` is empty or numeric params are invalid.
    """

    def __init__(
        self,
        proxies: list[ProxyConfig],
        *,
        geo_endpoint: str = "https://ipinfo.io/json",
        timeout_s: float = 8.0,
        seed: int | None = None,
        allowed_countries: list[str] | None = None,
        blocked_countries: list[str] | None = None,
        cache_ttl_s: float = 0.0,
        geo_retries: int = 0,
        health_threshold_ms: float = 5000.0,
    ) -> None:
        if not proxies:
            raise ProxyError(
                "proxies list must not be empty",
                details={"stage": "init", "reason": "empty proxy list"},
            )
        if geo_retries < 0:
            raise ProxyError(
                "geo_retries must be >= 0",
                details={"stage": "init", "geo_retries": geo_retries},
            )
        if health_threshold_ms <= 0:
            raise ProxyError(
                "health_threshold_ms must be > 0",
                details={"stage": "init", "health_threshold_ms": health_threshold_ms},
            )

        self._proxies: list[ProxyConfig] = list(proxies)
        self._geo_endpoint: str = geo_endpoint
        self._timeout_s: float = timeout_s
        self._session: aiohttp.ClientSession | None = None
        self._lock: asyncio.Lock | None = None
        self._geo_retries: int = geo_retries
        self._health_threshold_ms: float = health_threshold_ms
        self._allowed_countries: frozenset[str] | None = (
            frozenset(c.upper() for c in allowed_countries)
            if allowed_countries
            else None
        )
        self._blocked_countries: frozenset[str] | None = (
            frozenset(c.upper() for c in blocked_countries)
            if blocked_countries
            else None
        )
        if cache_ttl_s < 0:
            raise ProxyError(
                "cache_ttl_s must be >= 0",
                details={"stage": "init", "cache_ttl_s": cache_ttl_s},
            )
        self._cache_ttl_s: float = cache_ttl_s
        self._geo_cache: dict[str, tuple[float, GeoInfo]] = {}

        if seed is not None:
            self._rng: random.Random = random.Random(seed)
        else:
            self._rng = random.Random()

    def _get_lock(self) -> asyncio.Lock:
        """Return the instance asyncio.Lock, creating it lazily if needed.

        The lock is created on first call, which always happens inside an
        async method where an event loop is guaranteed to be running.

        Returns:
            The instance :class:syncio.Lock.
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def resolve_geo(self, proxy: ProxyConfig) -> GeoInfo:
        """Resolve geolocation for the exit IP of the given proxy.

        Makes a GET request to the configured ``geo_endpoint`` routed
        through ``proxy``, parses the JSON response, and derives locale
        and currency from the returned country code.

        Args:
            proxy: Proxy to route the request through.

        Returns:
            Populated :class:`GeoInfo` instance.

        Raises:
            ProxyError: On timeout, HTTP error, connection failure, or
                malformed / missing fields in the JSON response.
        """
        # BF-03/B-21: key by masked server — proxy.server may embed
        # user:pass credentials which must not sit in the cache dict.
        cache_key = str(self.mask(proxy)["server"])
        if self._cache_ttl_s > 0:
            cached = self._geo_cache.get(cache_key)
            if cached is not None and (time.time() - cached[0]) < self._cache_ttl_s:
                return cached[1]

        is_socks = proxy.server.startswith(("socks5://", "socks4://"))
        # aiohttp's proxy= argument speaks HTTP CONNECT, never SOCKS.
        session = None if is_socks else await self._get_session()
        proxy_url = self._build_proxy_url(proxy)
        proxy_auth = self._build_proxy_auth(proxy)
        timeout = aiohttp.ClientTimeout(total=self._timeout_s)
        masked = self.mask(proxy)

        data: dict[str, Any] | None = None
        last_exc: ProxyError | None = None
        for attempt in range(self._geo_retries + 1):
            try:
                if is_socks:
                    # Native SOCKS4a/SOCKS5 handshake; TLS peer validation
                    # happens inside _fetch_geo_via_socks. No optional deps.
                    data = await asyncio.wait_for(
                        asyncio.to_thread(self._fetch_geo_via_socks, proxy),
                        timeout=self._timeout_s,
                    )
                    break
                assert session is not None
                async with session.get(
                    self._geo_endpoint,
                    proxy=proxy_url,
                    proxy_auth=proxy_auth,
                    timeout=timeout,
                ) as resp:
                    if resp.status != 200:
                        raise ProxyError(
                            f"geo endpoint returned HTTP {resp.status}",
                            details={
                                "stage": "resolve_geo",
                                "proxy": masked,
                                "attempt": attempt + 1,
                            },
                        )
                    try:
                        data = await resp.json(content_type=None)
                    except Exception as exc:
                        raise ProxyError(
                            "geo endpoint returned non-JSON response",
                            details={
                                "stage": "resolve_geo",
                                "proxy": masked,
                                "reason": str(exc),
                                "attempt": attempt + 1,
                            },
                        ) from exc
                break
            except ProxyError as exc:
                last_exc = exc
                if attempt < self._geo_retries:
                    await asyncio.sleep(0.3 * (attempt + 1))
                    continue
                raise
            except asyncio.TimeoutError as exc:
                last_exc = ProxyError(
                    "geo endpoint timed out",
                    details={
                        "stage": "resolve_geo",
                        "proxy": masked,
                        "attempt": attempt + 1,
                    },
                )
                if attempt < self._geo_retries:
                    await asyncio.sleep(0.3 * (attempt + 1))
                    continue
                raise last_exc from exc
            except aiohttp.ClientError as exc:
                last_exc = ProxyError(
                    "geo endpoint connection error",
                    details={
                        "stage": "resolve_geo",
                        "proxy": masked,
                        "reason": str(exc),
                        "attempt": attempt + 1,
                    },
                )
                if attempt < self._geo_retries:
                    await asyncio.sleep(0.3 * (attempt + 1))
                    continue
                raise last_exc from exc
            except Exception as exc:
                # BF-03/B-09: wrap unexpected errors so callers always
                # see ProxyError.  CancelledError is BaseException and
                # propagates untouched.
                last_exc = ProxyError(
                    "geo endpoint unexpected error",
                    details={
                        "stage": "resolve_geo",
                        "proxy": masked,
                        "reason": str(exc),
                        "attempt": attempt + 1,
                    },
                )
                if attempt < self._geo_retries:
                    await asyncio.sleep(0.3 * (attempt + 1))
                    continue
                raise last_exc from exc

        assert data is not None  # loop either breaks with data or raises

        geo = self._parse_geo(data, proxy)
        if self._cache_ttl_s > 0:
            self._geo_cache[cache_key] = (time.time(), geo)
        return geo

    def _geo_allowed(self, geo: GeoInfo) -> bool:
        """Return True when ``geo.country`` passes the configured filters."""
        country = geo.country.upper()
        if self._allowed_countries is not None and country not in self._allowed_countries:
            return False
        if self._blocked_countries is not None and country in self._blocked_countries:
            return False
        return True

    async def health_check(self, proxy: ProxyConfig) -> float:
        """Measure proxy latency by timing a full :meth:`resolve_geo` call.

        Args:
            proxy: Proxy to check.

        Returns:
            Round-trip latency in milliseconds, rounded to 2 decimal places.

        Raises:
            ProxyError: If the proxy is unreachable or returns invalid data.
        """
        t0 = time.perf_counter()
        await self.resolve_geo(proxy)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        _log.debug(
            "proxy health_check",
            proxy_server=self.mask(proxy)["server"],
            latency_ms=latency_ms,
        )
        return latency_ms

    async def pick_healthy(self) -> tuple[ProxyConfig, GeoInfo]:
        """Return the first proxy that passes a health check under
        ``health_threshold_ms``.

        The candidate list is shuffled using the instance RNG (seeded or
        random).  The method is safe to call concurrently; an
        :class:`asyncio.Lock` serialises rotation access.

        Returns:
            A ``(ProxyConfig, GeoInfo)`` tuple for the selected proxy.

        Raises:
            ProxyError: If all proxies fail the health check.
        """
        async with self._get_lock():
            # Shuffle and copy both happen under the lock so self._rng is
            # never accessed concurrently from two pick_healthy() calls.
            self._rng.shuffle(self._proxies)
            candidates = list(self._proxies)

        tried: list[dict] = []
        for proxy in candidates:
            try:
                t0 = time.perf_counter()
                geo = await self.resolve_geo(proxy)
                latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                if latency_ms < self._health_threshold_ms and self._geo_allowed(geo):
                    _log.info(
                        "picked healthy proxy",
                        proxy_server=self.mask(proxy)["server"],
                        country=geo.country,
                        latency_ms=latency_ms,
                    )
                    return proxy, geo
                tried.append(self.mask(proxy))
            except ProxyError:
                tried.append(self.mask(proxy))

        raise ProxyError(
            "all proxies failed health check",
            details={"stage": "pick_healthy", "tried": tried},
        )

    def to_playwright(self, proxy: ProxyConfig) -> dict[str, str]:
        """Convert a :class:`ProxyConfig` to a Playwright proxy dict.

        Only includes ``username`` and ``password`` keys when the proxy
        actually has credentials — omits them entirely otherwise.

        Args:
            proxy: Proxy configuration to convert.

        Returns:
            Dict suitable for Playwright's ``proxy=`` argument with
            ``"server"`` always present, and ``"username"`` /
            ``"password"`` included only when set.
        """
        server, embedded_username, embedded_password = self._proxy_parts(proxy)
        result: dict[str, str] = {"server": server}
        username = proxy.username if proxy.username is not None else embedded_username
        password = proxy.password if proxy.password is not None else embedded_password
        if username is not None:
            result["username"] = username
        if password is not None:
            result["password"] = password
        return result

    def mask(self, proxy: ProxyConfig) -> dict[str, str | None]:
        """Return a safe, loggable representation of a proxy with credentials redacted.

        Args:
            proxy: Proxy configuration to mask.

        Returns:
            Dict with ``"server"`` intact, ``"username"`` as-is (not secret),
            and ``"password"`` replaced by ``"***"`` when present.
        """
        server, embedded_username, embedded_password = self._proxy_parts(proxy)
        return {
            "server": server,
            "username": (
                proxy.username if proxy.username is not None else embedded_username
            ),
            "password": (
                "***"
                if proxy.password is not None or embedded_password is not None
                else None
            ),
        }

    async def aclose(self) -> None:
        """Close the underlying aiohttp session if one was created.

        Safe to call multiple times (idempotent).
        """
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None
            _log.debug("ProxyManager session closed")
        self._geo_cache.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_geo_via_socks(self, proxy: ProxyConfig) -> dict[str, Any]:
        """GET GeoIP through a SOCKS5 or SOCKS4a TCP tunnel in a worker thread.

        Uses target hostname at the proxy (no local target DNS), validates
        HTTPS certificates, limits response bytes and avoids credential-bearing
        exceptions. This is only the SOCKS GeoIP/health request transport.
        """
        endpoint = urlsplit(self._geo_endpoint)
        if endpoint.scheme not in ("http", "https") or not endpoint.hostname:
            raise ProxyError("unsupported GeoIP endpoint", details={"stage": "resolve_geo"})
        proxy_url, embedded_user, embedded_pass = self._proxy_parts(proxy)
        address = urlsplit(proxy_url)
        username = proxy.username if proxy.username is not None else embedded_user
        password = proxy.password if proxy.password is not None else embedded_pass
        host = endpoint.hostname
        port = endpoint.port or (443 if endpoint.scheme == "https" else 80)
        masked = self.mask(proxy)

        def recv_exact(conn: socket.socket, size: int) -> bytes:
            result = bytearray()
            while len(result) < size:
                chunk = conn.recv(size - len(result))
                if not chunk:
                    raise OSError("SOCKS peer closed connection")
                result.extend(chunk)
            return bytes(result)

        try:
            with socket.create_connection((address.hostname, address.port), timeout=self._timeout_s) as sock:
                sock.settimeout(self._timeout_s)
                if address.scheme == "socks5":
                    use_auth = username is not None or password is not None
                    sock.sendall(b"\x05\x01" + (b"\x02" if use_auth else b"\x00"))
                    selection = recv_exact(sock, 2)
                    if selection[0] != 5 or selection[1] != (2 if use_auth else 0):
                        raise OSError("SOCKS5 method rejected")
                    if use_auth:
                        u = (username or "").encode("utf-8")
                        pw = (password or "").encode("utf-8")
                        if not 1 <= len(u) <= 255 or len(pw) > 255:
                            raise OSError("invalid SOCKS5 credential length")
                        sock.sendall(b"\x01" + bytes([len(u)]) + u + bytes([len(pw)]) + pw)
                        if recv_exact(sock, 2) != b"\x01\x00":
                            raise OSError("SOCKS5 authentication rejected")
                    # Domain name always sent for remote DNS (IPv4/IPv6 included).
                    target = host.encode("idna")
                    if len(target) > 255:
                        raise OSError("target hostname too long")
                    sock.sendall(b"\x05\x01\x00\x03" + bytes([len(target)]) + target + port.to_bytes(2, "big"))
                    response = recv_exact(sock, 4)
                    if response[:3] != b"\x05\x00\x00":
                        raise OSError("SOCKS5 connect rejected")
                    addr_type = response[3]
                    if addr_type == 1:
                        recv_exact(sock, 4)
                    elif addr_type == 4:
                        recv_exact(sock, 16)
                    elif addr_type == 3:
                        recv_exact(sock, recv_exact(sock, 1)[0])
                    else:
                        raise OSError("unknown SOCKS5 address type")
                    recv_exact(sock, 2)
                elif address.scheme == "socks4":
                    if password:
                        raise OSError("SOCKS4 does not support password authentication")
                    user = (username or "").encode("utf-8")
                    if b"\x00" in user:
                        raise OSError("invalid SOCKS4 user ID")
                    target = host.encode("idna")
                    if b"\x00" in target:
                        raise OSError("invalid SOCKS4 hostname")
                    # SOCKS4a avoids resolving target DNS on the client host.
                    sock.sendall(b"\x04\x01" + port.to_bytes(2, "big") + b"\x00\x00\x00\x01" + user + b"\x00" + target + b"\x00")
                    reply = recv_exact(sock, 8)
                    if reply[0] != 0 or reply[1] != 90:
                        raise OSError("SOCKS4 connect rejected")
                else:
                    raise OSError("unsupported SOCKS protocol")

                conn = sock
                if endpoint.scheme == "https":
                    conn = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
                path = endpoint.path or "/"
                if endpoint.query:
                    path += "?" + endpoint.query
                host_header = host if port in (80, 443) else f"{host}:{port}"
                conn.sendall((f"GET {path} HTTP/1.1\r\nHost: {host_header}\r\nAccept: application/json\r\nAccept-Encoding: identity\r\nConnection: close\r\n\r\n").encode("ascii"))
                response = http.client.HTTPResponse(conn)
                response.begin()
                if response.status != 200:
                    raise ProxyError("geo endpoint returned HTTP " + str(response.status), details={"stage": "resolve_geo", "proxy": masked})
                payload = response.read(1024 * 1024 + 1)
                if len(payload) > 1024 * 1024:
                    raise ProxyError("geo endpoint response too large", details={"stage": "resolve_geo", "proxy": masked})
                try:
                    data = json.loads(payload.decode("utf-8"))
                except (UnicodeError, ValueError):
                    raise ProxyError("geo endpoint returned non-JSON response", details={"stage": "resolve_geo", "proxy": masked}) from None
                if not isinstance(data, dict):
                    raise ProxyError("geo endpoint returned non-object JSON", details={"stage": "resolve_geo", "proxy": masked})
                return data
        except ProxyError:
            raise
        except (OSError, ssl.SSLError, ValueError, http.client.HTTPException) as exc:
            raise ProxyError(
                "SOCKS proxy GeoIP request failed",
                details={"stage": "resolve_geo", "proxy": masked, "reason_type": type(exc).__name__},
            ) from None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Return the shared aiohttp session, creating it lazily if needed.

        Returns:
            The open :class:`aiohttp.ClientSession` instance.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    @staticmethod
    def _build_proxy_url(proxy: ProxyConfig) -> str:
        """Return the proxy server URL with NO credentials embedded.

        Credentials are passed separately via :meth:`_build_proxy_auth` to
        prevent the password appearing in any URL string that aiohttp might
        log on connection errors.

        Args:
            proxy: Source proxy configuration.

        Returns:
            Credential-free proxy URL string.
        """
        return ProxyManager._proxy_parts(proxy)[0]

    @staticmethod
    def _build_proxy_auth(proxy: ProxyConfig) -> "aiohttp.BasicAuth | None":
        """Return an :class:`aiohttp.BasicAuth` object when credentials are present.

        Args:
            proxy: Source proxy configuration.

        Returns:
            :class:`aiohttp.BasicAuth` if both username and password are set;
            ``None`` otherwise.
        """
        _, embedded_username, embedded_password = ProxyManager._proxy_parts(proxy)
        username = proxy.username if proxy.username is not None else embedded_username
        password = proxy.password if proxy.password is not None else embedded_password
        if username is not None and password is not None:
            return aiohttp.BasicAuth(username, password)
        return None

    @staticmethod
    def _proxy_parts(proxy: ProxyConfig) -> tuple[str, str | None, str | None]:
        """Separate URL credentials from the server address."""
        return _split_proxy_credentials(proxy.server)

    def _parse_geo(self, data: dict[str, Any], proxy: ProxyConfig) -> GeoInfo:
        """Parse ipinfo.io JSON into a :class:`GeoInfo` instance.

        Args:
            data: Parsed JSON dict from the geo endpoint.
            proxy: Source proxy (used in error details only, via mask).

        Returns:
            Populated :class:`GeoInfo`.

        Raises:
            ProxyError: If required fields are missing or empty.
        """
        return parse_geo_data(data, masked_proxy=self.mask(proxy))


# ---------------------------------------------------------------------------
# Proxy pool file import (PH-18, N1)
# ---------------------------------------------------------------------------

def _parse_proxy_line(line: str, lineno: int) -> ProxyConfig:
    """Parse one proxy line into a :class:`ProxyConfig`.

    Supported formats (whitespace-separated fields, ``#`` comments, blank
    lines skipped by caller):

    - ``scheme://user:pass@host:port``
    - ``user:pass@host:port``        (defaults to http://)
    - ``host:port:user:pass``        (common provider export format)
    - ``host:port``                  (no auth)
    - ``scheme://host:port``

    Args:
        line: Raw line content (already stripped).
        lineno: 1-based line number for error reporting.

    Returns:
        Validated :class:`ProxyConfig`.

    Raises:
        ProxyError: If the line cannot be parsed.
    """
    def _err(msg: str) -> ProxyError:
        # Neither error details nor exception chain may expose credentials.
        return ProxyError(
            f"proxy file line {lineno}: {msg}",
            details={"stage": "load_proxies", "line": lineno},
        )

    line = line.strip()
    if "://" in line:
        # scheme://[user:pass@]host:port
        try:
            return ProxyConfig(server=line)
        except Exception as exc:
            raise _err("invalid URL proxy address") from None

    if "@" in line:
        # user:pass@host:port — embed credentials into a URL.
        creds, _, hostport = line.partition("@")
        user, _, pw = creds.partition(":")
        if not user or not hostport:
            raise _err("malformed credentials@host:port")
        from urllib.parse import quote
        server = f"http://{quote(user, safe='')}:{quote(pw, safe='')}@{hostport}"
        try:
            return ProxyConfig(server=server)
        except Exception as exc:
            raise _err("invalid credentialed proxy address") from None

    parts = line.split(":")
    if len(parts) == 2:
        host, port = parts
        server = f"http://{host}:{port}"
    elif len(parts) == 4:
        host, port, user, pw = parts
        from urllib.parse import quote
        server = (
            f"http://{quote(user, safe='')}:{quote(pw, safe='')}"
            f"@{host}:{port}"
        )
    else:
        raise _err(
            "expected host:port[:user:pass], user:pass@host:port, "
            "or scheme:// URL"
        )
    try:
        return ProxyConfig(server=server)
    except Exception as exc:
        raise _err("invalid proxy address") from None


def load_proxies(path: str) -> list[ProxyConfig]:
    """Load a proxy pool from a text file (PH-18, N1).

    One proxy per line; ``#`` comments and blank lines ignored.  See
    :func:`_parse_proxy_line` for accepted formats.

    Args:
        path: Filesystem path to the proxy list file.

    Returns:
        List of validated :class:`ProxyConfig` objects.

    Raises:
        ProxyError: If the file is missing, empty, or any line fails to
            parse (error includes the 1-based line number).
    """
    from pathlib import Path

    p = Path(path)
    if not p.exists():
        raise ProxyError(
            f"proxy file not found: {path}",
            details={"stage": "load_proxies", "path": str(p)},
        )
    proxies: list[ProxyConfig] = []
    errors: list[str] = []
    for lineno, raw in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            proxies.append(_parse_proxy_line(line, lineno))
        except ProxyError as exc:
            errors.append(str(exc))
    if errors:
        raise ProxyError(
            f"{len(errors)} invalid proxy line(s) in {path}",
            details={"stage": "load_proxies", "errors": errors[:10]},
        )
    if not proxies:
        raise ProxyError(
            f"proxy file contains no proxies: {path}",
            details={"stage": "load_proxies", "path": str(p)},
        )
    return proxies
