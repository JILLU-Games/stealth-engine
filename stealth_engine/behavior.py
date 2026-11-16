"""Human-like behavioral biometrics for stealth sessions (PH-15).

Provides deterministic, per-profile behavioral parameters persisted in
``behavior.json`` inside the profile directory, plus trajectory/scroll/dwell
primitives used by ``BrowserSession`` human hooks.

Design rules:
- All randomness flows through an isolated ``random.Random`` seeded from
  ``ProfileConfig.seed`` — never the global ``random`` module.
- Persisted parameters make the same profile *behave* consistently across
  launches (same typing cadence, scroll rhythm, mouse style).
- Corrupt/missing ``behavior.json`` self-heals by regenerating.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .utils.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from .session import SessionManager

_log = get_logger(__name__)

_BEHAVIOR_FILE = "behavior.json"

_REQUIRED_KEYS = ("typing", "scroll", "mouse")


def _bezier_point(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    """Cubic bezier interpolation at parameter ``t``."""
    u = 1.0 - t
    x = (
        u * u * u * p0[0]
        + 3 * u * u * t * p1[0]
        + 3 * u * t * t * p2[0]
        + t * t * t * p3[0]
    )
    y = (
        u * u * u * p0[1]
        + 3 * u * u * t * p1[1]
        + 3 * u * t * t * p2[1]
        + t * t * t * p3[1]
    )
    return (x, y)


def bezier_path(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    rng: random.Random,
    steps: int | None = None,
) -> list[tuple[float, float]]:
    """Generate a human-like curved mouse path from (x0,y0) to (x1,y1).

    Uses a cubic bezier with two control points offset perpendicular to the
    straight line, producing the slight arc real hands make.  Parameter ``t``
    is eased (smoothstep) so speed ramps up then settles — matching real
    mouse acceleration profiles.

    Args:
        x0, y0: Start coordinates.
        x1, y1: End coordinates.
        rng: Isolated RNG for control-point offsets.
        steps: Number of sample points; auto-chosen from distance if None.

    Returns:
        List of ``(x, y)`` waypoints including start and end.
    """
    dx, dy = x1 - x0, y1 - y0
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return [(x0, y0), (x1, y1)]

    if steps is None:
        steps = max(6, min(24, int(dist / 25)))

    # Unit perpendicular for control-point offset.
    px, py = -dy / dist, dx / dist
    # Control points sit 15-35% along the line, offset sideways by up to
    # ~18% of distance — gentle arc, never a loop.
    bow = rng.uniform(-0.18, 0.18) * dist
    c1_t = rng.uniform(0.25, 0.40)
    c2_t = rng.uniform(0.60, 0.75)
    p0 = (x0, y0)
    p3 = (x1, y1)
    p1 = (
        x0 + dx * c1_t + px * bow * rng.uniform(0.6, 1.0),
        y0 + dy * c1_t + py * bow * rng.uniform(0.6, 1.0),
    )
    p2 = (
        x0 + dx * c2_t + px * bow * rng.uniform(0.4, 0.9),
        y0 + dy * c2_t + py * bow * rng.uniform(0.4, 0.9),
    )

    path: list[tuple[float, float]] = []
    for i in range(steps + 1):
        t = i / steps
        # Smoothstep easing: slow start, fast middle, slow end.
        te = t * t * (3.0 - 2.0 * t)
        x, y = _bezier_point(p0, p1, p2, p3, te)
        # Tiny per-point jitter for hand tremor (endpoints stay exact).
        if 0 < i < steps:
            x += rng.uniform(-1.5, 1.5)
            y += rng.uniform(-1.5, 1.5)
        path.append((x, y))
    path[0] = (x0, y0)
    path[-1] = (x1, y1)  # exact landing
    return path


def physics_scroll_chunks(
    dy: int,
    rng: random.Random,
    profile: dict[str, Any],
) -> list[tuple[float, float]]:
    """Split a scroll distance into physics-like ``(delta, pause_s)`` chunks.

    Magnitude decays toward the end (inertia), with small random jitter —
    mimics a real flick-and-settle scroll instead of uniform steps.

    Args:
        dy: Total vertical scroll distance (positive = down).
        rng: Isolated RNG.
        profile: ``scroll`` section of the behavior profile.

    Returns:
        List of ``(wheel_delta, pause_seconds)`` tuples.
    """
    chunks = rng.randint(*profile["chunks"])
    if chunks < 1 or dy == 0:
        return []
    decay = profile.get("decay", 0.85)
    pause_lo, pause_hi = profile["pause_s"]
    sign = 1.0 if dy >= 0 else -1.0

    # Exponentially decaying shares, normalised; last chunk takes the
    # remainder so deltas always sum exactly to ``dy``.
    raw = [decay ** i for i in range(chunks)]
    raw_total = sum(raw)
    out: list[tuple[float, float]] = []
    remaining = float(dy)  # signed
    for i in range(chunks):
        if i == chunks - 1:
            delta = remaining
        else:
            magnitude = abs(dy) * raw[i] / raw_total * rng.uniform(0.85, 1.15)
            delta = sign * magnitude
            remaining -= delta
        pause = rng.uniform(pause_lo, pause_hi)
        out.append((delta, pause))
    return out


class BehaviorProfile:
    """Per-profile persisted behavioral parameters.

    Loaded from ``behavior.json`` in the profile directory; generated from
    the profile seed on first use.  Invalid files are regenerated.

    Attributes:
        data: Raw parameter dict (``typing``, ``scroll``, ``mouse`` keys).
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    # -- generation ------------------------------------------------------

    @staticmethod
    def _generate(rng: random.Random) -> dict[str, Any]:
        return {
            "typing": {
                "base_delay_s": round(rng.uniform(0.045, 0.115), 4),
                "jitter_frac": round(rng.uniform(0.25, 0.55), 3),
                "word_pause_prob": round(rng.uniform(0.10, 0.45), 3),
                "word_pause_s": [round(rng.uniform(0.04, 0.22), 3)] * 2,
            },
            "scroll": {
                "chunks": [rng.randint(3, 6), rng.randint(3, 8)],
                "pause_s": [round(rng.uniform(0.03, 0.10), 3), round(rng.uniform(0.08, 0.22), 3)],
                "decay": round(rng.uniform(0.75, 0.92), 3),
            },
            "mouse": {
                "steps": [rng.randint(8, 14), rng.randint(14, 22)],
                "total_s": [round(rng.uniform(0.18, 0.30), 3), round(rng.uniform(0.30, 0.45), 3)],
            },
        }

    @staticmethod
    def _valid(data: Any) -> bool:
        if not isinstance(data, dict):
            return False
        for key in _REQUIRED_KEYS:
            if not isinstance(data.get(key), dict):
                return False
        t = data["typing"]
        return all(
            k in t for k in ("base_delay_s", "jitter_frac", "word_pause_prob", "word_pause_s")
        )

    # -- persistence -----------------------------------------------------

    @classmethod
    def load_or_create(
        cls, session: "SessionManager", seed: int | None
    ) -> "BehaviorProfile":
        """Load ``behavior.json`` or generate + persist a new profile.

        Args:
            session: SessionManager owning the profile directory.
            seed: ``ProfileConfig.seed`` used to seed generation.

        Returns:
            A :class:`BehaviorProfile`; never raises on corrupt files.
        """
        profile_dir = Path(session.profile_dir)
        path = profile_dir / _BEHAVIOR_FILE
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if cls._valid(raw):
                return cls(raw)
            _log.warning("behavior.json invalid — regenerating", path=str(path))
        except FileNotFoundError:
            pass
        except Exception as exc:
            _log.warning("behavior.json unreadable — regenerating", reason=str(exc))

        rng = random.Random(seed) if seed is not None else random.Random()
        data = cls._generate(rng)
        try:
            profile_dir.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp.replace(path)
        except Exception as exc:
            _log.warning("behavior.json persist failed", reason=str(exc))
        return cls(data)

    # -- accessors -------------------------------------------------------

    def typing_delay(self, rng: random.Random, char: str) -> float:
        """Delay in seconds before the next keystroke."""
        t = self.data["typing"]
        delay = t["base_delay_s"] * rng.uniform(
            1.0 - t["jitter_frac"], 1.0 + t["jitter_frac"]
        )
        if char == " " and rng.random() < t["word_pause_prob"]:
            delay += rng.uniform(*t["word_pause_s"])
        return max(0.01, delay)

    def mouse_steps(self, rng: random.Random) -> int:
        lo, hi = self.data["mouse"]["steps"]
        return rng.randint(lo, hi)

    def mouse_total_s(self, rng: random.Random) -> float:
        lo, hi = self.data["mouse"]["total_s"]
        return rng.uniform(lo, hi)

    def scroll_plan(self, dy: int, rng: random.Random) -> list[tuple[float, float]]:
        """``(delta, pause_s)`` chunks for a scroll of ``dy`` pixels."""
        return physics_scroll_chunks(dy, rng, self.data["scroll"])


def dwell_plan(rng: random.Random, min_s: float, max_s: float) -> list[tuple[str, float]]:
    """Attention-dwell schedule: ``[("sleep", s) | ("jiggle", s), ...]``.

    Splits a dwell duration into 2–5 segments; segments may request a tiny
    mouse jiggle (``"jiggle"``) to mimic idle micro-movement.  Caller maps
    ``"jiggle"`` segments to small ``ahuman_move``/``human_move`` offsets.

    Args:
        rng: Isolated RNG.
        min_s, max_s: Dwell duration bounds in seconds.

    Returns:
        Ordered segment list summing to ~total duration.
    """
    total = rng.uniform(min_s, max_s)
    n = rng.randint(2, 5)
    weights = [rng.random() + 0.2 for _ in range(n)]
    wsum = sum(weights)
    segs: list[tuple[str, float]] = []
    for i, w in enumerate(weights):
        dur = total * w / wsum
        kind = "jiggle" if (i > 0 and rng.random() < 0.35) else "sleep"
        segs.append((kind, dur))
    return segs
