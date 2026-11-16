# Security Policy

## Reporting a vulnerability

Please report security issues privately to **hello@vibtools.io** with "stealth_engine security" in the subject line. Do not open public issues for unpatched vulnerabilities.

## Scope

This package handles browser fingerprints, proxies, cookies, and session state. Relevant concerns include:

- Credential or cookie leakage into logs, errors, or exported files
- Cross-profile state leakage (cookies, storage, locks)
- Fingerprint inconsistencies that could deanonymise a profile
- Unsafe deserialization of config/state files

## Supported versions

Only the latest release line is supported. Check `CHANGELOG.md` for the current version.

## Notes

- `docs/SECURITY.md` documents the stealth model, guarantees, and known limitations.
- The engine does not transmit telemetry; all network calls are caller-initiated.
