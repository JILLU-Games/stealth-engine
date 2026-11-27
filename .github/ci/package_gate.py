"""Locked Python CI environments and package acceptance. No publication."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parents[2]
LOCKS = {
    "linux-3.10": ("835ed43e71dd6f080f1a10c986693bc50c339012ae28dd53c86063337156992e", 69),
    "linux-3.11": ("f72ebfc989611ff0ff359d4d8533ef2fc2dbdb69cdd930576ba9ee0e68a230db", 103),
    "linux-3.12": ("9478f5f26e4b4bc54c1609ed88d5bfb9fcab5c001236f1c3868c2fd9380a1bc9", 99),
    "linux-3.13": ("087baed0ffba84d8dbbf0240be5c233f2d6c981882bd171680edb8426e4e4982", 99),
    "windows-3.12": ("96370d8a1d63de7bb95e869f7eda5ba0dd77ebce7720d5ac94e6b5d023e230ef", 99),
}
ROW = re.compile(r"([a-z0-9-]+)==([^\s]+) --hash=sha256:([a-f0-9]{64})")


def run(args, **kwargs):
    subprocess.run([str(a) for a in args], check=True, **kwargs)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_key():
    system = {"Linux": "linux", "Windows": "windows"}.get(platform.system())
    key = f"{system}-{sys.version_info.major}.{sys.version_info.minor}"
    if key not in LOCKS or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise RuntimeError(f"Unsupported locked CI environment: {key}/{platform.machine()}")
    return key


def verified_lock(key, directory):
    relative = f"requirements/ci-{key}.lock"
    data = git("show", f"HEAD:{relative}")
    expected, count = LOCKS[key]
    if hashlib.sha256(data).hexdigest() != expected:
        raise RuntimeError(f"Committed lock SHA256 mismatch: {key}")
    if (ROOT / relative).read_bytes().replace(b"\r\n", b"\n") != data.replace(b"\r\n", b"\n"):
        raise RuntimeError(f"Working lock differs from Git blob: {key}")
    lines = data.decode("ascii").splitlines()
    if lines[0] != "# Native GitHub Actions resolver; official PyPI wheels only.":
        raise RuntimeError("Unexpected lock header")
    pins = {}
    for line in lines[1:]:
        match = ROW.fullmatch(line)
        if not match or match[1] in pins:
            raise RuntimeError(f"Invalid or duplicate lock row: {key}")
        pins[match[1]] = (match[2], match[3])
    if len(pins) != count:
        raise RuntimeError(f"Lock count mismatch: {key}")
    path = directory / f"ci-{key}.lock"
    path.write_bytes(data)
    return path, pins


def env_python(directory):
    venv.EnvBuilder(with_pip=True).create(directory)
    return directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def pip(python, *args):
    run([python, "-m", "pip", "--isolated", "--disable-pip-version-check", *args])


def install_locked(python, lock, wheelhouse):
    pip(python, "install", "--force-reinstall", "--no-index", "--find-links", wheelhouse,
        "--only-binary=:all:", "--require-hashes", "-r", lock)
    pip(python, "check")


def check_versions(python, pins, project=False):
    raw = subprocess.check_output([str(python), "-I", "-c",
        "import importlib.metadata as m,json; print(json.dumps([(d.metadata['Name'],d.version) for d in m.distributions()]))"])
    actual = {}
    for name, version in json.loads(raw):
        name = re.sub(r"[-_.]+", "-", name).lower()
        if name in actual:
            raise RuntimeError(f"Duplicate installed distribution: {name}")
        actual[name] = version
    expected = {name: value[0] for name, value in pins.items()}
    if project:
        expected["stealth-engine"] = "0.4.0"
    if actual != expected:
        raise RuntimeError(f"Installed dependency set differs from lock: missing={sorted(expected.keys()-actual.keys())}, extra={sorted(actual.keys()-expected.keys())}, mismatched={sorted(k for k in actual.keys() & expected.keys() if actual[k] != expected[k])}")


def prepare(project):
    key = selected_key()
    staging = Path(tempfile.mkdtemp(prefix="locked-python-", dir=os.environ["RUNNER_TEMP"]))
    lock, pins = verified_lock(key, staging)
    wheelhouse = staging / "wheelhouse"
    wheelhouse.mkdir()
    python = env_python(staging / "environment")
    pip(python, "download", "--index-url", "https://pypi.org/simple", "--no-cache-dir",
        "--no-deps", "--only-binary=:all:", "--require-hashes", "-r", lock, "--dest", wheelhouse)
    if sorted(digest(p) for p in wheelhouse.glob("*.whl")) != sorted(v[1] for v in pins.values()):
        raise RuntimeError("Wheelhouse SHA256 set does not match committed lock")
    install_locked(python, lock, wheelhouse)
    if project:
        args = ["install", "--no-index", "--no-deps", "--no-build-isolation"]
        if project == "editable":
            args.append("-e")
        pip(python, *args, ROOT)
        pip(python, "check")
    check_versions(python, pins, bool(project))
    with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as stream:
        stream.write(str(python.parent) + "\n")
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as stream:
        stream.write(f"LOCKED_PYTHON_STAGE={staging}\n")
    print(f"LOCKED ENVIRONMENT PASS: {key} {len(pins)} {digest(lock)}")


def package():
    key = selected_key()
    staging = Path(os.environ["LOCKED_PYTHON_STAGE"])
    lock, pins = verified_lock(key, staging)
    wheelhouse = staging / "wheelhouse"
    check_versions(sys.executable, pins)
    dist = ROOT / "dist"
    if dist.exists():
        raise RuntimeError("Distribution directory must be absent before clean build")
    run([sys.executable, "-m", "build", "--no-isolation", "--outdir", dist], cwd=ROOT)
    wheels, sdists = sorted(dist.glob("*.whl")), sorted(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError("Expected exactly one wheel and one source distribution")
    if sys.version_info[:2] == (3, 12):
        run([sys.executable, "-m", "twine", "check", wheels[0], sdists[0]], cwd=ROOT)
    else:
        print("Metadata check retained in both Python 3.12 package jobs")
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    for label, artifact in (("wheel", wheels[0]), ("sdist", sdists[0])):
        with tempfile.TemporaryDirectory(prefix=f"package-{label}-", dir=staging) as directory:
            sandbox = Path(directory)
            python = env_python(sandbox / "venv")
            install_locked(python, lock, wheelhouse)
            check_versions(python, pins)
            pip(python, "install", "--no-index", "--no-deps", "--no-build-isolation", artifact)
            pip(python, "check")
            check_versions(python, pins, True)
            run([python, "-I", "-c",
                 "import importlib.metadata as m, pathlib, sys, stealth_engine; "
                 "from stealth_engine import ProfileConfig, StealthEngine; "
                 "assert m.version('stealth_engine') == stealth_engine.__version__ == '0.4.0'; "
                 "assert pathlib.Path(stealth_engine.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve()); "
                 "print('Installed package:', m.version('stealth_engine'))"], cwd=sandbox)
            (reports / f"{label}-dependency-versions.txt").write_bytes(
                subprocess.check_output([str(python), "-m", "pip", "freeze", "--all"]))
            print(f"FRESH {label.upper()} INSTALL PASS")
    hashes = {p.name: digest(p) for p in wheels + sdists}
    (reports / "SHA256SUMS.txt").write_text("".join(f"{h}  {name}\n" for name, h in sorted(hashes.items())), encoding="utf-8")
    provenance = {"source_commit": git("rev-parse", "HEAD").decode().strip(),
                  "source_tree": git("rev-parse", "HEAD^{tree}").decode().strip(),
                  "source_archive_sha256": hashlib.sha256(git("archive", "--format=tar", "HEAD")).hexdigest(),
                  "run_id": os.environ.get("GITHUB_RUN_ID"), "platform": key,
                  "python": sys.version, "lock_sha256": digest(lock), "artifacts": hashes,
                  "scope": "Python wheel dependencies and package artifacts; no release; not a bitwise reproducibility claim"}
    (reports / "build-provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("PACKAGE GATE PASS: independent locked wheel and sdist installs")


def audit():
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    stage = Path(os.environ["LOCKED_PYTHON_STAGE"])
    failures = []
    for key in LOCKS:
        lock, pins = verified_lock(key, stage)
        req = stage / f"audit-{key}.txt"
        req.write_text("".join(f"{name}=={version}\n" for name, (version, _) in sorted(pins.items())), encoding="utf-8")
        result = subprocess.run([sys.executable, "-m", "pip_audit", "--no-deps", "--disable-pip", "--strict",
                                 "-r", str(req), "--format", "json", "--output", str(reports / f"audit-{key}.json")])
        if result.returncode:
            failures.append(key)
    tracked = {p[6:] for p in git("ls-tree", "-r", "--name-only", "HEAD", "notes/").decode().splitlines() if p.startswith("notes/")}
    entries = re.findall(r"^\|\s*([^|]+?\.md)\s*\|", (ROOT/"notes/MANIFEST.md").read_text(encoding="utf-8"), re.M)
    entries = [x.strip() for x in entries]
    if len(entries) != len(set(entries)) or set(entries) != tracked:
        raise RuntimeError(f"Manifest mismatch: missing={sorted(tracked-set(entries))}, invalid={sorted(set(entries)-tracked)}")
    print(f"MANIFEST PASS: {len(tracked)} exact tracked paths")
    if failures:
        raise RuntimeError(f"Locked dependency audit failed: {failures}")
    print("ALL FIVE LOCK AUDITS PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("prepare", "package", "audit"))
    parser.add_argument("--project", choices=("editable", "regular"))
    args = parser.parse_args()
    if args.operation == "prepare":
        prepare(args.project)
    elif args.operation == "package":
        package()
    else:
        audit()
