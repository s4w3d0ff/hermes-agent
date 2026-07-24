# Git Hygiene — Magidex Case Study

Session 2026-06-22: `~/.hermes/magidex` repo hygiene audit.

## Problem

.git/ was **432MB**, containing:
- `scripts/default-cards.json` — 522MB (GitHub 100MB limit, rejected on push)
- `card_db.sqlite` — 42MB (in .gitignore but tracked in history)
- `test_cards/` images — ~50MB (in .gitignore but tracked)
- 6 old branches (dev, fix-ocr-accuracy, full-rework, magidex-app, magidex-audit-cleanup, magidex-ocr-improvement)

## Failed Attempts

### 1. git-filter-reboot --invert-paths (alone)
```bash
git filter-reboot --path scripts/default-cards.json --invert-paths --force
```
**Result:** Removed `default-cards.json` but `card_db.sqlite` blob survived (42MB still in pack). `test_cards/` also survived.

**Why:** filter-reboot only removes files from the index. Blobs that existed in old commits before untracking persisted.

### 2. git-filter-branch
```bash
git filter-branch --force --index-filter 'git rm -rf --cached --ignore-unmatch scripts/card_db.sqlite scripts/default-cards.json' --prune-empty -- --all
```
**Result:** Rewrote 124 commits, removed files from index. But `test_cards/` blobs still survived (they were in commits before the untracking commit).

**Why:** filter-branch rewrites the index but leaves blobs in pack objects if they're still referenced by other branches.

### 3. git gc --aggressive
**Result:** Only reduced from 502MB to 432MB. Didn't touch the large blobs because they were still referenced.

## Successful Solution (Step-by-Step)

### Step 1: Purge default-cards.json with filter-reboot
```bash
rm -rf .git/filter-reboot
git filter-reboot --path scripts/default-cards.json --invert-paths --force
```
Removed the 522MB file.

### Step 2: Remove card_db.sqlite from index
```bash
git rm --cached card_db.sqlite
```

### Step 3: Rewrite history with filter-branch to remove blobs
```bash
git filter-branch --force --index-filter \
  'git rm -rf --cached --ignore-unmatch scripts/card_db.sqlite scripts/default-cards.json test_cards/' \
  --prune-empty -- --all
```
Removed card_db.sqlite and test_cards/ from all commits.

### Step 4: Clean refs and gc
```bash
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Step 5: Delete old branches
```bash
git branch -D dev fix-ocr-accuracy full-rework magidex-app magidex-audit-cleanup magidex-ocr-improvement
```
Old branches referenced old blobs, preventing gc from pruning them.

### Step 6: Second pass with filter-reboot to clean up any remaining blobs
```bash
rm -rf .git/filter-reboot
git filter-reboot --path test_cards/ --invert-paths --path scripts/card_db.sqlite --invert-paths --path scripts/default-cards.json --invert-paths --force
```
This cleaned up the final 212 test_cards blobs that survived the filter-branch pass.

### Step 7: Final gc
```bash
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## Final Result

| Before | After | Reduction |
|--------|-------|-----------|
| 533MB .git/ | 49MB .git/ | **91% reduction** |
| 522MB default-cards.json | 0 | Removed |
| 42MB card_db.sqlite | 0 | Removed |
| ~50MB test_cards/ | 0 | Removed |
| 8 branches | 2 branches | Clean |

## Push to GitHub

```bash
# git-filter-reboot removes origin! Re-add:
git remote add origin https://s4w3d0ff@github.com/s4w3d0ff/magidex.git
git config --local credential.helper manager

# Force push (history rewritten):
git push origin full-rewrite --force
git push origin master --force
```

## Key Lessons

1. **git-filter-reboot does NOT remove blobs from old commits** — it only removes files from the index. Blobs persist in pack objects if referenced by other branches.

2. **git-filter-branch rewrites history** but leaves dangling blobs. You MUST run `rm -rf .git/refs/original/ && git reflog expire --expire=now --all && git gc --prune=now --aggressive` after.

3. **Old branches prevent gc pruning** — delete them before gc.

4. **Two-pass approach works**: filter-reboot for index changes + filter-branch for full history rewrite + filter-reboot again to clean any remaining blobs.

5. **git-filter-reboot removes origin** — always re-add it before pushing.

6. **Windows push 401 issues**: use `credential.helper manager` and include username in remote URL: `https://USERNAME@github.com/OWNER/REPO.git`.
