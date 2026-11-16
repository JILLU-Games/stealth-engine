# AGENTS.md — Developer & AI Agent Rules

This file defines the mandatory rules for all contributors and AI agents working on the **stealth_engine** project.

---

## 1. `notes/` Folder Rules

- `notes/` is **git-ignored** and exists on local machines only. It is never committed or shared.
- `notes/` contains **personal developer notes** during development time only.
  - Planning, scratch thoughts, draft ideas, and work-in-progress notes go here.
  - **No public information, no public-facing documents, no end-user content, no production data.**
- **Before every update/change/addition begins**, a plan/report must be written in `notes/` covering:
  - What is being changed and why
  - Which files/modules will be affected
  - Expected outcome
- **During every update/fix**, a phase/step log must be maintained in `notes/` recording:
  - Each step taken
  - Any issues encountered
  - Final outcome of each phase
- Notes are informal and may use any format; they do not need to be production-quality prose.

---

## 2. `project/` Folder Rules

- `project/` **is committed to git** and stays in the repository permanently.
- `project/` is the single source of truth for all development and planning activity on this project.
- It must contain **detailed markdown documentation** for every feature, page, module, and component.
- **Every time any code is changed, added, fixed, or updated**, the corresponding markdown file(s) in `project/` must be updated in the **same commit** to reflect:
  - What changed and why
  - Current status of the feature/module
  - Any known limitations or follow-up tasks
- No feature or module may be considered "done" without its `project/` documentation being current.
- Agents must never skip updating `project/` after a code change.

---

## 3. `docs/` Folder Rules

- `docs/` **is committed to git** and stays in the repository permanently.
- `docs/` contains **engine-level usage guidelines and reference documentation** for stealth_engine.
- All A–Z features must be documented here with:
  - What the feature does
  - Why it exists
  - How it works internally
  - Where in the codebase it lives
  - When it activates / is called
  - How to use it correctly
- **No detail may be omitted.**
- **All information must be real and exact** — no guesses, no approximations, no placeholder text.
- `docs/` is updated whenever engine behaviour changes.

---

## 4. General Agent Behaviour

- Read `AGENTS.md` at the start of every session before making any changes.
- Always check `notes/` for a pre-existing plan before starting work.
- Always update `project/` and `docs/` as part of the same unit of work as code changes.
- Never commit the `notes/` folder.
- Never leave `project/` or `docs/` stale after a code change.
