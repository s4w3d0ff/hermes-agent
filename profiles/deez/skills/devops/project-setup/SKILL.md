---
name: project-setup
description: >-
  Troubleshooting and verification for project setup, dependency installation,
  environment configuration, and cross-platform compatibility. Covers common
  pitfalls when running Windows-originated projects on Linux or vice versa.
  Includes systemd service creation for headless bot apps.
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [setup, install, dependencies, cross-platform, troubleshooting, systemd]
    related_skills: []
---

# Project Setup

Install deps, verify environment, fix cross-platform issues.

## When to Use

- User asks to run/install/setup a project for the first time
- Install script fails on new machine or fresh clone
- Dependencies not loading, import errors on startup
- Cross-platform compatibility issues (Windows repo on Linux)
- Verify a codebase works before committing changes
- systemd service creation for headless boot-start bots/apps

## Steps

1. **Read install script.** Check what it does: venv creation, pip install, model downloads, service setup.
2. **Check line endings.** Windows-originated files have `\\r\\n` — breaks pip parsing and bash scripts on Linux. Fix with `sed 's/\\r$//' file` or python rewrite.
3. **Run install script.** Watch for failures. Don't trust success output blindly — verify imports after.
4. **Verify each dependency.** `python3 -c "import <dep>; print('ok')"`. Check models loaded (spacy, nltk, etc).
5. **Check missing deps.** CLI tools that run via `python -m` need their own deps (spaCy CLI needs click, not always in requirements.txt). Add to requirements.txt if missing.

## Pitfalls

- **CRLF line endings:** Windows files break Linux pip/bash. Always check with `file requirements.txt` or `head -1 install.sh | cat -A`. Fix before running.
- **SPAcy CLI needs click:** `python -m spacy download` requires click module. Not always listed in requirements.txt even though spacy is. Add click if missing.
- **pip=missing on system:** Use `python3 -m pip` not `pip`. PEP 668 blocks system pip — use venv or `--break-system-packages`.
- **Model downloads separate from package install:** spaCy, nltk models are separate steps after package install. Don't assume they ship with the package.
- **Install script uses `python` not `python3`:** Linux systems often have only python3. Fix in script or ensure alias exists.

## systemd Service Pitfalls

When creating systemd units for python bots/apps:

- **WorkingDirectory is mandatory.** systemd runs with no cwd set (default `/`). All relative file paths in your app (cfg.json, .env, db files) fail. Add `WorkingDirectory=/home/s4w3d0ff/Projects/deezbot` to the unit file or every relative path breaks at startup.
- **venv activation doesn't work via exec.** `source venv/bin/activate` then `exec python ...` loses all env vars because exec replaces the shell image. Use `export PYTHONPATH="$SCRIPT_DIR/venv/lib/python3.X/site-packages:$PYTHONPATH"` instead — sets module search path before exec, survives into the replaced process.
- **exec -a for process naming.** use `exec -a deezbot python script.py` to rename the process in the ps tree from `python3` to `deezbot`. The shell wrapper stays as `bash`, the actual python process shows as the custom name. easy to identify in process tree or logs.
- **PYTHONUNBUFFERED=1.** set this env var in the systemd unit so logs appear immediately in journalctl instead of buffered and delayed. critical for debugging service crashes.

## Templates

Copy from templates/ directory:

- `templates/systemd-wrapper.sh` — wrapper script with exec -a, PYTHONPATH, .env sourcing
- `templates/systemd-unit.service` — systemd unit file template

## Verification Checklist

After install:
- [ ] All requirements.txt deps importable
- [ ] CLI tools runnable (spacy download, etc)
- [ ] Models/weights loaded if needed
- [ ] No import errors on `python3 -c "import main_module"`
- [ ] systemd unit tests via `sudo systemctl start` then `journalctl -u <service> --no-pager -n 20`