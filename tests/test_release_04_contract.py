"""Offline tests for release metadata, authorization and integrity gates."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_04_contract", ROOT / ".github/ci/core_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
SHA = "a" * 40
RUN = 123


def evidence():
    workflow = {"id": 42, "path": release.WORKFLOW_PATH}
    run = {"id": RUN, "workflow_id": 42, "path": release.WORKFLOW_PATH,
           "head_sha": SHA, "head_branch": "main", "event": "push",
           "status": "completed", "conclusion": "success", "run_attempt": 1,
           "head_repository": {"full_name": release.REPOSITORY},
           "repository": {"full_name": release.REPOSITORY}}
    records = [{"id": i, "name": f"required-{i}", "status": "completed",
                "conclusion": "success"} for i in range(19)]
    records += [{"id": 19, "name": release.AGGREGATE_JOB, "status": "completed",
                 "conclusion": "success"},
                {"id": 20, "name": release.EXTERNAL_JOB, "status": "completed",
                 "conclusion": "skipped"}]
    return run, workflow, {"total_count": 21, "jobs": records}


class Release04ContractTests(unittest.TestCase):
    def test_version_and_workflow_contract(self):
        self.assertIn('version = "0.4.0"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn('__version__: str = "0.4.0"', (ROOT / "stealth_engine/__init__.py").read_text(encoding="utf-8"))
        self.assertEqual(release.VERSION, "0.4.0")
        import yaml
        data = yaml.load((ROOT / ".github/workflows/release-v040.yml").read_text(encoding="utf-8"),
                         Loader=yaml.BaseLoader)
        self.assertEqual(set(data["on"]), {"workflow_dispatch"})
        self.assertEqual(data["permissions"]["contents"], "read")
        self.assertIn("refs/heads/main", data["jobs"]["publish"]["if"])
        self.assertEqual(set(data["on"]["workflow_dispatch"]["inputs"]),
                         {"validated_sha", "core_run_id", "confirmation"})

    def test_exact_core_ci_evidence(self):
        run, workflow, jobs = evidence()
        release.verify_ci_evidence(run, workflow, jobs, SHA, RUN)

    def test_reject_invalid_ci_evidence(self):
        for key, value in (("head_sha", "b" * 40), ("event", "pull_request"),
                           ("head_branch", "dev"), ("conclusion", "failure"),
                           ("workflow_id", 43), ("status", "in_progress"),
                           ("head_repository", {"full_name": "other/repo"})):
            with self.subTest(key=key):
                run, workflow, jobs = evidence()
                run[key] = value
                with self.assertRaises(SystemExit):
                    release.verify_ci_evidence(run, workflow, jobs, SHA, RUN)

    def test_reject_incomplete_or_failed_jobs(self):
        for mutation in ("aggregate", "extra-skip", "missing", "duplicate"):
            with self.subTest(mutation=mutation):
                run, workflow, jobs = evidence()
                if mutation == "aggregate":
                    jobs["jobs"][19]["conclusion"] = "failure"
                elif mutation == "extra-skip":
                    jobs["jobs"][0]["conclusion"] = "skipped"
                elif mutation == "missing":
                    jobs["jobs"].pop()
                else:
                    jobs["jobs"][1]["id"] = jobs["jobs"][0]["id"]
                with self.assertRaises(SystemExit):
                    release.verify_ci_evidence(run, workflow, jobs, SHA, RUN)

    def test_reject_unauthorized_dispatch_without_network(self):
        with patch.dict(os.environ, {"RELEASE_CONFIRMATION": "no"}, clear=True), patch.object(
                release, "github_json") as api:
            with self.assertRaises(SystemExit):
                release.publication_preflight()
            api.assert_not_called()

    def test_reject_duplicate_tag_or_draft(self):
        run, workflow, jobs = evidence()
        env = {"RELEASE_CONFIRMATION": "PUBLISH v0.4.0", "GITHUB_EVENT_NAME": "workflow_dispatch",
               "GITHUB_REPOSITORY": release.REPOSITORY, "GITHUB_REF": "refs/heads/main",
               "GITHUB_SHA": SHA, "VALIDATED_SHA": SHA, "CORE_RUN_ID": str(RUN)}
        for duplicate in ("tag", "draft", None):
            with self.subTest(duplicate=duplicate):
                responses = [{"object": {"sha": SHA}}, workflow, run, jobs,
                             {"object": {"sha": SHA}} if duplicate == "tag" else None]
                if duplicate != "tag":
                    responses.append([{"tag_name": release.TAG, "draft": True}] if duplicate == "draft" else [])
                with patch.dict(os.environ, env, clear=True), patch.object(
                        release.subprocess, "check_output", return_value=SHA), patch.object(
                        release, "github_json", side_effect=responses):
                    if duplicate is None:
                        release.publication_preflight()
                    else:
                        with self.assertRaises(SystemExit):
                            release.publication_preflight()

    def test_non_404_api_failure_not_treated_as_absence(self):
        from urllib.error import HTTPError
        for status in (403, 429, 500):
            with self.subTest(status=status), patch.dict(os.environ, {"GH_TOKEN": "test"}), patch.object(
                    release, "urlopen", side_effect=HTTPError("https://example.invalid", status, "", None, None)):
                with self.assertRaises(SystemExit):
                    release.github_json("git/ref/tags/v0.4.0", missing_ok=True)

    def test_downloaded_asset_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            local = Path(td) / "local"
            remote = Path(td) / "remote"
            local.mkdir()
            remote.mkdir()
            names = release.FILES | {"stealth_engine-0.4.0-py3-none-any.whl",
                                     "stealth_engine-0.4.0.tar.gz"}
            for name in names:
                (local / name).write_bytes(name.encode())
                (remote / name).write_bytes(name.encode())
            with patch.object(release, "OUT", local), patch.object(release, "verify"):
                release.verify_download(str(remote))
                (remote / "LICENSE").write_bytes(b"modified")
                with self.assertRaises(SystemExit):
                    release.verify_download(str(remote))

    def test_remote_metadata_and_duplicate_asset_rejection(self):
        with tempfile.TemporaryDirectory() as td:
            local = Path(td) / "local"
            local.mkdir()
            (local / "LICENSE").write_text("MIT", encoding="utf-8")
            path = Path(td) / "remote.json"
            good = {"tagName": release.TAG, "isPrerelease": True, "isDraft": True,
                    "targetCommitish": SHA, "assets": [{"name": "LICENSE"}]}
            with patch.object(release, "OUT", local), patch.dict(os.environ, {"VALIDATED_SHA": SHA}):
                path.write_text(json.dumps(good), encoding="utf-8")
                release.verify_remote(str(path), draft=True)
                for change in ({"isPrerelease": False}, {"isDraft": False},
                               {"targetCommitish": "b" * 40},
                               {"assets": [{"name": "LICENSE"}, {"name": "LICENSE"}]}):
                    bad = copy.deepcopy(good)
                    bad.update(change)
                    path.write_text(json.dumps(bad), encoding="utf-8")
                    with self.assertRaises(SystemExit):
                        release.verify_remote(str(path), draft=True)
