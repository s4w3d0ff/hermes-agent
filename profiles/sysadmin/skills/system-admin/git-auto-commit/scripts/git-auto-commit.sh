#!/usr/bin/env bash
# Auto-commit and push ~/.hermes to origin/master with date-based tag

set -euo pipefail

HERMES_DIR="$HOME/.hermes"
DATE_TAG="$(date +%Y-%m-%d)"
LOG_FILE="$HERMES_DIR/scripts/git-auto-commit.log"

cd "$HERMES_DIR" || exit 1

# Remove any tracked files that now match .gitignore patterns so they won't
# get picked up by `git add .` in future cron runs. This handles the case where
# a new .gitignore rule catches files that were previously committed to the repo.
for f in $(git ls-files); do
    if git check-ignore -q "$f"; then
        git rm --cached "$f" 2>/dev/null || true
    fi
done

# Stage all changes
git add .

# Check if there are any changes to commit
if ! git diff --cached --quiet; then
    # Create commit message with date
    git commit -m "cronjob(remote-backup): $DATE_TAG"

    # Create version tag using the date (force-update handles duplicates)
    git tag -f "$DATE_TAG"

    # Force-push master and tag to overwrite remote (never pull)
    git push --force origin master && git push --force origin "$DATE_TAG"

    echo "$(date '+%Y-%m-%d %H:%M:%S') COMMITTED, tagged $DATE_TAG, pushed to origin/master" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') NO CHANGES — nothing to commit" >> "$LOG_FILE"
fi
