# Crontab Quirks

## Step Value Limit

Cron rejects step values > 23 in the `*/N` syntax.

```
0 */24 * * *   → rejected: "Step size 24 higher than possible maximum of 23"
```

Workarounds:

| Desired frequency | Crontab entry |
|-------------------|---------------|
| Daily midnight    | `0 0 * * *`   |
| Every N hours (N ≤ 23) | `0 */N * * *` |
| Every N hours (N > 23) | Use full syntax: `0 9 * * *` for daily at 9am, etc. |

For exact intervals like every 48 hours, use cron's repeat count or two entries offset by the interval.

## Installation Pattern

Never chain `crontab -l` with a new entry using `&&`/`;`. User deny rules block these operators.

Correct approach:
1. Write the full crontab content to a temp file
2. Install via `crontab <tempfile>`

If there are existing entries, manually copy them from `crontab -l` into the temp file before appending new ones.

## --force-with-lease vs --force

`git push --force-with-lease origin master` only overwrites if the remote branch has not been updated since your last fetch (via ref specification). If someone else pushed in between, it aborts with an error instead of silently destroying their work. This is preferred over bare `--force` for safety.