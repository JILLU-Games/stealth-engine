"""Browser identity and fingerprint profile management."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import random
import secrets
from pathlib import Path
from typing import Any, Protocol

from browserforge.fingerprints import FingerprintGenerator

from .config import ProfileConfig
from .exceptions import IdentityError
from .utils.logging import get_logger

_log = get_logger(__name__)

# Canonical platform strings per OS persona.
_PLATFORM_MAP: dict[str, str] = {
    "windows": "Win32",
    "macos": "MacIntel",
    "linux": "Linux x86_64",
}

# Default device-memory values (GB) used as fallback when browserforge returns None.
_DEFAULT_DEVICE_MEMORY: int = 8

# Reduced-motion and color-scheme pools for seeded random selection.
_COLOR_SCHEMES: tuple[str, ...] = ("light", "dark")
_REDUCED_MOTION_OPTIONS: tuple[str, ...] = ("no-preference", "reduce")


_REQUIRED_SEED_KEYS: dict[str, type] = {
    "canvas": int,
    "audio": int,
    "fonts": int,
    "locale": str,
    "timezone_id": str,
}


def _profile_root(config: ProfileConfig) -> Path:
    """Resolve the on-disk profile root exactly as the engine does.

    Mirrors ``StealthEngine._derive_base_dir`` + ``SessionManager``:
    ``config.user_data_dir`` is the profile root when its final component
    equals ``profile_name``; otherwise the profile root is
    ``<user_data_dir>/<profile_name>``.  An empty derived base falls back to
    ``./profiles`` (``SessionManager`` treats falsy ``base_dir`` that way).

    Args:
        config: Validated profile configuration.

    Returns:
        Path to the directory that owns ``seeds.json``.
    """
    udd = config.user_data_dir.rstrip("/\\")
    if os.path.basename(udd) == config.profile_name:
        base = os.path.dirname(udd)
    else:
        base = udd
    return Path(base or "./profiles") / config.profile_name


def _valid_seed_dict(data: Any) -> bool:
    """Check a loaded seeds.json payload has the required keys/types."""
    if not isinstance(data, dict):
        return False
    for key, expected in _REQUIRED_SEED_KEYS.items():
        value = data.get(key)
        # bool is a subclass of int — reject it for numeric seeds.
        if expected is int and (not isinstance(value, int) or isinstance(value, bool)):
            return False
        if expected is str and (not isinstance(value, str) or not value.strip()):
            return False
    return True


def _detect_host_locale() -> str | None:
    """Best-effort host locale detection. Returns 'xx-XX' or None."""
    try:
        import locale as _locale

        loc, _ = _locale.getlocale()
        if loc:
            normalized = loc.split(".", 1)[0].replace("_", "-")
            parts = normalized.split("-")
            if (
                len(parts) == 2
                and len(parts[0]) == 2
                and len(parts[1]) == 2
                and all(part.isalpha() for part in parts)
            ):
                return f"{parts[0].lower()}-{parts[1].upper()}"
    except Exception:
        pass
    return None


def _detect_host_timezone() -> str | None:
    """Best-effort IANA timezone detection.

    Uses tzlocal (lazy import) to map Windows registry names to IANA via
    CLDR, and to read /etc/timezone on Linux. Returns 'Area/City' (e.g.
    'Asia/Dhaka') or None on failure.
    """
    try:
        from tzlocal import get_localzone_name

        tz = get_localzone_name()
        if tz and "/" in tz:
            return tz
    except Exception:
        pass
    tz = os.environ.get("TZ")
    if tz and "/" in tz:
        return tz
    return None


# ---------------------------------------------------------------------------
# Feature P — pluggable identity providers
# ---------------------------------------------------------------------------


class IdentityProvider(Protocol):
    """Contract for pluggable browser-identity generators.

    A provider receives the profile config and the generator's isolated RNG
    and must return a fingerprint dict with the same shape as
    :meth:`IdentityGenerator.generate` output (all primitive types).  Config
    ``locale``/``timezone`` overrides and final validation are applied by
    :class:`IdentityGenerator` after ``build`` returns, so providers do not
    need to implement them.
    """

    def build(
        self, config: ProfileConfig, rng: random.Random
    ) -> dict[str, Any]:
        """Build a raw fingerprint dict for ``config``.

        Args:
            config: Validated profile configuration.
            rng: Isolated :class:`random.Random` instance seeded from
                ``config.seed`` (or OS entropy when seed is ``None``).

        Returns:
            Fingerprint dict; must satisfy ``IdentityGenerator`` validation.
        """
        ...


class BrowserForgeIdentityProvider:
    """Default :class:`IdentityProvider` backed by browserforge.

    Wraps ``browserforge.fingerprints.FingerprintGenerator`` and converts its
    dataclass output into the canonical primitive fingerprint dict.  This is
    the historical behaviour of ``IdentityGenerator`` and remains the
    default when no provider is supplied.
    """

    def build(
        self, config: ProfileConfig, rng: random.Random
    ) -> dict[str, Any]:
        """Generate a fingerprint via browserforge.

        Args:
            config: Validated profile configuration.
            rng: Isolated RNG used for colour-scheme / reduced-motion picks.

        Returns:
            Fingerprint dict (config overrides NOT yet applied).

        Raises:
            IdentityError: On generation or extraction failure.
        """
        os_name: str = config.os  # "windows" | "macos" | "linux"

        try:
            gen = FingerprintGenerator(os=os_name)
            raw = gen.generate(os=os_name)
        except Exception as exc:
            raise IdentityError(
                "browserforge fingerprint generation failed",
                details={"stage": "generate", "reason": str(exc)},
            ) from exc

        try:
            return self._extract(raw, os_name, rng)
        except IdentityError:
            raise
        except Exception as exc:
            raise IdentityError(
                "fingerprint extraction failed",
                details={"stage": "extract", "reason": str(exc)},
            ) from exc

    def _extract(
        self, raw: Any, os_name: str, rng: random.Random
    ) -> dict[str, Any]:
        """Extract primitive values from a browserforge ``Fingerprint`` dataclass.

        Args:
            raw: ``Fingerprint`` instance returned by browserforge.
            os_name: Canonical OS name from ``ProfileConfig.os``.
            rng: Isolated RNG for colour-scheme / reduced-motion selection.

        Returns:
            Partially assembled fingerprint dict (before config overrides).

        Raises:
            IdentityError: If required fields are missing or inconsistent.
        """
        try:
            nav = raw.navigator
            scr = raw.screen
        except AttributeError as exc:
            raise IdentityError(
                "unexpected browserforge output structure",
                details={"stage": "extract", "reason": str(exc)},
            ) from exc

        # --- User-Agent ---
        user_agent: str = nav.userAgent or ""
        if not user_agent:
            raise IdentityError(
                "browserforge returned empty user_agent",
                details={"stage": "extract", "reason": "userAgent is empty"},
            )

        # --- Platform (enforced to match config.os) ---
        platform: str = _PLATFORM_MAP[os_name]

        # --- Screen dimensions ---
        screen_w: int = int(scr.width or 1920)
        screen_h: int = int(scr.height or 1080)
        if screen_w <= 0:
            screen_w = 1920
        if screen_h <= 0:
            screen_h = 1080

        # --- Viewport (inner dimensions, clamped to screen) ---
        inner_w: int = int(scr.innerWidth or scr.clientWidth or screen_w)
        inner_h: int = int(scr.innerHeight or scr.clientHeight or screen_h)
        # Ensure viewport <= screen
        inner_w = min(max(inner_w, 1), screen_w)
        inner_h = min(max(inner_h, 1), screen_h)

        # --- Locale ---
        locale: str = (nav.language or "en-US").strip() or "en-US"

        # --- Timezone (best-effort from Accept-Language; placeholder fallback) ---
        timezone_id: str = self._derive_timezone(locale)

        # --- Hardware ---
        hw_concurrency: int = int(nav.hardwareConcurrency or 4)
        if hw_concurrency <= 0:
            hw_concurrency = 4
        device_memory: int = int(nav.deviceMemory or _DEFAULT_DEVICE_MEMORY)
        if device_memory <= 0:
            device_memory = _DEFAULT_DEVICE_MEMORY

        # --- Touch / mobile ---
        max_touch: int = int(getattr(nav, "maxTouchPoints", 0) or 0)
        has_touch: bool = max_touch > 0
        # Mobile heuristic: touch + screen narrower than 768 px
        is_mobile: bool = has_touch and screen_w < 768

        # --- Color scheme & reduced motion (seeded random choice) ---
        color_scheme: str = rng.choice(_COLOR_SCHEMES)
        reduced_motion: str = rng.choice(_REDUCED_MOTION_OPTIONS)

        return {
            "user_agent": user_agent,
            "viewport": {"width": inner_w, "height": inner_h},
            "screen": {"width": screen_w, "height": screen_h},
            "locale": locale,
            "timezone_id": timezone_id,
            "platform": platform,
            "hardware_concurrency": hw_concurrency,
            "device_memory": device_memory,
            "color_scheme": color_scheme,
            "reduced_motion": reduced_motion,
            "is_mobile": is_mobile,
            "has_touch": has_touch,
        }

    @staticmethod
    def _derive_timezone(locale: str) -> str:
        """Return a plausible IANA timezone for a BCP-47 locale tag.

        This is a static best-effort mapping used when GeoIP data is not
        yet available.  The proxy layer will override this value later.

        Args:
            locale: BCP-47 locale tag (e.g. ``"en-US"``).

        Returns:
            IANA timezone string (e.g. ``"America/New_York"``).
        """
        _LOCALE_TZ: dict[str, str] = {
            "en-US": "America/New_York",
            "en-GB": "Europe/London",
            "en-AU": "Australia/Sydney",
            "en-CA": "America/Toronto",
            "fr-FR": "Europe/Paris",
            "de-DE": "Europe/Berlin",
            "es-ES": "Europe/Madrid",
            "it-IT": "Europe/Rome",
            "pt-BR": "America/Sao_Paulo",
            "ja-JP": "Asia/Tokyo",
            "zh-CN": "Asia/Shanghai",
            "ko-KR": "Asia/Seoul",
            "ru-RU": "Europe/Moscow",
            "tr-TR": "Europe/Istanbul",
            "nl-NL": "Europe/Amsterdam",
            "pl-PL": "Europe/Warsaw",
            "sv-SE": "Europe/Stockholm",
            "da-DK": "Europe/Copenhagen",
            "fi-FI": "Europe/Helsinki",
            "nb-NO": "Europe/Oslo",
        }
        # BF-03/B-18: bare language-code fallbacks ("fr" → Paris, etc.)
        _LANG_TZ: dict[str, str] = {
            "en": "America/New_York",
            "fr": "Europe/Paris",
            "de": "Europe/Berlin",
            "es": "Europe/Madrid",
            "it": "Europe/Rome",
            "pt": "America/Sao_Paulo",
            "ja": "Asia/Tokyo",
            "zh": "Asia/Shanghai",
            "ko": "Asia/Seoul",
            "ru": "Europe/Moscow",
            "tr": "Europe/Istanbul",
            "nl": "Europe/Amsterdam",
            "pl": "Europe/Warsaw",
            "sv": "Europe/Stockholm",
            "da": "Europe/Copenhagen",
            "fi": "Europe/Helsinki",
            "nb": "Europe/Oslo",
            "no": "Europe/Oslo",
        }
        # Try exact match, then case-normalised lookup (BF-03/B-18 —
        # "en-us" must resolve like "en-US"), then language-only fallback.
        canon = locale.strip()
        lookup = {k.lower(): v for k, v in _LOCALE_TZ.items()}
        lang = canon.split("-")[0].lower()
        return (
            _LOCALE_TZ.get(canon)
            or lookup.get(canon.lower())
            or lookup.get(lang + "-" + lang.upper())
            or _LANG_TZ.get(lang)
            or "UTC"
        )


class IdentityGenerator:
    """Generates a coherent, optionally seed-deterministic browser fingerprint.

    The fingerprint is derived from a ``ProfileConfig`` and expressed as a
    plain :class:`dict`.  All provider objects are consumed internally;
    callers receive only primitive Python types.

    Args:
        config: Validated profile configuration produced by
            :class:`~stealth_engine.config.ProfileConfig`.
        provider: Optional :class:`IdentityProvider` implementation.
            Defaults to :class:`BrowserForgeIdentityProvider`.
    """

    def __init__(
        self,
        config: ProfileConfig,
        provider: IdentityProvider | None = None,
        launch_salt: str | None = None,
    ) -> None:
        """Initialise the generator.

        Stores the config and provider, and — when ``config.seed`` is set —
        creates an isolated :class:`random.Random` instance so the global
        RNG is never touched.  The provider is **not** invoked here
        (lazy).

        Args:
            config: Profile configuration for this identity.
            provider: Identity provider; ``None`` selects the default
                browserforge-backed provider.
            launch_salt: Optional per-launch salt (PH-17 diversity mode).
                When combined with ``config.seed`` it derives a different
                RNG stream — same profile, different fingerprint per launch.
        """
        self._config: ProfileConfig = config
        self._provider: IdentityProvider = (
            provider if provider is not None else BrowserForgeIdentityProvider()
        )
        self._cached_fingerprint: dict[str, Any] | None = None
        self._cached_hash: str | None = None

        effective_seed: int | None = config.seed
        if config.seed is not None and launch_salt is not None:
            import hashlib

            effective_seed = int(
                hashlib.sha256(f"{config.seed}:{launch_salt}".encode()).hexdigest()[:16],
                16,
            )
        self._effective_seed: int | None = effective_seed
        if effective_seed is not None:
            # Isolated RNG — never touches the global random state.
            self._rng: random.Random = random.Random(effective_seed)
        else:
            self._rng = random.Random()  # seeded from OS entropy

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> dict[str, Any]:
        """Generate and return the browser fingerprint as a plain dict.

        The result is cached on the instance.  Calling this method more
        than once always returns the identical dict (by reference for the
        cache, structurally identical in all cases).

        Returns:
            A generated identity *proposal*, not a guarantee of browser-visible
            values. Camoufox generates its own browser fingerprint at launch;
            only the explicitly supported fields mapped by
            ``StealthEngine._build_launch_kwargs`` are applied. The remaining
            fields are diagnostics and must not be reported as live spoofed
            properties. Contains the following keys:

            - ``user_agent`` (:class:`str`)
            - ``viewport`` (:class:`dict` with ``width`` / ``height``)
            - ``screen`` (:class:`dict` with ``width`` / ``height``)
            - ``locale`` (:class:`str`)
            - ``timezone_id`` (:class:`str`)
            - ``platform`` (:class:`str`)
            - ``hardware_concurrency`` (:class:`int`)
            - ``device_memory`` (:class:`int`)
            - ``color_scheme`` (:class:`str`)
            - ``reduced_motion`` (:class:`str`)
            - ``is_mobile`` (:class:`bool`)
            - ``has_touch`` (:class:`bool`)

        Raises:
            IdentityError: If fingerprint generation or validation fails
                for any reason.
        """
        if self._cached_fingerprint is not None:
            # Return a deep copy so callers cannot corrupt the internal cache.
            return copy.deepcopy(self._cached_fingerprint)

        self._cached_fingerprint = self._build_fingerprint()
        return copy.deepcopy(self._cached_fingerprint)

    def fingerprint_hash(self) -> str:
        """Return a stable SHA-256 hex digest of the generated fingerprint.

        If :meth:`generate` has not yet been called, it is invoked once
        and the result is cached on the instance.  The hash is derived
        from a deterministic JSON serialisation (sorted keys) so the same
        fingerprint always produces the same digest.

        Returns:
            64-character lowercase hex string.

        Raises:
            IdentityError: Propagated from :meth:`generate` on failure.
        """
        if self._cached_hash is not None:
            return self._cached_hash

        fp = self.generate()
        serialised = json.dumps(fp, sort_keys=True, ensure_ascii=True)
        self._cached_hash = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
        return self._cached_hash

    def get_or_create_seeds(self) -> dict:
        """Load or create persistent per-profile fingerprint seeds.

        Numeric device seeds derive from ``config.seed``. Locale and timezone
        values prefer explicit config, then host detection, then fallback.
        """
        seeds_path = _profile_root(self._config) / "seeds.json"

        if seeds_path.exists():
            try:
                loaded = json.loads(seeds_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                _log.warning(
                    "Corrupt seeds.json at {} — regenerating: {}",
                    seeds_path,
                    exc,
                )
            else:
                if _valid_seed_dict(loaded):
                    # Explicit locale/timezone take precedence over legacy saved
                    # metadata; numeric seeds remain byte-for-byte stable.
                    # The "auto" sentinel is deliberately resolved at launch.
                    updates = {}
                    for field, key, source in (
                        (self._config.locale, "locale", "locale_source"),
                        (self._config.timezone, "timezone_id", "timezone_source"),
                    ):
                        if isinstance(field, str) and field.strip() and field.strip().lower() != "auto":
                            if loaded[key] != field or loaded.get(source) != "config":
                                updates[key] = field
                                updates[source] = "config"
                    if updates:
                        revised = {**loaded, **updates}
                        tmp_path = seeds_path.with_suffix(".json.tmp")
                        try:
                            tmp_path.write_text(json.dumps(revised, indent=2, sort_keys=True), encoding="utf-8")
                            os.replace(tmp_path, seeds_path)
                        except OSError as exc:
                            try:
                                tmp_path.unlink(missing_ok=True)
                            except OSError:
                                pass
                            raise IdentityError(
                                "Failed to persist updated locale/timezone seeds",
                                details={"path": str(seeds_path), "reason": str(exc)},
                            ) from exc
                        return revised
                    return loaded
                _log.warning(
                    "seeds.json at {} missing required keys or has wrong "
                    "types — regenerating",
                    seeds_path,
                )

        base_rng = random.Random(
            self._config.seed
            if self._config.seed is not None
            else secrets.randbits(32)
        )

        # "auto" is a launch-time sentinel resolved by the engine from GeoIP;
        # seeds must never persist the literal value — treat it as unset.
        cfg_locale = self._config.locale
        if cfg_locale and cfg_locale.strip().lower() != "auto":
            locale_value = cfg_locale
            locale_source = "config"
        else:
            detected_locale = _detect_host_locale()
            if detected_locale:
                locale_value = detected_locale
                locale_source = "host"
            else:
                locale_value = "en-US"
                locale_source = "fallback"

        cfg_timezone = self._config.timezone
        if cfg_timezone and cfg_timezone.strip().lower() != "auto":
            timezone_value = cfg_timezone
            timezone_source = "config"
        else:
            detected_timezone = _detect_host_timezone()
            if detected_timezone:
                timezone_value = detected_timezone
                timezone_source = "host"
            else:
                timezone_value = "UTC"
                timezone_source = "fallback"
                _log.warning(
                    "Host timezone could not be detected as IANA. "
                    "Set ProfileConfig.timezone explicitly. Falling back to UTC."
                )

        seeds = {
            "canvas": base_rng.randint(0, 2**31 - 1),
            "audio": base_rng.randint(0, 2**31 - 1),
            "fonts": base_rng.randint(0, 2**31 - 1),
            "locale": locale_value,
            "timezone_id": timezone_value,
            "locale_source": locale_source,
            "timezone_source": timezone_source,
        }

        tmp_path = seeds_path.with_suffix(".json.tmp")
        try:
            seeds_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_text(
                json.dumps(seeds, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            os.replace(tmp_path, seeds_path)
        except OSError as exc:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise IdentityError(
                "Failed to persist seeds.json",
                details={"path": str(seeds_path), "reason": str(exc)},
            ) from exc

        return seeds

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_fingerprint(self) -> dict[str, Any]:
        """Delegate raw generation to the provider and finalise the dict.

        The provider returns the base fingerprint; ``ProfileConfig``
        ``locale``/``timezone`` overrides are applied here so every provider
        gets identical override semantics, then the result is validated.

        Returns:
            Validated fingerprint dict.

        Raises:
            IdentityError: On any generation or validation failure.
        """
        cfg = self._config

        try:
            fp = self._provider.build(cfg, self._rng)
        except IdentityError:
            raise
        except Exception as exc:
            raise IdentityError(
                "identity provider failed",
                details={"stage": "provider.build", "reason": str(exc)},
            ) from exc

        # Apply ProfileConfig overrides.
        if cfg.locale is not None:
            fp["locale"] = cfg.locale
        if cfg.timezone is not None:
            fp["timezone_id"] = cfg.timezone

        self._validate(fp)
        _log.debug(
            "Fingerprint generated",
            profile=cfg.profile_name,
            platform=fp["platform"],
            ua_prefix=fp["user_agent"][:40],
        )
        return fp

    @staticmethod
    def _validate(fp: dict[str, Any]) -> None:
        """Assert that the assembled fingerprint satisfies all hard constraints.

        Args:
            fp: Assembled fingerprint dict.

        Raises:
            IdentityError: If any constraint is violated.
        """
        required_keys = (
            "user_agent",
            "viewport",
            "screen",
            "locale",
            "timezone_id",
            "platform",
            "hardware_concurrency",
            "device_memory",
            "color_scheme",
            "reduced_motion",
            "is_mobile",
            "has_touch",
        )
        for key in required_keys:
            if fp.get(key) is None:
                raise IdentityError(
                    f"fingerprint missing required field: {key!r}",
                    details={"stage": "validate", "reason": f"{key} is None"},
                )

        # String fields must be non-empty.
        for str_key in ("user_agent", "locale", "timezone_id", "platform", "color_scheme", "reduced_motion"):
            val = fp.get(str_key, "")
            if not isinstance(val, str) or not val.strip():
                raise IdentityError(
                    f"fingerprint field {str_key!r} is empty or not a string",
                    details={"stage": "validate", "reason": f"{str_key}={val!r}"},
                )

        # Viewport must be <= screen.
        vp = fp["viewport"]
        sc = fp["screen"]
        if vp["width"] > sc["width"] or vp["height"] > sc["height"]:
            raise IdentityError(
                "viewport exceeds screen dimensions",
                details={
                    "stage": "validate",
                    "reason": f"viewport={vp} > screen={sc}",
                },
            )

        # All int fields must be positive.
        for int_key in ("hardware_concurrency", "device_memory"):
            if not isinstance(fp[int_key], int) or fp[int_key] <= 0:
                raise IdentityError(
                    f"fingerprint field {int_key!r} must be a positive integer",
                    details={"stage": "validate", "reason": f"{int_key}={fp[int_key]!r}"},
                )


# ---------------------------------------------------------------------------
# Fingerprint consistency validator (PH-18, N2)
# ---------------------------------------------------------------------------

_FP_REQUIRED_KEYS = (
    "user_agent", "viewport", "screen", "locale", "timezone_id",
    "platform", "hardware_concurrency", "device_memory",
)

_OS_UA_TOKENS = {
    "windows": ("windows nt", "win64", "win32", "windows"),
    "macos": ("mac os x", "macintosh"),
    "linux": ("linux", "x11"),
}


def validate_fingerprint(fp: dict[str, Any]) -> dict[str, Any]:
    """Score internal consistency of a generated fingerprint dict (N2).

    Checks required keys, viewport-vs-screen sanity, UA↔platform↔OS-token
    coherence, IANA timezone validity, locale shape, and sane numeric
    ranges.  Pure function — no I/O.

    Args:
        fp: Fingerprint dict (e.g. from ``IdentityGenerator.generate()``).

    Returns:
        ``{"consistent": bool, "issues": [str], "score": int}`` — score is
        100 minus 15 per issue, floored at 0.
    """
    issues: list[str] = []

    for key in _FP_REQUIRED_KEYS:
        if key not in fp or fp[key] in (None, "", {}, []):
            issues.append(f"missing/empty required key: {key}")

    viewport = fp.get("viewport") or {}
    screen = fp.get("screen") or {}
    vw, vh = viewport.get("width"), viewport.get("height")
    sw, sh = screen.get("width"), screen.get("height")
    if all(isinstance(v, int) for v in (vw, vh, sw, sh)):
        if vw > sw or vh > sh:
            issues.append(f"viewport {vw}x{vh} exceeds screen {sw}x{sh}")

    ua = str(fp.get("user_agent") or "").lower()
    platform = str(fp.get("platform") or "").lower()
    os_name = str(fp.get("os") or "").lower()
    detected_os = ""
    if ua:
        for name, tokens in _OS_UA_TOKENS.items():
            if any(t in ua for t in tokens):
                detected_os = name
                if os_name and os_name != name and name not in os_name:
                    issues.append(f"UA suggests {name} but os={os_name!r}")
                break
    if not os_name:
        # BF-03/B-11: real fingerprints carry no "os" key — infer it from
        # UA tokens so the platform↔OS coherence check isn't dead code.
        os_name = detected_os
    if platform and os_name:
        # Coherence with known platform↔OS aliases (Win32/Win64→windows,
        # MacIntel→macos, Linux x86_64→linux).
        _aliases = {
            "windows": ("win32", "win64", "windows"),
            "macos": ("macintel", "macppc", "macos"),
            "linux": ("linux", "x86_64", "i686"),
        }
        coherent = (
            os_name in platform
            or platform in os_name
            or os_name in _aliases
            and any(a in platform for a in _aliases[os_name])
        )
        if not coherent:
            issues.append(f"platform {platform!r} vs os {os_name!r} mismatch")

    tz = str(fp.get("timezone_id") or "")
    if tz:
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(tz)
        except Exception:
            issues.append(f"invalid IANA timezone_id: {tz!r}")

    locale = str(fp.get("locale") or "")
    if locale and not locale.replace("-", "").replace("_", "").isalnum():
        issues.append(f"suspicious locale format: {locale!r}")

    hc = fp.get("hardware_concurrency")
    if hc is not None and (not isinstance(hc, int) or hc < 1 or hc > 128):
        issues.append(f"unusual hardware_concurrency: {hc!r}")
    dm = fp.get("device_memory")
    if dm is not None and (not isinstance(dm, int) or dm < 1 or dm > 64):
        issues.append(f"unusual device_memory: {dm!r}")

    score = max(0, 100 - 15 * len(issues))
    return {
        "consistent": not issues,
        "issues": issues,
        "score": score,
    }
