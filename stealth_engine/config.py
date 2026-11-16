"""Configuration models and defaults for the stealth engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _split_proxy_credentials(server: str) -> tuple[str, str | None, str | None]:
    parsed = urlsplit(server)
    username = unquote(parsed.username) if parsed.username is not None else None
    password = unquote(parsed.password) if parsed.password is not None else None
    safe_server = urlunsplit(
        (parsed.scheme, parsed.netloc.rsplit("@", 1)[-1], parsed.path, parsed.query, parsed.fragment)
    )
    return safe_server, username, password


class ProxyConfig(BaseModel):
    """Proxy server connection parameters.

    Attributes:
        server: Full proxy URL including scheme and port.
        username: Optional authentication username.
        password: Optional authentication password.
    """

    # Prevent pydantic ValidationError output from echoing credentialed URLs.
    model_config = ConfigDict(str_strip_whitespace=True, hide_input_in_errors=True)

    server: str
    username: str | None = None
    password: str | None = None

    @field_validator("server")
    @classmethod
    def _validate_server(cls, v: str) -> str:
        """Ensure server URL uses an accepted scheme.

        Args:
            v: Raw server string.

        Returns:
            Validated server string.

        Raises:
            ValueError: If the scheme is not one of the accepted proxy schemes.
        """
        accepted = ("http://", "https://", "socks5://", "socks5h://", "socks4://")
        if not v.startswith(accepted):
            raise ValueError("proxy server requires http(s):// or socks4/5://")
        try:
            parsed = urlsplit(v)
            hostname = parsed.hostname
            port = parsed.port  # raises on invalid/non-numeric/out-of-range ports
        except ValueError:
            raise ValueError("proxy server has invalid host or port") from None
        if (
            not hostname or port is None or port < 1
            or any(ch.isspace() for ch in v)
            or parsed.path or parsed.query or parsed.fragment
            or any(ch in hostname for ch in "/?#@")
        ):
            raise ValueError("proxy server requires a valid host and port without path/query")
        # Maintain the established socks5h alias contract for downstream engines.
        if parsed.scheme == "socks5h":
            return "socks5://" + v[len("socks5h://"):]
        return v


class ProfileConfig(BaseModel):
    """Full configuration for a single stealth browser profile.

    Attributes:
        profile_name: Unique human-readable identifier for this profile.
        os: Target operating system persona for fingerprint generation.
        user_data_dir: Filesystem path for the isolated browser profile directory.
        proxy: Optional proxy settings; None means direct connection.
        geoip: When True, timezone/locale/WebRTC are derived from the proxy GeoIP.
        seed: Integer seed for deterministic identity generation; None is random.
        headless: Run the browser without a visible window when True.
        locale: BCP-47 locale tag override (e.g. "en-US"); ``"auto"`` derives
            it from GeoIP at launch; None defers to GeoIP/seeds.
        timezone: IANA timezone override (e.g. "America/New_York"); ``"auto"``
            derives it from GeoIP at launch; None defers to GeoIP/seeds.
        disable_ipv6: When True, sets Firefox pref
            ``network.dns.disableIPv6`` to prevent IPv6 leaks around proxies.
        proxy_remote_dns: When True (default) and the proxy scheme is SOCKS,
            sets ``network.proxy.socks_remote_dns`` so DNS resolves through
            the proxy instead of the host resolver.
        webgl_config: Optional ``(vendor, renderer)`` tuple forwarded to
            camoufox ``webgl_config`` (PH-14). Requires ``os`` to be set.
        fonts: Optional explicit font list forwarded to camoufox ``fonts``
            (PH-14).
        custom_fonts_only: When True with ``fonts``, restrict rendering to
            only the listed fonts.
        screen_bounds: Optional ``(min_w, max_w, min_h, max_h)`` bounds for
            fingerprint screen generation, forwarded as camoufox ``Screen``
            (PH-14).
        hardware_concurrency: Optional ``navigator.hardwareConcurrency``
            override forwarded via camoufox ``config`` (PH-14).
        seed_localstorage: When True, an init script seeds plausible
            ``localStorage`` keys on every origin so storage isn't empty
            (empty storage is a bot signal) — PH-16.
        fingerprint_diversity: When True, each launch derives a unique
            identity from ``seed`` + a per-launch salt — same profile gets
            a *different* fingerprint every launch (anti-linking) at the
            cost of losing seed reproducibility — PH-17.
        record_har_path: Optional HAR recording path (PH-19, M3). Relative
            paths resolve under the profile directory. Content controlled
            by ``record_har_content``.
        record_har_content: Optional HAR content mode — ``"omit"`` (default
            playwright), ``"embed"``, or ``"attach"``.
        record_video_dir: Optional directory for session video recording
            (PH-19, M3). Relative paths resolve under the profile dir.
        js_noise: Opt-in experimental JS-level canvas/WebGL readback noise
            (PH-20, G1). camoufox adds no canvas noise upstream — this
            patches ``toDataURL``/``getImageData``/``readPixels`` with
            deterministic per-seed noise via init script.  **Trade-off:**
            JS-level patching is detectable by sophisticated probes —
            enable only when canvas uniqueness matters more than patch
            detectability.
        extra_headers: Additional HTTP headers injected into every request.
        log_level: Minimum loguru log level for this profile's operations.
        schema_version: Config schema version for forward-compatibility tracking.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    profile_name: str
    os: Literal["windows", "macos", "linux"] = "windows"
    user_data_dir: str
    proxy: ProxyConfig | None = None
    target_ip: str | None = None
    geoip: bool = True
    seed: int | None = None
    headless: bool = True
    locale: str | None = None
    timezone: str | None = None
    disable_ipv6: bool = False
    proxy_remote_dns: bool = True
    webgl_config: tuple[str, str] | None = None
    fonts: list[str] | None = None
    custom_fonts_only: bool = False
    screen_bounds: tuple[int, int, int, int] | None = None
    hardware_concurrency: int | None = None
    seed_localstorage: bool = False
    fingerprint_diversity: bool = False
    record_har_path: str | None = None
    record_har_content: str | None = None
    record_video_dir: str | None = None
    js_noise: bool = False
    extra_headers: dict[str, str] = Field(default_factory=dict)
    log_level: str = "INFO"
    schema_version: str = "1"

    @field_validator("profile_name", "user_data_dir")
    @classmethod
    def _reject_empty_strings(cls, v: str) -> str:
        """Strip whitespace and reject blank values.

        Args:
            v: Field value after stripping.

        Returns:
            Stripped, non-empty string.

        Raises:
            ValueError: If the stripped value is empty.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field must not be empty or whitespace-only.")
        return stripped

    @field_validator("seed")
    @classmethod
    def _validate_seed(cls, v: int | None) -> int | None:
        """Ensure seed is non-negative when provided.

        Args:
            v: Seed value or None.

        Returns:
            Validated seed value.

        Raises:
            ValueError: If seed is negative.
        """
        if v is not None and v < 0:
            raise ValueError(f"seed must be >= 0; got {v}")
        return v

    @field_validator("extra_headers")
    @classmethod
    def _validate_extra_headers(cls, v: dict[str, str]) -> dict[str, str]:
        """Ensure all header keys and values are non-empty strings.

        Args:
            v: Raw extra_headers mapping.

        Returns:
            Validated mapping.

        Raises:
            ValueError: If any key is empty or any value is not a string.
        """
        for key, value in v.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(
                    f"extra_headers keys must be non-empty strings; got {key!r}"
                )
            if not isinstance(value, str):
                raise ValueError(
                    f"extra_headers values must be strings; got {value!r} for key {key!r}"
                )
        return v

    def to_public_dict(self) -> dict:
        """Return a serialisable representation with proxy secrets redacted.

        Excludes the raw proxy block and replaces username/password with
        ``"***"`` to prevent accidental secret exposure in logs or exports.

        Returns:
            Dict containing all fields except a raw proxy; proxy credentials
            are replaced with ``"***"`` if a proxy is configured.
        """
        base = self.model_dump(exclude={"proxy"})
        if self.proxy is not None:
            server, embedded_username, embedded_password = _split_proxy_credentials(
                self.proxy.server
            )
            base["proxy"] = {
                "server": server,
                "username": (
                    "***"
                    if self.proxy.username is not None or embedded_username is not None
                    else None
                ),
                "password": (
                    "***"
                    if self.proxy.password is not None or embedded_password is not None
                    else None
                ),
            }
        else:
            base["proxy"] = None
        return base

    # ------------------------------------------------------------------
    # File serialisation (Feature Y: JSON/YAML import-export)
    # ------------------------------------------------------------------

    def _export_data(self, include_secrets: bool) -> dict:
        """Prepare an export without altering this in-memory configuration.

        A default export omits proxy authentication and redacts sensitive
        headers. The loaded default export requires the user to provide
        secrets again; use include_secrets=True only for private backups.
        """
        data = self.model_dump(mode="json")
        if include_secrets:
            return data
        if data["proxy"] is not None:
            safe_server, _, _ = _split_proxy_credentials(data["proxy"]["server"])
            data["proxy"]["server"] = safe_server
            data["proxy"]["username"] = None
            data["proxy"]["password"] = None
        for name in list(data.get("extra_headers", {})):
            if name.lower() in {"authorization", "proxy-authorization", "cookie", "set-cookie", "x-api-key", "x-auth-token"}:
                data["extra_headers"][name] = "***"
        return data

    @staticmethod
    def _write_private_export(path: str | Path, payload: str) -> None:
        """Write without exposing a world-readable intermediate file.

        Create an exclusive 0600 file beside the destination and replace it
        atomically. Windows NTFS ACL guarantees still require live validation.
        """
        import os
        import tempfile

        p = Path(path)
        tmp_path = None
        try:
            fd, name = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent))
            tmp_path = Path(name)
            try:
                if hasattr(os, "fchmod"):
                    os.fchmod(fd, 0o600)
                else:
                    os.chmod(tmp_path, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
                    out.write(payload)
            except BaseException:
                # fdopen owns fd if it was reached; avoid replacing a failed write.
                try:
                    os.close(fd)
                except OSError:
                    pass
                raise
            os.replace(tmp_path, p)
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

    def save_json(self, path: str | Path, *, include_secrets: bool = False) -> None:
        """Atomically export JSON. Credentials are omitted by default.

        Pass include_secrets=True only for a private, access-controlled backup.
        On Windows, file ACL behavior must be verified separately.
        """
        data = self._export_data(include_secrets)
        self._write_private_export(path, json.dumps(data, indent=2, sort_keys=True) + "\n")

    @classmethod
    def load_json(cls, path: str | Path) -> "ProfileConfig":
        """Load and validate a :class:`ProfileConfig` from a JSON file.

        Args:
            path: Source file path.

        Returns:
            A validated ``ProfileConfig`` instance.

        Raises:
            pydantic.ValidationError: If the file content is not a valid
                ``ProfileConfig``.
            OSError: If the file cannot be read.
        """
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))

    def save_yaml(self, path: str | Path, *, include_secrets: bool = False) -> None:
        """Atomically export YAML with proxy secrets redacted by default.

        Pass include_secrets=True only for a private, access-controlled backup.
        """
        import yaml

        self._write_private_export(
            path,
            yaml.safe_dump(self._export_data(include_secrets), sort_keys=True),
        )

    @classmethod
    def load_yaml(cls, path: str | Path) -> "ProfileConfig":
        """Load and validate a :class:`ProfileConfig` from a YAML file.

        Uses ``yaml.safe_load`` — aliases are resolved but no Python objects
        are constructed.

        Args:
            path: Source file path.

        Returns:
            A validated ``ProfileConfig`` instance.

        Raises:
            pydantic.ValidationError: If the document is not a valid
                ``ProfileConfig``.
            yaml.YAMLError: If the file is not valid YAML.
            OSError: If the file cannot be read.
        """
        import yaml

        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)


# ---------------------------------------------------------------------------
# Config presets (PH-18, N7)
# ---------------------------------------------------------------------------

_PROFILE_PRESETS: dict[str, dict[str, Any]] = {
    "us-desktop": {
        "os": "windows",
        "locale": "en-US",
        "timezone": "America/New_York",
        "headless": True,
    },
    "eu-desktop": {
        "os": "windows",
        "locale": "de-DE",
        "timezone": "Europe/Berlin",
        "headless": True,
    },
    # "mobile-android" deliberately removed: Camoufox ProfileConfig
    # supports only windows/macos/linux. Do not falsely label a desktop
    # fingerprint as Android; unknown name raises ConfigError below.
}


def preset_names() -> list[str]:
    """Return the names of all built-in profile presets (PH-18)."""
    return sorted(_PROFILE_PRESETS)


# Attach the classmethod without cluttering the class body.
def _preset_classmethod(cls: type, name: str, **overrides: Any) -> "ProfileConfig":
    """Build a ``ProfileConfig`` from a named preset merged with overrides."""
    if name not in _PROFILE_PRESETS:
        from .exceptions import ConfigError

        raise ConfigError(
            f"unknown profile preset: {name!r}",
            details={"stage": "preset", "preset": name, "available": preset_names()},
        )
    merged = {**_PROFILE_PRESETS[name], **overrides}
    return cls.model_validate(merged)


ProfileConfig.preset = classmethod(_preset_classmethod)  # type: ignore[attr-defined]
