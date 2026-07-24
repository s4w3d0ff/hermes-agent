#!/usr/bin/env bash
# Auto-commit and push ~/.hermes to origin/master with date-based tag
# Installed via system crontab (not Hermes cron)

set -euo pipefail

HERMES_DIR="$HOME/.hermes"
DATE_TAG="$(date +%Y-%m-%d)"
LOG_FILE="$HERMES_DIR/scripts/git-auto-commit.log"

cd "$HERMES_DIR" || exit 1

# Stage all changes (except .gitignore which is already in git)
git add .

# Check if there are any changes to commit
if ! git diff --cached --quiet; then
    # Create commit message with date
    git commit -m "auto-commit: $DATE_TAG"

    # Create version tag using the date
    git tag "$DATE_TAG"

    # Push to master branch and tags
    git push origin master && git push origin "$DATE_TAG"

    echo "$(date '+%Y-%m-%d %H:%M:%S') COMMITTED, tagged $DATE_TAG, pushed to origin/master" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') NO CHANGES — nothing to commit" >> "$LOG_FILE"
fi
