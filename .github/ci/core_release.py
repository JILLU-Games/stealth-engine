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
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT = Path(__file__).resolve().parents[2]
VERSION = "0.4.0"
TAG = "v0.4.0"
NOTES = PROJECT / "notes" / "releases" / f"{TAG}.md"
REPOSITORY = "JILLU-Games/stealth-engine"
WORKFLOW_PATH = ".github/workflows/production-validation.yml"
AGGREGATE_JOB = "Aggregate CI verdict (NO automatic release)"
EXTERNAL_JOB = "Real external proxy egress (manual and secret-gated)"
DIST = PROJECT / "dist"
OUT = PROJECT / "release-assets"
FILES = {
    "LICENSE", "RELEASE_NOTES.md", "DEPENDENCY_SNAPSHOT.txt",
    "BUILD_PROVENANCE.json", "SHA256SUMS.txt",
}


def fail(message: str) -> None:
    raise SystemExit("CORE RELEASE GATE FAILURE: " + message)


def validate() -> None:
    import tomllib  # Release metadata validation runs on Python 3.12.
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
    wheel = list(DIST.glob(f"stealth_engine-{VERSION}-*.whl"))
    sdist = list(DIST.glob(f"stealth_engine-{VERSION}.tar.gz"))
    if len(wheel) != 1 or len(sdist) != 1:
        fail(f"exactly one {VERSION} wheel and one {VERSION} sdist required")
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
        "publication_workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "package_build_provenance": json.loads(
            (PROJECT / "reports" / "build-provenance.json").read_text(encoding="utf-8")
        ),
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
    wheel = list(OUT.glob(f"stealth_engine-{VERSION}-*.whl"))
    sdist = list(OUT.glob(f"stealth_engine-{VERSION}.tar.gz"))
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
    build = provenance.get("package_build_provenance", {})
    if (build.get("source_commit") != provenance.get("source_sha")
            or build.get("platform") != "linux-3.12"
            or build.get("run_id") != provenance.get("publication_workflow_run_id")
            or build.get("artifacts") != {p.name: checksum(p) for p in wheel + sdist}):
        fail("package build provenance or package hashes differ")
    print("RELEASE ARTIFACT INTEGRITY PASS")


def verify_ci_evidence(run, workflow, jobs, sha, run_id):
    """Pure exact-source Core CI evidence check; no publication side effects."""
    if (run.get("id") != run_id or run.get("workflow_id") != workflow.get("id")
            or workflow.get("path") != WORKFLOW_PATH or run.get("path") != WORKFLOW_PATH
            or run.get("head_sha") != sha or run.get("head_branch") != "main"
            or run.get("event") != "push" or run.get("status") != "completed"
            or run.get("conclusion") != "success"
            or (run.get("head_repository") or {}).get("full_name") != REPOSITORY
            or (run.get("repository") or {}).get("full_name") != REPOSITORY
            or not isinstance(run.get("run_attempt"), int) or run["run_attempt"] < 1):
        fail("Core CI run is not the exact successful main push workflow")
    records = jobs.get("jobs", [])
    if jobs.get("total_count") != 21 or len(records) != 21:
        fail("incomplete or unexpected Core CI job set")
    if len({j.get("id") for j in records}) != 21:
        fail("duplicate CI job")
    if any(j.get("status") != "completed" or j.get("conclusion") not in {"success", "skipped"} for j in records):
        fail("Core CI has incomplete or failed jobs")
    aggregate = [j for j in records if j.get("name") == AGGREGATE_JOB]
    skipped = [j.get("name") for j in records if j.get("conclusion") == "skipped"]
    if len(aggregate) != 1 or aggregate[0].get("conclusion") != "success" or skipped != [EXTERNAL_JOB]:
        fail("aggregate acceptance or expected external skip differs")


