# GitHub Noreply Email Format

GitHub's noreply email format is `ID+username@users.noreply.github.com`, where:
- **ID** = numeric user ID from the GitHub API
- **username** = login handle

NOT `username@users.noreply.github.com` (missing the ID prefix).

## How to derive it

```bash
# Get numeric ID
gh api user --jq '.id'        # e.g. 6069664

# Get login
gh api user --jq '.login'     # e.g. s4w3d0ff

# Combine: ID+username@users.noreply.github.com
# Result: 6069664+s4w3d0ff@users.noreply.github.com
```

## Why this matters

Git commits need to match the GitHub account for attribution. Using just
`username@users.noreply.github.com` will NOT link commits back to your
GitHub profile, GitHub requires the `ID+` prefix to recognize the noreply
address as belonging to that account.

## Reference

This format is documented in GitHub's help center under "Keeping your email
addresses private". The numeric ID + username concatenation is the only valid
noreply pattern GitHub recognizes for commit attribution.