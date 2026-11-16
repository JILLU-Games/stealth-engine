"""Ban-risk scoring heuristic for stealth sessions (PH-17, N55).

Aggregates signals from :meth:`BrowserSession.probe_fingerprint`,
optional :class:`GeoInfo`, and :class:`ProfileConfig` into a 0-100 risk
score with per-signal explanations.  Pure function — no I/O.

Interpretation:
- ``0-30``  low    — identity looks like a real consumer browser
- ``31-60`` medium — some suspicious signals; review before scale
- ``61-100`` high  — likely detectable; do not use for sensitive work
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from .config import ProfileConfig
    from .proxy import GeoInfo

_SOFTWARE_RENDERERS = ("swiftshader", "llvmpipe", "softpipe", "microsoft basic")


def ban_risk_score(
    probe: dict[str, Any],
    geo: "GeoInfo | None" = None,
    config: "ProfileConfig | None" = None,
) -> dict[str, Any]:
    """Score ban/detection risk from probe + optional geo/config signals.

    Args:
        probe: Dict from ``BrowserSession.probe_fingerprint`` (missing
            keys are treated as absent, not errors).
        geo: Optional :class:`GeoInfo` for timezone/locale cross-checks.
        config: Optional :class:`ProfileConfig` for explicit overrides.

    Returns:
        ``{"score": int, "level": "low"|"medium"|"high", "signals": [str]}``
    """
    signals: list[str] = []
    score = 0

    def add(points: int, msg: str) -> None:
        nonlocal score
        score += points
        signals.append(msg)

    renderer = str(probe.get("webgl_renderer") or "").lower()
    if not renderer:
        add(15, "webgl_renderer missing")
    elif any(s in renderer for s in _SOFTWARE_RENDERERS):
        # Software rasteriser is a strong headless/bot tell.
        add(65, f"software WebGL renderer: {renderer[:60]}")

    if not probe.get("canvas_hash"):
        add(15, "canvas readback failed/null")

    ua = str(probe.get("user_agent") or "")
    if not ua:
        add(20, "user_agent missing")

    langs = probe.get("languages")
    if not langs:
        add(10, "navigator.languages empty")

    hc = probe.get("hardware_concurrency")
    if hc is None:
        add(10, "hardware_concurrency missing")
    elif isinstance(hc, int) and (hc < 2 or hc > 64):
        add(10, f"unusual hardware_concurrency={hc}")

    dm = probe.get("device_memory")
    if dm is None:
        add(5, "device_memory missing")

    if probe.get("gamepad_count"):
        add(5, f"gamepad_count={probe['gamepad_count']} (unusual for desktop)")
    if probe.get("has_usb"):
        add(3, "navigator.usb present")
    if probe.get("has_serial"):
        add(3, "navigator.serial present")

    if geo is not None and probe.get("timezone"):
        # Cheap consistency: timezone string should share a region hint
        # with the geo timezone when both present.
        geo_tz = getattr(geo, "timezone_id", None)
        probe_tz = probe.get("timezone")
        if geo_tz and probe_tz and geo_tz != probe_tz:
            add(15, f"timezone mismatch: probe={probe_tz} geo={geo_tz}")

    if config is not None:
        if config.fingerprint_diversity:
            add(5, "fingerprint_diversity enabled — identity changes per launch")
        if config.disable_ipv6:
            add(2, "ipv6 disabled — slight fingerprint deviation")

    score = min(100, score)
    level = "low" if score <= 30 else "medium" if score <= 60 else "high"
    return {"score": score, "level": level, "signals": signals}
