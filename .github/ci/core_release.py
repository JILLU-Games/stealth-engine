"""Fail-closed packaging metadata and checksums for the scoped Core prerelease.

This helper does not create tags, GitHub releases or deployments. The trusted
release workflow performs the actual publish after verifying Core CI.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

PROJECT = Path(__file__).resolve().parents[2]
VERSION = "0.3.0"
TAG = "v0.3.0"
NOTES = PROJECT / "notes" / "releases" / "v0.3.0.md"
DIST = PROJECT / "dist"
OUT = PROJECT / "release-assets"
FILES = {
    "LICENSE", "RELEASE_NOTES.md", "DEPENDENCY_SNAPSHOT.txt",
    "BUILD_PROVENANCE.json", "SHA256SUMS.txt",
}


def fail(message: str) -> None:
    raise SystemExit("CORE RELEASE GATE FAILURE: " + message)


def validate() -> None:
    metadata = tomllib.loads((PROJECT / "pyproject.toml").read_text(encoding="utf-8"))
    if metadata["project"]["name"] != "stealth_engine":
        fail("unexpected package name")
    if metadata["project"]["version"] != VERSION:
        fail("pyproject.toml version differs from release version")
    init = (PROJECT / "stealth_engine" / "__init__.py").read_text(encoding="utf-8")
    if not re.search(r'^__version__:\s*str\s*=\s*"' + re.escape(VERSION) + r'"', init, re.M):
        fail("package __version__ differs")
    license_text = (PROJECT / "LICENSE").read_text(encoding="utf-8")
    if not license_text.startswith("MIT License") or "Copyright" not in license_text:
        fail("MIT LICENSE is absent or malformed")
    release_text = NOTES.read_text(encoding="utf-8")
    for term in ("Core Preview", "UNVERIFIED", "prerelease", "SHA256SUMS.txt"):
        if term not in release_text:
            fail("release notes fail explicit scope/limitation contract: " + term)
    print(f"RELEASE PREFLIGHT PASS: {VERSION}, MIT, prerelease disclosure")


def _dist_files() -> list[Path]:
    wheel = list(DIST.glob("stealth_engine-0.3.0-*.whl"))
    sdist = list(DIST.glob("stealth_engine-0.3.0.tar.gz"))
    if len(wheel) != 1 or len(sdist) != 1:
        fail("exactly one 0.3.0 wheel and one 0.3.0 sdist required")
    return [wheel[0], sdist[0]]


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def assemble() -> None:
    validate()
    sha = os.environ.get("VALIDATED_SHA", "")
    run_id = os.environ.get("CORE_RUN_ID", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        fail("validated Core CI commit SHA missing")
    if not run_id.isdecimal() or not repo or "/" not in repo:
        fail("CI run ID/repository missing")
    snapshot = PROJECT / "dependency-versions.txt"
    if not snapshot.is_file() or not snapshot.read_text(encoding="utf-8").strip():
        fail("dependency freeze snapshot missing")
    if OUT.exists():
        fail("refusing to reuse release-assets from another build")
    OUT.mkdir()
    packages = _dist_files()
    for path in packages:
        shutil.copy2(path, OUT / path.name)
    shutil.copy2(NOTES, OUT / "RELEASE_NOTES.md")
    shutil.copy2(PROJECT / "LICENSE", OUT / "LICENSE")
    shutil.copy2(snapshot, OUT / "DEPENDENCY_SNAPSHOT.txt")
    provenance = {
        "package": "stealth_engine", "version": VERSION, "tag": TAG,
        "scope": "direct-host Core preview",
        "external_proxy_certification": "UNVERIFIED",
        "source_sha": sha, "core_ci_workflow_run_id": int(run_id),
        "core_ci_url": f"https://github.com/{repo}/actions/runs/{run_id}",
        "repository": repo, "builder": "GitHub Actions / ubuntu-24.04 / Python 3.12",
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT / "BUILD_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    signed = sorted(path for path in OUT.iterdir() if path.is_file())
    (OUT / "SHA256SUMS.txt").write_text(
        "".join(f"{checksum(path)}  {path.name}\n" for path in signed),
        encoding="utf-8",
    )
    verify()
    print(f"RELEASE BUNDLE ASSEMBLED: {len(signed) + 1} files")


def verify() -> None:
    wheel = list(OUT.glob("stealth_engine-0.3.0-*.whl"))
    sdist = list(OUT.glob("stealth_engine-0.3.0.tar.gz"))
    if len(wheel) != 1 or len(sdist) != 1:
        fail("missing or duplicate core package artifacts")
    names = {p.name for p in OUT.iterdir() if p.is_file()}
    expected = FILES | {wheel[0].name, sdist[0].name}
    if names != expected:
        fail("release bundle file set differs: " + repr(sorted(names ^ expected)))
    lines = (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    if len(lines) != len(expected) - 1:
        fail("unexpected checksum manifest length")
    seen: set[str] = set()
    for line in lines:
        if not re.fullmatch(r"[0-9a-f]{64}  [^/\\]+", line):
            fail("invalid SHA256SUMS line")
        digest, name = line.split("  ", 1)
        if name in seen or name not in expected or name == "SHA256SUMS.txt":
            fail("checksum entry missing or duplicated")
        if checksum(OUT / name) != digest:
            fail("release artifact digest mismatch: " + name)
        seen.add(name)
    if seen != expected - {"SHA256SUMS.txt"}:
        fail("some release bundle files have no hashes")
    provenance = json.loads((OUT / "BUILD_PROVENANCE.json").read_text(encoding="utf-8"))
    if provenance["external_proxy_certification"] != "UNVERIFIED":
        fail("proxy limitation was incorrectly certified")
    if provenance["version"] != VERSION or provenance["tag"] != TAG:
        fail("version/provenance mismatch")
    print("RELEASE ARTIFACT INTEGRITY PASS")


def verify_remote(filename: str) -> None:
    info = json.loads(Path(filename).read_text(encoding="utf-8"))
    if info.get("tagName") != TAG or info.get("isPrerelease") is not True:
        fail("published release tag/prerelease flags differ")
    local = {p.name for p in OUT.iterdir() if p.is_file()}
    remote = {item["name"] for item in info.get("assets", [])}
    if local != remote:
        fail("remote release asset set mismatch: " + repr(sorted(local ^ remote)))
    print("PUBLISHED RELEASE VERIFICATION PASS:", info.get("url", ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("validate", "assemble", "verify", "verify-remote"))
    parser.add_argument("file", nargs="?")
    args = parser.parse_args()
    if args.operation == "validate":
        validate()
    elif args.operation == "assemble":
        assemble()
    elif args.operation == "verify":
        verify()
    elif args.file:
        verify_remote(args.file)
    else:
        fail("verify-remote requires release details file")
