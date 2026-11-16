# Published Core Release — v0.3.0

**Verified GitHub Release:** https://github.com/JILLU-Games/stealth-engine/releases/tag/v0.3.0  
**Published GitHub Actions workflow run:** https://github.com/JILLU-Games/stealth-engine/actions/runs/43956108813 — **SUCCESS**  
**Release-triggering Core CI:** https://github.com/JILLU-Games/stealth-engine/actions/runs/43955132352 — **SUCCESS**  
**Exact immutable tag / source commit:** `b695b2c6eee3c207132c6a58e2ea8993a50ad921`  
**Release type:** published GitHub **prerelease** (Core Preview), **not** full external-proxy GA.  
**License:** MIT. **Visibility:** private GitHub organization repository.

## Actual verified GitHub Release assets

| Asset | Size (bytes) | Evidence |
|---|---:|---|
| `stealth_engine-0.3.0-py3-none-any.whl` | 78,860 | Built/clean-installed through GitHub Actions |
| `stealth_engine-0.3.0.tar.gz` | 111,617 | Sdist + fresh-venv installation verified |
| `BUILD_PROVENANCE.json` | 515 | Exact source SHA, CI run ID, build metadata |
| `DEPENDENCY_SNAPSHOT.txt` | 1,537 | Build-run Python environment versions; **not** universal lock |
| `LICENSE` | 1,066 | MIT text |
| `RELEASE_NOTES.md` | 3,146 | Scoped support statement and limitations |
| `SHA256SUMS.txt` | 533 | SHA256 manifest of every other release asset |

The publisher verified **7/7 release assets** and the tag target SHA before
marking the workflow successful. A copy of release build evidence was uploaded
as GitHub Actions artifact `core-release-build-evidence`.

## Security and release scope

- The initial publisher correctly refused to release after a Windows
  dead-owner lock regression exposed a bug. Windows process liveness now uses
  `GetExitCodeProcess` rather than OpenProcess handle existence alone. A new
  terminated-child acceptance test passed in the release CI.
- The first successful Core CI release request was then blocked by missing
  `actions:read` permission to query the Core CI run. Publisher permissions
  were corrected without broadening write access beyond the release job.
- Both the final release CI and publisher passed for the **same SHA**.
- Real external HTTP/SOCKS proxy egress/auth, remote DNS, proxy-specific
  WebRTC leaks and arbitrary target environments remain **UNVERIFIED**.
- Experimental JS noise and third-party anti-detection behavior are **not**
  guaranteed; profile-global logging remains a documented limitation.
- Release artifacts are pure Python distributions, not a Windows EXE or
  compiled PYD module. Camoufox browser fetching remains separate.
- The SHA256 manifest and JSON provenance are audit metadata, **not signed
  supply-chain attestations or a cross-platform reproducible dependency lock**.

## GitLab synchronization

The GitLab `main` mirror must contain the same executable/workflow/docs blob
content, but its Git commit SHA is independent of GitHub's. GitHub Release and
its `v0.3.0` tag are the authoritative published distribution source. This
record does **not** claim a separate GitLab Release or GitLab tag was created.

**Final decision:** v0.3.0 Core Preview prerelease **PUBLISHED** under its
defined Core acceptance scope. Full external-proxy production certification
remains **NOT ESTABLISHED**.
