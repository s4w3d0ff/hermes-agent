---
name: git-auto-commit
description: >
  Automated recurring git commits via system crontab. Installs a bash script
  that git-add, commit, tag, and push to origin/master on a fixed schedule.
category: system-admin
tags: [git, crontab, automation, backup, system-cron]
---

## Trigger Conditions

Use when:
- User wants daily (or recurring) auto-commit of a directory into a git repo
- No LLM logic needed — pure script that stages, commits, tags, pushes
- Remote repo is already configured; .gitignore is already correct

## Procedure

### 1. Create the Script

Write a bash script using `skill_manage(action='write_file')` under the skill's `scripts/` directory. See `scripts/git-auto-commit.sh` for the canonical template.

### 2. Install as System Crontab

Do NOT use Hermes cron — this is a system crontab (`crontab -l`). Write the entry to a temp file and install via `crontab <file>`. Avoid chaining commands (user deny rules block `&&`, `;`, `||`). Use `workdir=` instead of `cd &&` for git commands.

### 3. Verify Execution

Run the script manually once to confirm it works end-to-end before relying on cron. **Don't undo and re-run** — the first run's output is sufficient verification evidence.

## Push Strategy

- **Force-push with `--force-with-lease`** overwrites remote. Never pull from remote in the cron script.
- `--force-with-lease` is safer than bare `--force`: it only overwrites if the remote hasn't been modified by someone else since your last fetch. If that condition fails, the push aborts rather than silently destroying remote commits.

## Pitfalls

- **Crontab step values**: `*/24` is rejected by cron (max step value is 23). Use `0 0 * * *` for daily at midnight. For "every N hours" where N <= 23, use `0 */N * * *`. Anything > 23 needs full cron syntax like `0 9 * * *`. See `references/crontab-quirks.md`.
- **Tag duplicates**: `git tag` without `-f` fails on existing tags. With `set -e`, this aborts the entire script. Always use `git tag -f "$DATE_TAG"`.
- **Verification sufficiency**: The first successful run's output IS sufficient evidence. Do not undo, reset, and re-run — that creates divergent local history and is wasted work.
- **One command at a time**: No chaining (`&&`, `;`, `||`). Terminal tool may block chained commands via user-defined deny rules (e.g., `git restore *`, `git checkout -- *`, `git reset --hard *`). Use `workdir=` instead of `cd &&`.

## Session-Specific References

See `references/crontab-quirks.md` for crontab step value limits and syntax quirks.