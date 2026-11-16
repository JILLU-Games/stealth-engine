# GitHub Actions Core Release Pipeline — v0.3.0

**Purpose:** publish one scoped Core prerelease from an exact successful GitHub CI commit.  
**Release:** `v0.3.0` / Python package version `0.3.0`.  
**License:** MIT. **Visibility:** private GitHub repository.  
**No local EXE, Nuitka build or PYD binary.**

## How the automatic publication works

1. One authorized commit with the exact subject `release(core): v0.3.0 release workflow` lands on `main`.
2. Existing `Production Validation (no release)` executes all Core gates including the new release metadata contract; an external proxy is explicitly not required for the **Core-only** gate.
3. `.github/workflows/core-release.yml` listens for **completion** of that CI. It runs only for `push` events on the same repository's `main` with a **successful** conclusion.
4. The publish job checks out the exact CI-tested SHA, confirms it is still `main`, compares the official workflow run status, verifies the exact release commit subject and refuses existing tags/releases.
5. It builds `stealth_engine-0.3.0-py3-none-any.whl` and `stealth_engine-0.3.0.tar.gz`, executes fresh isolated wheel **and sdist** installations, and writes a dependency snapshot.
6. The release helper creates seven assets: the two Python distributions, `LICENSE`, `RELEASE_NOTES.md`, `BUILD_PROVENANCE.json`, `DEPENDENCY_SNAPSHOT.txt`, `SHA256SUMS.txt`. Every asset except the manifest is SHA256-verified.
7. GitHub Actions `gh release create` creates the `v0.3.0` tag pointing at the **exact successful CI commit**, uploads the assets and marks the GitHub Release **prerelease**, not latest.
8. Postpublish the workflow verifies tag SHA, exact assets and prerelease status. No deployments follow.
9. Only after the GitHub Release is verified should the matched source/workflow/notes be synchronized to GitLab. GitLab mirrored commit IDs differ; file blob hashes must match.

## Scope and risk acceptance

- **Accepted Core scope:** direct-host, controlled localhost HTTP proxy protocol, Windows/Linux profile security, live WebGL/canvas, package integrity and dependency audit on the CI-tested runners.
- **Explicitly NOT certified:** real third-party HTTP/SOCKS proxies, their DNS/WebRTC leak properties, any anti-bot detection guarantee, full browserforge parity or arbitrary user operating environments.
- The package remains `0.3.0` Beta/preview. Release packaging does not bundle Camoufox browser binaries and needs `python -m camoufox fetch` for a usable runtime.
- The release dependency snapshot is environment-specific; it is not a cross-platform lockfile. No promise of future byte-identical dependency resolution.
- GitHub Actions `contents: write` must be permitted for the publisher job. If org policy denies writes, the job fails without claiming publication.

## Evidence

- [Core acceptance baseline](16-CORE-PRODUCTION-ACCEPTANCE.md) / [GitHub Actions Run #8](https://github.com/JILLU-Games/stealth-engine/actions/runs/43948468121).
- [Release workflow](https://github.com/JILLU-Games/stealth-engine/blob/main/.github/workflows/core-release.yml).
- [Release notes](https://github.com/JILLU-Games/stealth-engine/blob/main/notes/releases/v0.3.0.md).
- **Actual published release:** [v0.3.0 Core Preview](https://github.com/JILLU-Games/stealth-engine/releases/tag/v0.3.0) (GitHub release publisher [Run #43956108813](https://github.com/JILLU-Games/stealth-engine/actions/runs/43956108813), SUCCESS; exact Core CI [Run #43955132352](https://github.com/JILLU-Games/stealth-engine/actions/runs/43955132352), SUCCESS). Published prerelease tag SHA: `b695b2c6eee3c207132c6a58e2ea8993a50ad921`. See [18-CORE-RELEASE-PUBLICATION-EVIDENCE.md](18-CORE-RELEASE-PUBLICATION-EVIDENCE.md).

**Verified:** the release publisher checked the exact successful Core CI commit, published the prerelease and verified all seven assets and the tag SHA. No full external-proxy certification is claimed.
