---
name: poolguy-install
description: >-
  Install and troubleshoot the poolguy twitch bot framework. Covers git repo vs pip version differences, import path changes, storage setup, and known API bugs.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [poolguy, twitch-bot, installation, troubleshooting]
---

# poolguy-install

Install poolguy from the git repo (NOT pip). Pip version is stale and broken.

## Pitfall: pip vs git versions differ wildly

pip installs v0.1.8 (broken). git repo has v0.1.9 (working). Always install from git.

```bash
gh repo clone s4w3d0ff/pool-guy poolguy_git -- --depth 1
pip install ./poolguy_git
rm -rf poolguy_git  # temp clone, not part of project
```

## import path changed between versions

v0.1.8 (pip): `from poolguy.storage import loadJSON`
v0.1.9 (git): `from poolguy.core.storage import loadJSON`

grep imports before running code:

```bash
source deez_venv/bin/activate && python3 -c "import poolguy; print('core' in dir(poolguy))"
```

## storage type must be string 'sqlite', not object

cfg.json needs `"storage": "sqlite"` (string). StorageFactory.create_storage('sqlite') returns SQLiteStorage class. v0.1.8 threw NotImplementedError on sqlite, v0.1.9 works.

## API arg changed: paused → hold

TwitchBot.start() takes `hold=True`, NOT `paused=True`. Deprecated arg in v0.1.9. Fix import before running.

```bash
python3 -c "import poolguy; help(poolguy.TwitchBot.start)" 2>&1 | head -5
```

## requirements.txt git URL format

```
poolguy @ git+https://github.com/s4w3d0ff/pool-guy.git
```

Not just `poolguy`. pip will install stale version.

## sensitive keys pattern

keys go in `.env` file at project root (gitignored). scripts source `.env`, never hardcoded keys anywhere. run.sh template uses `$SCRIPT_DIR` for all paths, no hardcoded absolute paths.

## cfg.json stale platform paths

poolguy config (`cfg.json`) may carry stale platform-specific paths from a previous install (e.g. Windows browser exe path: `C:\Program Files\LibreWolf\librewolf.exe`). Remove any `browser` key on Linux. Delete non-applicable config keys before running the bot.