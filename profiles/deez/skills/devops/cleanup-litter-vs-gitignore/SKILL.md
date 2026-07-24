---
name: cleanup-litter-vs-gitignore
description: >-
  Distinguish repo litter from legitimate exclusions. Delete trash, gitignore real files only.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Cleanup, GitIgnore, RepoHygiene]
---

# Cleanup Litter vs GitIgnore

When cleaning a repo, separate two categories of files/dirs: litter and legitimate exclusions. Never put litter in `.gitignore`. Delete it. Only gitignore real artifacts that the project needs on disk but shouldn't commit.

## When to Use

- User says "clean up", "remove trash", "audit repo", or "check git status"
- You discover unexpected files/dirs in a project tree
- `.gitignore` needs updating during cleanup
- Bot/runtime creates cache dirs that confuse git tracking

## Prerequisites

No external tools needed. Use `terminal` to list files, `search_files` to scan trees.

## How to Run

1. List repo contents with `terminal`.
2. Categorize each item into litter or legitimate exclusion.
3. Delete litter immediately.
4. Add only legitimate exclusions to `.gitignore`.

## Quick Reference

| Category | Action | Examples |
|---|---|---|
| Litter | Delete permanently | temp git clones, wrong install dirs, orphan folders, dead cache files |
| Legitimate Exclusion | Gitignore | sensitive env files, runtime db cache, build artifacts, .env, *.db |

## Procedure

1. `terminal` run `find . -type f -o -type d | sort` to list all non-.git files.
2. For each item, ask: "does this serve the project?"
   - No → litter → `rm -rf <path>` or `rm <file>` immediately.
   - Yes → legitimate → add to `.gitignore` if it shouldn't commit.
3. Verify with `git status`. Only source files + needed runtime cache should remain untracked/modified.
4. Commit only intentional changes (code fixes, .gitignore updates for real exclusions).

## Pitfalls

- **Never gitignore litter.** Trash belongs nowhere. Deleting it is the correct action. Adding it to gitignore means you're trying to keep it — which is wrong if it serves no purpose.
- **Runtime cache ≠ litter.** Files that bots/apps recreate naturally (eventsub caches, db tables) are legitimate. They stay on disk, get gitignored if sensitive.
- **Temp install clones = litter.** `poolguy_git/`, cloned repos used only for pip install → delete immediately after installing into venv.
- **Don't guess purpose.** If you created a file/dir yourself and can't trace its caller in the codebase, it's probably litter. Delete it.
- **SQLite tables > json dirs.** Old poolguy versions wrote tokens/alerts as json files in `db/tokens/` dirs. New version uses SQLiteStorage (tables inside db/twitch.db). Empty leftover dirs are litter from old install → delete.

## Verification

```bash
cd <repo> && git status
```

Should show only source code files, legitimate runtime cache (gitignored), and intentional changes. No temp clones, no orphan dirs, no dead json file folders. Clean tree = correct state.