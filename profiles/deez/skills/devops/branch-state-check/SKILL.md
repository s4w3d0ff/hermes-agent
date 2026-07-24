---
name: branch-state-check
description: Verify local branch and remote state before any git work.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Git, Workflow, Safety]
---

# Branch State Check

Always verify current branch status and remote PR state before committing or pushing. Prevents orphaned changes, duplicate PRs, and accidental pushes to stale branches. Git operations without this check are a failure pattern.

## When to Use

- Before any `git commit`, `git push`, or `gh pr create`
- After switching branches or pulling from origin
- When creating a new feature branch for work
- Any time before touching git state in the project repo

## Prerequisites

- Project repo cloned locally with correct remote configured
- `gh` CLI installed and authenticated
- Working directory set to the project root

## How to Run

Invoke through the `terminal` tool. Check status, verify branch name, compare against origin before proceeding.

## Quick Reference

```bash
git status          # uncommitted changes
git log --oneline -5  # recent commits on current branch
git branch -vv      # local branches with remote tracking info
gh pr list --state open   # active PRs targeting dev
```

## Procedure

ALWAYS follow this exact order for any git work:

1. Switch to dev: `git checkout dev`
2. Pull latest: `git pull origin dev` — never skip this. Dev may have moved past your last local branch.
3. Create new feature branch: `git checkout -b feature/<name>` — from the freshly pulled dev.
4. Verify state: run Quick Reference checks before committing.
5. Work and commit on the feature branch only.

If you skip step 2, your work will be orphaned when origin/dev fast-forwards ahead of you. This is the root cause of the previous failure pattern.

## Pitfalls

- Pulling from origin can fast-forward dev past your local commits. Your work becomes orphaned on an old branch. Always pull before branching.
- A merged PR does not mean the commits are in origin/dev — verify with `git log origin/dev..HEAD` after merging.
- Never assume `git checkout <branch>` lands you where you expect. Always run `git branch --show-current` after switching.
- Pushing to an existing branch updates that PR automatically. If you want a separate PR, create a new branch first.
- The previous session may have left dirty state or stale branches. Verify every time.

## Verification

```bash
git status && git branch --show-current && git log origin/dev..HEAD --oneline
```

All three lines must match the expected state before proceeding with commits or pushes.