def github_json(path, *, missing_ok=False):
    """Authenticated read; only an actual HTTP 404 may mean absence."""
    token = os.environ.get("GH_TOKEN")
    if not token:
        fail("GitHub authorization token missing")
    request = Request("https://api.github.com/repos/" + REPOSITORY + "/" + path,
                      headers={"Authorization": "Bearer " + token,
                               "Accept": "application/vnd.github+json",
                               "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        if exc.code == 404 and missing_ok:
            return None
        fail(f"GitHub evidence lookup failed (HTTP {exc.code})")
    except (URLError, TimeoutError, ValueError):
        fail("GitHub evidence lookup failed")


def publication_preflight(*, require_absent=True):
    """Only a separately authorized manual dispatch on the accepted main SHA."""
    sha = os.environ.get("VALIDATED_SHA", "")
    raw_id = os.environ.get("CORE_RUN_ID", "")
    if (os.environ.get("RELEASE_CONFIRMATION") != "PUBLISH v0.4.0"
            or os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
            or os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or not re.fullmatch(r"[0-9a-f]{40}", sha)
            or os.environ.get("GITHUB_SHA") != sha
            or not re.fullmatch(r"[1-9][0-9]*", raw_id)):
        fail("manual publication authorization or exact main SHA missing")
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT, text=True).strip() != sha:
        fail("checked-out source differs from authorized SHA")
    if github_json("git/ref/heads/main").get("object", {}).get("sha") != sha:
        fail("main moved from authorized SHA")
    run_id = int(raw_id)
    workflow = github_json("actions/workflows/production-validation.yml")
    run = github_json(f"actions/runs/{run_id}")
    attempt = run.get("run_attempt")
    if not isinstance(attempt, int) or attempt < 1:
        fail("invalid CI attempt")
    jobs = github_json(f"actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100")
    verify_ci_evidence(run, workflow, jobs, sha, run_id)
    if require_absent:
        if github_json(f"git/ref/tags/{TAG}", missing_ok=True) is not None:
            fail("version tag already exists; no replacement")
        # Include drafts in the authenticated release listing. Refuse to proceed
        # if the API cannot establish absence within a bounded page count.
        for page in range(1, 101):
            releases = github_json(f"releases?per_page=100&page={page}")
            if not isinstance(releases, list):
                fail("unexpected release listing")
            if any(r.get("tag_name") == TAG for r in releases):
                fail("version release already exists; no replacement")
            if len(releases) < 100:
                break
        else:
            fail("release listing exceeded bounded verification")
    print("MANUAL PUBLICATION AUTHORIZATION PASS")


def verify_remote(filename: str, *, draft: bool = False) -> None:
    info = json.loads(Path(filename).read_text(encoding="utf-8"))
    if (info.get("tagName") != TAG or info.get("isPrerelease") is not True
            or info.get("isDraft") is not draft
            or info.get("targetCommitish") != os.environ.get("VALIDATED_SHA")):
        fail("remote release tag/target/prerelease/draft contract differs")
    local = {p.name for p in OUT.iterdir() if p.is_file()}
    records = info.get("assets", [])
    remote = {item["name"] for item in records}
    if local != remote or len(records) != len(local):
        fail("remote release asset set mismatch")
    print("REMOTE RELEASE METADATA PASS")


def verify_download(directory: str) -> None:
    """Compare independently downloaded bytes, including checksum manifest."""
    verify()
    remote = Path(directory)
    local = {p.name for p in OUT.iterdir() if p.is_file()}
    if {p.name for p in remote.iterdir()} != local:
        fail("downloaded release asset set mismatch")
    for name in sorted(local):
        if not (remote / name).is_file() or checksum(remote / name) != checksum(OUT / name):
            fail("downloaded release asset digest mismatch: " + name)
    print("DOWNLOADED RELEASE ASSET INTEGRITY PASS")


def verify_published_tag():
    tag = github_json(f"git/ref/tags/{TAG}").get("object", {})
    if tag.get("type") != "commit" or tag.get("sha") != os.environ.get("VALIDATED_SHA"):
        fail("published tag differs from exact authorized commit")
    print("PUBLISHED TAG PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("validate", "assemble", "verify", "authorize",
                                               "authorize-existing", "verify-draft",
                                               "verify-remote", "verify-download", "verify-tag"))
    parser.add_argument("file", nargs="?")
    args = parser.parse_args()
    if args.operation == "validate":
        validate()
    elif args.operation == "assemble":
        assemble()
    elif args.operation == "verify":
        verify()
    elif args.operation == "authorize":
        validate()
        publication_preflight()
    elif args.operation == "authorize-existing":
        validate()
        publication_preflight(require_absent=False)
    elif args.operation == "verify-tag":
        verify_published_tag()
    elif args.file and args.operation == "verify-download":
        verify_download(args.file)
    elif args.file:
        verify_remote(args.file, draft=args.operation == "verify-draft")
    else:
        fail("verification requires a file or directory")
