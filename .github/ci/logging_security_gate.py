"""F-19 security acceptance: inspect Loguru raw structured records, not str(message).

Only synthetic test secrets are used. This checks profile-owned log events; it
does not certify legacy module-global loggers as per-profile isolated.
"""
from __future__ import annotations

from loguru import logger
from stealth_engine.utils.logging import get_profile_logger


def main() -> int:
    records: list[dict] = []
    secret = "CI_SYNTHETIC_SECRET_9f44"
    handler_id = logger.add(lambda message: records.append(message.record.copy()), level="TRACE")
    try:
        info = get_profile_logger("ci", "info-profile", "INFO", secrets=(secret,))
        error = get_profile_logger("ci", "error-profile", "ERROR", secrets=(secret,))
        info.debug("filtered", payload={"secret": secret})
        info.info("structured", payload={
            "nested": {"password": secret},
            "items": [secret, {"value": (secret,)}],
        })
        error.info("filtered", payload={"secret": secret})
        error.error("error visible", credential=secret)
    finally:
        logger.remove(handler_id)
    events = [(record["extra"].get("profile"), record["message"]) for record in records]
    expected = [("info-profile", "structured"), ("error-profile", "error visible")]
    if events != expected:
        print("F-19 SECURITY GATE FAIL: profile-level filtering mismatch")
        return 1
    if any(secret in repr(record["extra"]) or secret in record["message"] for record in records):
        print("F-19 SECURITY GATE FAIL: nested secret remains in structured record")
        return 1
    if not records or not all("profile" in record["extra"] for record in records):
        print("F-19 SECURITY GATE FAIL: missing profile metadata")
        return 1
    print("F-19 scoped record-level sanitization and severity PASS")
    print("NOTE: module-global logs are not covered by this gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
