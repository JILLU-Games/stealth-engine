# GitHub Actions Production Validation — CI Setup & Acceptance Record

**State:** WORKFLOW PREPARED / STATIC-VALIDATED / **NOT EXECUTED ON GITHUB**. No GitHub repo or runner was connected for this implementation. This is a CI harness, **not a production-ready certificate**.

**GitLab source snapshot (before workflow):** `2b517514dd551225e0c4daf50c88ea6559c3cd31`, containing P-01–P-05 patches. `notes/productions/11`–`13` document release-gate blockers. The workflow is deliberately not a code fix for them.

## Tracked files

- `.github/workflows/production-validation.yml` — Linux/Windows regression matrix, actual Camoufox smoke and browserforge canaries, clean wheel/sdist builds, F-19 security contract, opt-in external proxy check, fail-closed aggregate verdict.
- `.github/ci/junit_gate.py` — checks JUnit counts, fails unexpected test skip and failures; writes GitHub step summary.
- `.github/ci/package_gate.py` — wheel/sdist build and `twine` check, independent virtualenv install/import outside repository.
- `.github/ci/logging_security_gate.py` — synthetic nested secret check for the still-open F-19 gap (expected failure on current source).
- `.github/ci/external_proxy_gate.py` — opt-in authenticated proxy through real browser, requiring configured HTTPS JSON endpoint with `{"ip": "..."}` and expected public egress IP. **Not a DNS/WebRTC leak guarantee.**
- `.github/ci/release_gate.py` — reports job statuses and blocks when any required gate fails/is skipped; does not tag or release.

## Import and run

1. Import the **complete GitLab repository**, preserving its `.github/workflows/production-validation.yml` path, to your own GitHub repo; choose `main` as the default branch. Do not copy only `.py` files; the `.github/` directory is essential.
2. On GitHub, open **Actions → Production Validation (no release) → Run workflow → main → Run workflow**. The workflow also runs on pushes to `main` and pull requests; no secrets are exposed to PR jobs.
3. Inspect the individual jobs: `Regression` (Python 3.10/3.12/3.13 on Ubuntu; Python 3.12 on Windows), `Real Camoufox` (Ubuntu/Windows), `Clean wheel and sdist` (Ubuntu/Windows), `F-19 nested log-secret contract`, `Real external proxy egress`, and `Aggregate CI verdict`.
4. Open the **Summary** and download artifacts named `regression-*`, `real-browser-*`, `package-*`. The regression/browser artifacts contain JUnit XML plus installed dependency versions. Artifacts may be absent if a job fails before generating them; that is **not** a pass. Raw external-proxy traces are not uploaded because of credential risk.
5. Expect **FAIL/NO-GO initially**: the last read-only audit observed 8 full-suite failures (with local dependency stubs), F-19 nested-sanitizer failure, and absent real-browser/Windows evidence. New CI results, not historic offline figures, determine current state.

## Optional real external proxy gate (manual only)

In your GitHub repository select **Settings → Secrets and variables → Actions → New repository secret**. Create:

| Secret | Meaning |
|---|---|
| `CI_PROXY_SERVER` | Authorized HTTP/HTTPS/SOCKS4/SOCKS5 proxy endpoint with host and port, e.g. `socks5://host:1080`; put username/password separately, not in the URL |
| `CI_PROXY_USERNAME` | Authentication username, when required |
| `CI_PROXY_PASSWORD` | Authentication password, when required |
| `CI_EGRESS_JSON_URL` | HTTPS IP-check endpoint you trust/control that returns JSON such as `{"ip":"203.0.113.42"}` (example is illustrative, not a public IP for validation) |
| `CI_EXPECTED_EXIT_IP` | The **real publicly routable** proxy exit IP expected from that endpoint |

Then open **Actions → Run workflow**, set `run_external_proxy = true`. On automatic push/PR or without this opt-in, the external gate is SKIPPED and aggregate result is **BLOCKED**, not a fake green release approval. For security, secrets are not passed to untrusted pull requests.

