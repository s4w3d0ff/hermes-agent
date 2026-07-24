# Deezbot Dependency Notes

## poolguy — Git Repo Required, pip is Stale
- pip package (v0.1.8) lacks SQLiteStorage support and `core` subpackage
- git repo (`github.com/s4w3d0ff/pool-guy`) v0.1.9 has both
- requirements.txt must use: `poolguy @ git+https://github.com/s4w3d0ff/pool-guy.git`
- import path in deezbot: `from poolguy.core.storage import loadJSON` (v0.1.8 was `poolguy.storage`)

## spaCy CLI Needs click
- `python -m spacy download en_core_web_sm` requires `click` module
- click is not listed in spacy's direct dependencies for the CLI subcommand
- add `click` to requirements.txt before running model downloads

## twitch.db and my_run.sh Sensitive Files
- `.gitignore` covers: `*.db`, `my_run*` (prefix glob)
- API keys must come from env vars, never hardcoded in scripts or committed files