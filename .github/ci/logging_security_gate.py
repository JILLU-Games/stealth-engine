"""Regression contract for F-19's currently confirmed nested payload leak.

Only synthetic credentials are tested. No private secrets or raw logs emitted.
"""
from __future__ import annotations

from loguru import logger
from stealth_engine.utils.logging import get_profile_logger


def main() -> int:
    captured: list[str] = []
    handler_id = logger.add(lambda message: captured.append(str(message)), level="DEBUG")
    secret = "CI_SYNTHETIC_SECRET_9f44"
    try:
        profile = get_profile_logger("ci", "ci_profile", "INFO", secrets=(secret,))
        profile.info("safe synthetic test", payload={"nested": {"password": secret}})
    finally:
        logger.remove(handler_id)
    if any(secret in message for message in captured):
        print("F-19 SECURITY GATE FAIL: nested secret leaked through profile logger")
        return 1
    print("F-19 nested secret redaction PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
