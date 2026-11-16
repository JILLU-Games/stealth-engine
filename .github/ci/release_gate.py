"""Fail-closed CI verdict: verify core separately from external proxy claims.

Core acceptance is a defined subset (direct host and controlled localhost
transport only). A green Core CI gate is not full proxy/WebRTC certification.
No releases, tags or deployments are performed.
"""
from __future__ import annotations

import os


_REQUIRED = (
    "REGRESSION", "BROWSER", "DIRECT_HOST", "LOCAL_PROXY",
    "FILE_SECURITY", "PACKAGE", "LOGGING_SECURITY", "DEPENDENCY_AUDIT",
)


def main() -> int:
    observed = {name: os.environ.get(name, "unknown") for name in _REQUIRED}
    proxy = os.environ.get("PROXY", "unknown")
    blocked = [name for name, status in observed.items() if status != "success"]
    core_status = "CORE_CI_ACCEPTED" if not blocked else "CORE_BLOCKED"
    lines = [
        "## stealth-engine — Release Gate",
        "",
        "**Scope:** core direct-host, controlled localhost proxy, browser, regression,",
        "Windows/Linux private files, packaging, scoped log security, dependency audit.",
        "",
        "| Core required job | Result |",
        "|---|---|",
        *[f"| {name.lower()} | {status} |" for name, status in observed.items()],
        "",
        f"**Core CI verdict: {core_status}**",
        "",
        f"**External real proxy gate: {proxy.upper()}**",
        "External proxy authentication/exit IP/DNS/WebRTC are NOT CORE-certified.",
        "The local proxy test cannot replace the external proxy acceptance.",
        "",
        "**Production readiness:** CI acceptance covers these tested environments",
        "and features only; an actual production release additionally requires",
        "release-provenance review, documented support limits, and final sign-off.",
        "Camoufox is not guaranteed undetectable; third-party sites can behave differently.",
        "ProfileLogger only covers profile-owned events; legacy module-global logs",
        "remain outside the per-profile severity contract.",
        "No automatic tag, release or deployment is performed.",
    ]
    if blocked:
        lines.append("Core blocking jobs: " + ", ".join(blocked))
    output = "\n".join(lines) + "\n"
    print(output)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(output)
    return int(bool(blocked))


if __name__ == "__main__":
    raise SystemExit(main())
