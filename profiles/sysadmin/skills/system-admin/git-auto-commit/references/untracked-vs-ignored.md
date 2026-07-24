# .gitignore: Tracked vs Ignored Files

## The Core Distinction

`.gitignore` only affects **untracked** files. Once a file is committed, git
continues to track it regardless of `.gitignore` entries. This is a common
trap when adding new ignore rules for files that were previously in the repo.

## Fixing Previously-Tracked Files

If you add a `.gitignore` rule but files matching that pattern still show up
in `git status`, they are already tracked. Remove them:

```bash
git rm -f --cached <path>
git commit -m "Remove <file> from tracking (already covered by .gitignore)"
```

The `-f` flag is needed when the working copy differs from staging or HEAD.
`--cached` ensures only git tracking is removed, not the file itself on disk.

## Verifying Ignore Rules Work

To confirm a `.gitignore` rule catches files before committing:

```bash
# 1. Create test files matching the pattern
touch .npm_lock_hash_test
touch gateway.heartbeat

# 2. Run git add .
git add .

# 3. Check what got staged
git diff --cached --name-only
```

If your test files do NOT appear in the output, the rule works. If they do,
the rule is wrong or missing.

## Common Trap Patterns

- **Wildcard `.lock` + `.npm_lock_hash_abc123`**: Both `*.lock` and `.npm_lock*`
  cover this file. Prefer the more specific pattern for clarity.
- **`.heartbeat` files**: `*.heartbeat` catches all heartbeat files at any depth.
  But if one was previously committed, it needs `git rm --cached` too.