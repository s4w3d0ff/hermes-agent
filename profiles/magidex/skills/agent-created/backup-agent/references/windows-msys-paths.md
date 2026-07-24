# Windows + MSYS Path Resolution Guide

On Windows hosts running Hermes via git-bash/MSYS, path handling is a common source of bugs.

## The Mapping

| Shell Notation | MSYS Path | Windows Filesystem Path |
|---|---|---|
| `~` or `$HOME` | `/c/Users/<user>/` | `C:\Users\<user>\` |
| `~/.hermes` | `/c/Users/<user>/.hermes` | `C:\Users\<user>\.hermes` |
| `~/AppData` | `/c/Users/<user>/AppData` | `C:\Users\<user>\AppData` |

## Common Mistake

```
~/.hermes/agent-backup    ← CORRECT backup location
  → C:\Users\<user>\.hermes\agent-backup

AppData/Local/hermes/agent-backup  ← WRONG — different directory entirely
  → C:\Users\<user>\AppData\Local\hermes\agent-backup
```

The `~/.hermes` directory is a dotfile-style config home. The `AppData/Local/hermes` directory
is the Hermes application data store. They are **not** the same.

## Python Subprocess Gotchas

### 1. Backslash escaping
Windows paths contain backslashes (`C:\Users\...`). When passed to `bash -c` or
`subprocess.run(shell=True)`, backslashes are interpreted as escape sequences.

**Fix:** Convert to forward slashes before shell execution:
```python
posix_path = str(path).replace('\\', '/')
```

### 2. `cwd=` parameter fails on Windows
`subprocess.run(..., cwd=r"C:\path\with spaces\dir")` often silently fails on Windows+MSYS.

**Fix:** Use `git -C <path>` with the `cwd=None` default instead.

### 3. Multiline commit messages
`git commit -m "line1\nline2"` fails because bash splits on newlines.

**Fix:** Write to a temp file and use `git commit -F <file>`.

### 4. Glob patterns in f-strings
`run(f"git tag -l 'v0.1.*'")` — bash strips the single quotes from the f-string.

**Fix:** Use double quotes: `run(f"git tag -l \"v0.1.*\"")`.

## Detection Patterns

When you need to find paths dynamically:

```python
from pathlib import Path
import os

# Detect home directory
home = os.environ.get("HOME") or str(Path.home())

# Try candidate locations in priority order
candidates = [
    Path(home) / ".hermes",
    Path.home() / "AppData" / "Local" / "hermes",
]

for c in candidates:
    if c.exists():
        return c
```
