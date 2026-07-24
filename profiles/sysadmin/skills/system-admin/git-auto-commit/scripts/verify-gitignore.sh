#!/usr/bin/env bash
# Verify .gitignore rules catch test files during git add .
set -euo pipefail

HERMES_DIR="/home/s4w3d0ff/.hermes"
cd "$HERMES_DIR" || exit 1

# Test files that should be ignored by current .gitignore
TEST_FILES=(
    ".npm_lock_hash_abc123"
    "gateway.heartbeat"
    "profiles/sysadmin/state/gateway.heartbeat"
    "profiles/shamu/state/gateway.heartbeat"
)

# Create them
for f in "${TEST_FILES[@]}"; do
    touch "$f"
done

# Stage (same as cron does)
git add .

# Check what got staged
staged=$(git diff --cached --name-only 2>/dev/null || true)

echo "=== Files that got staged ==="
echo "$staged"
echo ""

failed=0

for f in "${TEST_FILES[@]}"; do
    if echo "$staged" | grep -qF "$f"; then
        echo "FAIL: $f was staged (should be ignored)"
        failed=$((failed + 1))
    fi
done

if [ $failed -eq 0 ]; then
    echo "PASS: all test files correctly ignored by .gitignore"
fi

# Cleanup
for f in "${TEST_FILES[@]}"; do
    rm -f "$f"
done

exit $failed
