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

Do NOT use Hermes cron — this is a system crontab (`crontab -l`). Write the entry to a temp file and install via `crontab <file>`. **Never chain commands** (`&&`, `||`, `;`) — user deny rules block these. Use `workdir=` instead of `cd &&` for git commands. Run each command as a separate terminal call.

### 3. Verify Execution

Run the script manually once to confirm it works end-to-end before relying on cron. **Don't undo and re-run** — the first run's output is sufficient verification evidence.

## Push Strategy

- **Force-push with `--force-with-lease`** overwrites remote. Never pull from remote in the cron script.
- `--force-with-lease` is safer than bare `--force`: it only overwrites if the remote hasn't been modified by someone else since your last fetch. If that condition fails, the push aborts rather than silently destroying remote commits.

## Pitfalls

- **Tracked files that should be ignored**: `.gitignore` does NOT affect files already committed to the repo. The cron script must proactively handle this: before `git add .`, iterate `git ls-files`, check each against `git check-ignore -q`, and run `git rm --cached` on any match. This prevents previously tracked files from being silently re-committed when a new `.gitignore` rule catches them. See `scripts/git-auto-commit.sh` for the canonical template with this logic.
- **Crontab step values**: `*/24` is rejected by cron (max step value is 23). Use `0 0 * * *` for daily at midnight. For "every N hours" where N <= 23, use `0 */N * * *`. Anything > 23 needs full cron syntax like `0 9 * * *`. See `references/crontab-quirks.md`.
- **Tag duplicates**: `git tag` without `-f` fails on existing tags. With `set -e`, this aborts the entire script. Always use `git tag -f "$DATE_TAG"`.\n- **Never commit test artifacts into the target repo**. Verification scripts that create dummy files (e.g., `touch SOUL.md`, `touch .npm_lock_hash_test`) must NEVER be committed or pushed to the remote. If you need to test, run ad-hoc outside of any commit — clean up afterward without committing the test debris.\n- **`git reset --hard` is dangerous for cron cleanup**. It discards all staged changes including legitimate ones. Use `git rm --cached` for individual files instead. The cron script must never reset the entire index before staging.\n- **One command at a time**: No chaining (`&&`, `;`, `||`). User deny rules block these in terminal. Execute single commands sequentially. Use `workdir=` instead of `cd &&`.

## Session-Specific References

See `references/crontab-quirks.md` for crontab step value limits and syntax quirks.
See `references/test-artifacts-never-commit.md` for the rule that test dummy files must never be committed to the target repo.
See `references/untracked-vs-ignored.md` for the tracked-vs-ignored distinction and how to untrack files that were previously committed.
Use `scripts/verify-gitignore.sh` to validate ignore rules by creating test files and running `git add .`.