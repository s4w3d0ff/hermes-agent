---
name: git-github-config
description: >
  Configure git to match a GitHub account via `gh`. Sets user.name,
  user.email, and credential helper. Always queries the GitHub API for
  authoritative values - never assumes from system username or gh login.
argument-hint: ""
license: MIT
related_skills: []
---

# Git GitHub Config

Configure git to match a GitHub account via `gh`.

## Trigger

User asks to configure git, set up git credentials, or make git auth work with GitHub.

## Steps

1. **Inspect current state** - run both:
   ```
   git config --list --show-origin
   gh auth status
   ```
2. **Get the real GitHub account info** - DO NOT assume values. Query GitHub directly:
   ```
   gh api user --jq '.name + "\n" + .email'
   ```
3. **Set name and email** to match what `gh api` returns.
4. **If the account has no public email**, get the numeric ID and use noreply format (see reference):
   ```
   gh api user --jq '.id'
   ```
5. **Verify credential helper** is pointing to `gh auth git-credential`:
   ```
   git config --global credential.https://github.com.helper '!/usr/bin/gh auth git-credential'
   ```
6. **Confirm** with `git config --list --show-origin`.

## Pitfalls

- **GitHub noreply email is NOT `username@users.noreply.github.com`**. Correct format: `ID+username@users.noreply.github.com`. Always fetch the numeric ID via `gh api user --jq '.id'`. See `references/github-noreply-format.md`.
- **Never assume** GitHub name or email from system username or gh login. Query the API - profile fields can differ from the login handle.
- **GitHub may have no email on file**. Check `gh api user --jq '.email'` - if null/empty, fall back to noreply format with ID prefix.

## Support files

- `references/github-noreply-format.md` - authoritative details on GitHub noreply email format and how to derive it.