**Do not use credentials you are not authorized to test.** The endpoint must be an HTTPS URL returning a JSON object with an `ip` property. This checks IP egress only; it does not establish the absence of DNS/STUN/WebRTC leaks or that fingerprint consistency is achieved.

## Existing real-browser tests used (not invented substitutes)

- `tests/test_smoke.py::RealBrowserSmokeTests::test_launch_about_blank_and_close` — Camoufox launch, page/navigation/close.
- `tests/test_smoke.py::RealBrowserSmokeTests::test_verify_stealth_real_browser` — browser probe/summary.
- `tests/test_smoke.py::FingerprintCanaryTests` — real browserforge fingerprint generation and validation; these canaries are browser-independent but need the actual provider.

The browser job runs with `STEALTH_SMOKE=1`, `STEALTH_CANARY=1`, installs `camoufox[geoip]` and runs `python -m camoufox fetch` **without mocking**. `junit_gate.py` fails if the four browser/canary cases are skipped or absent. The full-regression job leaves these flags disabled and expects exactly four documented skips in `tests/test_smoke.py`; other skips fail the gate.

## Automated acceptance vs real production certification

The 12 gates from [`13-RELEASE-GATE-ACCEPTANCE-MATRIX.md`](13-RELEASE-GATE-ACCEPTANCE-MATRIX.md) remain the release source of truth:

| Gate group | What the new workflow can actually run | Not fully proven by the workflow |
|---|---|---|
| G-01, G-05, G-08 | Real Camoufox launch/probe, generated-fingerprint canaries; existing unit route/noise tests | Browser-visible fingerprint parity for all properties, real public-domain tracker routes, anti-detection claims |
| G-02, G-06, G-10 | Windows test runner and package installation, Python compatibility subset | Two-process crash recovery under real user profile/ACL policies; all supported OS/Python versions |
| G-03, G-04 | Local SOCKS tests in full regression; opt-in **real proxy exit-IP** probe | External DNS/WebRTC/STUN leak checks and NAT behavior require separate controlled endpoint/integration |
| G-07 | Dedicated synthetic nested logging-secret regression; currently known to fail | Global module logger profile isolation remains a separate security design/acceptance gate |
| G-09 | Full existing suite with **real dependencies**, JUnit and zero unexpected skip enforcement | No guarantee of pass before CI actually executes; previously known 8 failures are unmodified |
| G-11 | Wheel + sdist build, `twine check`, fresh virtualenv install/import on Linux and Windows | Exact dependency lock/reproducible release builds not provided by this workflow |
| G-12 | GitHub Actions per-commit logs/artifacts | No pipeline run yet; no tag, protected release or attestation job installed |

**Interpretation:** `Aggregate CI verdict: AUTOMATED JOBS PASSED` means only the configured jobs ran successfully. It is **not** permission to label the project production-ready while the documented Windows/real-network/WebRTC/F-19 acceptance is missing. The aggregate job fails if the proxy job is SKIPPED or any job fails; it cannot create a release.

## Verification performed before commit

- GitLab baseline HEAD and unchanged source/test blobs checked; no application source changed.
- Workflow YAML parsed; defined job graph and event triggers checked.
- All CI Python helper scripts compiled with `ast`/`py_compile`; synthetic JUnit pass/fail/skip parser cases exercised; release summarizer missing/skipped job cases exercised.
- **GitHub-hosted Actions were not run here**. Real dependency installation, browser fetch, Windows runners, external proxy, and packaging build are **NOT RUN**. Actual runner compatibility can only be verified when you import to GitHub and execute Actions.

**Security / scope:** no PR secrets, no `pull_request_target`, read-only `GITHUB_TOKEN`, no repository writes, no real credentials committed, no source fixes, no automatic tag/publish/deploy.
