# Notes Tracking Policy Update

## Plan

- Change `AGENTS.md`, `.github/copilot-instructions.md`, `MEMORY.md`, and `notes/README.md` so they treat `notes/` as repository-tracked and shareable.
- Keep `notes/` planning, work logs, and project records; do not describe them as local-only or forbid committing them.
- Confirm the existing `.gitignore` has no `notes/` exclusion, verify the policy edits, stage the notes directory with the policy files, then commit and push to `origin/main` as requested.
- Expected outcome: project instructions agree that notes are tracked; the policy update and notes are pushed.

## Phase Log

- 2026-11-26: Confirmed `main` is clean and aligned with `origin/main`; 99 files under `notes/` are already tracked, and `.gitignore` contains no notes exclusion.
- 2026-11-26: Updated the repository rules and project memory to define notes as tracked/shared, and updated this folder's README. Confirmed no `notes/` ignore rule exists; `git -c core.whitespace=cr-at-eol diff --check` passed.
- Outcome: policy/documentation updates are complete and registered here; the requested commit and push will carry this note with the other tracked notes.
