# Test Artifacts — Never Commit to Target Repo

## Problem

Verification scripts that create dummy files for testing `.gitignore` rules (e.g., `touch SOUL.md`, `touch .npm_lock_hash_test`) can accidentally get committed into the target repo if the verification flow is wrapped in a commit/push cycle.

## Session Example

During verification of the cron script fix, a test script created `SOUL.md`, committed it to verify the `.gitignore` sweep logic, then pushed those commits to the user's remote repo — adding unwanted test debris into history (commits `5f00131`, `71c8362`, `00eaceb`).

## Correct Approach

- Create test files for verification → run `git add .` → check `git status --short`
- If patterns work correctly: remove test files, do NOT commit anything related to the test
- If patterns don't work: fix `.gitignore`, then run a fresh cycle (rm --cached + git add .) without committing test artifacts
- Never wrap verification dummy file creation in `git commit -m`

## Verification Pattern (Safe)

```bash
# Create test file
touch .npm_lock_hash_test

# Run staging only — no commit
git add .

# Check result
git status --short | grep .npm_lock_hash_test
# If empty: pattern works, clean up and stop
rm .npm_lock_hash_test
# No git commit needed for the test itself

# If staged (pattern doesn't work): fix gitignore, then run the proper cycle
```

The only commits should be real changes to `.gitignore`, tracked file removals (`git rm --cached`), or legitimate content updates. Test artifacts belong nowhere in repo history.
