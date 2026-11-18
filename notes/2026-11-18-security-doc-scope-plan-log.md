# Security Document Scope Lock — Plan and Phase Log

## Plan

- **Authorization:** User approved a separate PR-02 Scope Lock for `docs/SECURITY.md` only on 2026-11-18.
- **Baseline:** Source remains `58c87e2b4de27e5a0510b628a623fcf6f1a1a96b`; v0.3.0 tag remains `b695b2c6eee3c207132c6a58e2ea8993a50ad921`.
- **Only product/reference target:** `docs/SECURITY.md`.
- **Procedural records:** this local plan/log, `notes/MANIFEST.md`, and the cumulative PR-02 status row in `notes/productions/22-PRODUCTION-READINESS-PHASE-LOG.md`.
- **Forbidden:** source, tests, workflows, public API/schema, UI, examples, release/tag/branch, runtime profile data, all other project/reference/security docs, and `docs/ROADMAP-v2-FREEZE.md`.
- **Goal:** Replace claims of guaranteed stealth/coherence, leak prevention, universal profile isolation, and deterministic identity with only source- and release-evidence-backed statements. Correct unsupported Firefox video/CDP descriptions.
- **Expected result:** `docs/SECURITY.md` clearly separates implemented controls, partial behavior, scoped CI evidence, and unverified guarantees. If any requested statement cannot be supported, say so plainly rather than infer behavior.

## Phase Log

| Step                                                    | Status   | Outcome                                                                                                                                                                                                                                                                          |
| ------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Re-read current SECURITY.md and phase/release evidence  | Complete | Conflicting claims and evidence sources identified.                                                                                                                                                                                                                              |
| Record this plan before editing SECURITY.md             | Complete | This file; indexed in `notes/MANIFEST.md`.                                                                                                                                                                                                                                       |
| Reconcile SECURITY.md within the single-file Scope Lock | Complete | Removed unsupported guarantees; retained only source- and release-evidence-backed controls, partial behavior, and exclusions. Clarified that proxy GeoIP locale/timezone behavior requires available GeoIP data.                                                                 |
| Validate claims, formatting, and single-target scope    | Complete | Source anchors and Core evidence checked; both unique relative evidence links resolve; CRLF-aware `git diff --check` passes. The only product/reference file in this Scope Lock is `docs/SECURITY.md`; no source, tests, workflows, API, UI, release, or frozen roadmap changed. |

**Outcome:** COMPLETE. This was a documentation-only amendment to PR-02. No source or runtime implementation is part of this phase. External proxy, DNS/WebRTC, arbitrary-host, and complete fingerprint-parity claims remain unverified.
