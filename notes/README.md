# notes/

**Purpose:** Shared development planning, research, work logs, and project-history records. This folder is tracked in git.

## When to use

- Before starting any update, fix, or new feature: write a plan here first.
- During development: keep a running step/phase log of what you did and what happened.
- After finishing: jot down any follow-up items or lessons learned.

## When NOT to use

- Do not store credentials, private personal information, or sensitive production/user data here.
- Keep public-facing guides and API references in `docs/` or the appropriate project documentation.
- Commit relevant notes with the work they document; this folder is not local-only.

## Structure (suggested, not enforced)

```
notes/
├── README.md         ← this file
├── MANIFEST.md       ← index of all note files
└── <date>-<topic>.md ← one file per planning/work session
```

## Rules (from AGENTS.md)

1. Write a plan here **before** every update/change/addition.
2. Keep a phase log **during** every update/fix.
3. Keep secrets and sensitive personal/production data out of notes.
4. Notes are shared repository records; update `MANIFEST.md` when adding one.
