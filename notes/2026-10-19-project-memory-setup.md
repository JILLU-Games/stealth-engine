# Project memory setup

Date: 2026-10-19

## Plan

- Inspect package metadata, source modules, project guidance, and existing docs.
- Add root `MEMORY.md` with verified architecture, dependencies, implemented behavior, and conventions.
- Add `.github/copilot-instructions.md` with scoped workflow rules and the required real-time memory update rule.
- Verify the files exist and their instructions/content are consistent with the inspected source.

## Phase log

- Inspection: Read the project agent rules, package metadata, README, architecture reference, package modules, and test placeholder.
- Finding: The package has no database; `tests/test_placeholder.py` has no implemented tests. The A-Z README is a feature specification, so memory will separate shipped code behavior from documented goals.
- Finding: `BrowserRuntime` is the package root and has no `.git` directory in this environment.
- Implementation: Added root `MEMORY.md` and `.github/copilot-instructions.md` with the requested project analysis and exact critical memory rule.
- Verification: Read both files back and confirmed the critical rule is present verbatim; editor diagnostics report no errors. No runtime tests apply to these documentation-only changes.
