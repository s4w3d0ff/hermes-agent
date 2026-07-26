#!/usr/bin/env bash
# Auto-commit and push ~/.hermes to origin/master with date-based tag
# Fixed: uses Python fnmatch to cross-reference tracked files vs .gitignore rules

set -euo pipefail

HERMES_DIR="$HOME/.hermes"
DATE_TAG="$(date +%Y-%m-%d)"
LOG_FILE="$HERMES_DIR/scripts/git-auto-commit.log"

export HERMES_DIR LOG_FILE
cd "$HERMES_DIR" || exit 1

# Use Python to find tracked files that match .gitignore patterns
# and untrack them via git rm --cached
python3 << 'PYTHON_EOF'
import fnmatch
import os
import subprocess
import sys

def parse_gitignore(path):
    """Parse .gitignore rules into a list of (pattern, negated, directory_only) tuples."""
    rules = []
    with open(path, "r") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            negated = False
            if line.startswith("!"):
                negated = True
                line = line[1:]
            directory_only = line.endswith("/")
            if directory_only:
                line = line.rstrip("/")
            rules.append((line, negated, directory_only))
    return rules

def should_ignore(filepath, rules):
    """Check if a filepath should be ignored by .gitignore rules."""
    matched_negation = False
    for pattern, negated, directory_only in rules:
        # Leading slash means anchor at root
        anchored = pattern.startswith("/")
        if anchored:
            pattern = pattern[1:]
        
        # For directories, match if filepath starts with the pattern
        if directory_only:
            if anchored:
                matches = fnmatch.fnmatch(filepath, pattern + "/*") or filepath == pattern
            else:
                matches = fnmatch.fnmatch(filepath, pattern + "/*") or \
                          any(fnmatch.fnmatch(part, pattern) for part in filepath.split("/")) or \
                          filepath.startswith(pattern + "/")
        else:
            if anchored:
                matches = fnmatch.fnmatch(filepath, pattern)
            else:
                # Match against basename and full path segments
                basename = filepath.split("/")[-1]
                matches = fnmatch.fnmatch(basename, pattern) or \
                          fnmatch.fnmatch(filepath, pattern) or \
                          any(fnmatch.fnmatch(part, pattern) for part in filepath.split("/"))
        
        if matches:
            if negated:
                matched_negation = True
            else:
                if not matched_negation:
                    return True
                # Negation overrides previous match
                matched_negation = False
    return matched_negation

hermes_dir = os.environ["HERMES_DIR"]
gitignore_path = hermes_dir + "/.gitignore"
rules = parse_gitignore(gitignore_path)

# Get tracked files
tracked = subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n")

to_untrack = []
for f in tracked:
    if should_ignore(f, rules):
        to_untrack.append(f)

print(f"Tracked files matching .gitignore: {len(to_untrack)}")
for f in to_untrack[:30]:
    print(f"  {f}")
if len(to_untrack) > 30:
    print(f"  ... and {len(to_untrack) - 30} more")

# Untrack them
untracked_count = 0
for f in to_untrack:
    result = subprocess.run(["git", "rm", "--cached", f], capture_output=True)
    if result.returncode == 0:
        untracked_count += 1
    else:
        print(f"  FAILED to untrack: {f} ({result.stderr.decode().strip()})")

print(f"Successfully untracked: {untracked_count}")
PYTHON_EOF

# Stage all changes
git add .

# Check if there are any changes to commit
if ! git diff --cached --quiet; then
    # Create commit message with date
    git commit -m "cronjob(remote-backup): $DATE_TAG"

    # Create version tag using the date
    git tag -f "$DATE_TAG"

    # Force-push master and tag to overwrite remote (never pull)
    git push --force origin master && git push --force origin "$DATE_TAG"

    echo "$(date '+%Y-%m-%d %H:%M:%S') COMMITTED, tagged $DATE_TAG, pushed to origin/master" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') NO CHANGES - nothing to commit" >> "$LOG_FILE"
fi
