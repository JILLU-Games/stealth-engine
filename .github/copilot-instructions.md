# Copilot Instructions

These repository-specific instructions supplement `AGENTS.md`, `AI_INSTRUCTIONS.md`, and `MEMORY.md`. When instructions differ, follow the more specific repository rules and the user's latest request.

## Project Workflow

- At the start of work, read `MEMORY.md`, `AGENTS.md`, and the relevant portions of `AI_INSTRUCTIONS.md`; check `notes/` for an existing plan.
- Inspect only the files needed to establish the behavior and make the smallest correct change. Preserve the existing Python architecture and public API.
- Before each change, record its plan in `notes/`; maintain a phase log and update the notes manifest when adding a note. `notes/` is tracked and shared, so include relevant notes in commits.
- When package code changes, update the corresponding `project/` documentation in the same unit of work. Update `docs/` when engine behavior or its reference documentation changes, as required by `AGENTS.md`.
- Use focused verification, report any unavailable or failing checks accurately, and do not fix unrelated issues.
- Keep `MEMORY.md` factual. Distinguish implemented behavior from roadmap/specification, and revise stale details rather than accumulating conflicting notes.

## Critical Memory Rule

> CRITICAL RULE: Whenever a change, update, bug fix, or new feature is implemented in this project during our conversation, you (the AI) must automatically prompt me to update the `MEMORY.md` file, or directly write/suggest the exact markdown updates needed to keep the project memory 100% up-to-date in real-time.

Operationally, when a task changes a project fact captured in `MEMORY.md`, update that file in the same task and summarize the exact memory change. If the project memory does not need a content change, still explicitly prompt the user about keeping `MEMORY.md` current rather than silently skipping the rule.
