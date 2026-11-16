"""Fail closed when expected CI tests disappear or are silently skipped."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def verify(path: Path, *, gate: str, expected_skips: int, min_cases: int) -> int:
    if not path.is_file():
        print(f"ERROR [{gate}]: missing JUnit report: {path}", file=sys.stderr)
        return 1

    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        print(f"ERROR [{gate}]: unreadable JUnit report: {exc}", file=sys.stderr)
        return 1

    cases = list(root.iter("testcase"))
    failed = [c for c in cases if c.find("failure") is not None or c.find("error") is not None]
    skipped = [c for c in cases if c.find("skipped") is not None]
    completed = len(cases) - len(failed) - len(skipped)
    issues: list[str] = []
    if len(cases) < min_cases:
        issues.append(f"expected at least {min_cases} testcases; got {len(cases)}")
    if failed:
        issues.append(f"{len(failed)} failing/error testcases")
    if len(skipped) != expected_skips:
        issues.append(f"unexpected skip count {len(skipped)} (expected {expected_skips})")
    if gate == "regression":
        # Only the four deliberately env-gated smoke/canary cases and the
        # one POSIX-only PID permission test on Windows may be skipped.
        allowed = {"test_launch_about_blank_and_close",
                   "test_verify_stealth_real_browser",
                   "test_generated_fingerprint_has_required_keys",
                   "test_generated_fingerprints_pass_validator"}
        posix_only = "test_f07_pid_permission_denied_is_not_considered_dead"
        for case in skipped:
            name = case.get("name", "")
            classname = case.get("classname", "")
            if name in allowed and "test_smoke" in classname:
                continue
            if os.name == "nt" and name == posix_only and "test_forensic_regressions" in classname:
                continue
            issues.append(f"unexpected skipped testcase: {classname}.{name}")
    summary = (
        f"### {gate} JUnit gate\n\n"
        f"Cases: **{len(cases)}** | Passed: **{completed}** | Failed/errors: **{len(failed)}** | "
        f"Skipped: **{len(skipped)}** (expected: {expected_skips})\n\n"
        f"Status: **{'FAIL' if issues else 'PASS'}**\n"
    )
    print(summary)
    for case in failed[:20]:
        print(f"  FAIL {case.get('classname', '')}.{case.get('name', '')}")
    for item in issues:
        print("ERROR:", item, file=sys.stderr)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
            out.write(summary)
            for item in issues:
                out.write(f"- {item}\n")
    return int(bool(issues))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("junit", type=Path)
    p.add_argument("--gate", choices=("regression", "browser"), required=True)
    p.add_argument("--expected-skips", type=int, required=True)
    p.add_argument("--min-cases", type=int, default=1)
    args = p.parse_args()
    return verify(args.junit, gate=args.gate, expected_skips=args.expected_skips, min_cases=args.min_cases)


if __name__ == "__main__":
    raise SystemExit(main())
