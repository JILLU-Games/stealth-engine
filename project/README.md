# project/

**Purpose:** Permanent, git-committed development and planning record for the stealth_engine project.

## What lives here

Every feature, module, component, and subsystem gets its own markdown file here. Documentation covers:

- Feature purpose and design rationale
- Current implementation status
- File/module location in the codebase
- Known limitations and open tasks
- Change history per feature

## When to update

**Every code change — no exceptions.** Whenever any file in `stealth_engine/` is created, modified, or deleted, the corresponding `project/` markdown must be updated in the same commit.

## Structure

```
project/
├── README.md           ← this file
├── MANIFEST.md         ← index of all project docs
├── features/           ← one .md per A–Z feature
└── modules/            ← one .md per stealth_engine module
```

## Rules (from AGENTS.md)

1. Update `project/` in the **same commit** as any code change.
2. No feature or module is "done" without current documentation here.
3. Agents must never skip this folder after a code change.
4. All information must be factual and current — no stale entries.
