#!/usr/bin/env python3
"""
backup-agent-run.py — Portable automated backup of Hermes environment to GitHub.
Cleans, copies, updates README, commits with v0.1.x tag, and pushes.

This script is system-portable: it detects paths dynamically rather than using
hardcoded values.
"""

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def detect_hermes_home():
    """Detect the Hermes home directory across platforms.

    Windows: C:\\Users\\<user>\\AppData\\Local\\hermes
    POSIX:   $HOME/.hermes
    """
    candidates = []

    # Windows pattern
    if os.name == "nt" or sys.platform == "win32":
        user_home = Path.home()
        candidates.append(user_home / "AppData" / "Local" / "hermes")

    # POSIX pattern (also works on Windows via git-bash/MSYS)
    home = os.environ.get("HOME") or str(Path.home())
    candidates.append(Path(home) / ".hermes")

    # Try each candidate; return the first that exists
    for c in candidates:
        if c.exists():
            return c

    # Fallback: try to find any directory named 'hermes' under common locations
    for base in [Path.home() / "AppData" / "Local", Path(home)]:
        if base.exists():
            for d in base.iterdir():
                if d.name == "hermes" and d.is_dir():
                    return d

    raise RuntimeError(
        "Cannot find Hermes home directory. "
        "Set HERMES_HOME env var or place script in the correct environment."
    )


def detect_backup_dir(hermes_home):
    """Detect or derive the backup directory.

    On most systems, ~/.hermes/agent-backup is the correct location.
    Falls back to <hermes_home>/agent-backup.
    """
    home = os.environ.get("HOME") or str(Path.home())
    candidates = [
        Path(home) / ".hermes" / "agent-backup",
        hermes_home.parent / ".hermes" / "agent-backup",
        hermes_home / "agent-backup",
    ]

    for c in candidates:
        if c.exists():
            return c

    # Default: next to the .hermes directory
    return Path(home) / ".hermes" / "agent-backup"


def detect_github_user():
    """Detect the authenticated GitHub username."""
    # Try gh CLI first
    try:
        r = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: .git-credentials file
    home = os.environ.get("HOME") or str(Path.home())
    creds_path = Path(home) / ".git-credentials"
    if creds_path.exists():
        content = creds_path.read_text()
        for line in content.splitlines():
            if "github.com" in line:
                # Extract token from https://token@github.com/...
                parts = line.split("@")
                if len(parts) >= 2:
                    return parts[1].split("/")[0]

    # Fallback: detect from existing git remote
    try:
        r = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=10,
            cwd=Path(os.environ.get("HOME", str(Path.home()))) / ".hermes" / "agent-backup"
        )
        if r.returncode == 0:
            url = r.stdout.strip()
            # Parse https://github.com/username/repo.git
            import re
            m = re.search(r"github\.com[/:]([^/]+)/agent-backup", url)
            if m:
                return m.group(1)
    except Exception:
        pass

    return None


def run(cmd, cwd=None, check=True):
    """Run a shell command and return stdout.

    On Windows, the terminal runs through bash (git-bash / MSYS), so we need
    to convert Windows-style paths (backslashes) to POSIX-style (forward slashes)
    for reliable shell execution.
    """
    # Convert Windows paths to POSIX for the shell
    if cwd is not None:
        cwd = str(cwd).replace("\\", "/")
    # Normalize the command string for MSYS bash
    cmd = cmd.replace("\\", "/")

    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    if check and result.returncode != 0:
        print(f"ERROR running: {cmd}")
        print(f"  stdout: {result.stdout}")
        print(f"  stderr: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def get_next_version():
    """Determine the next v0.1.x version number from existing git tags."""
    # Use git -C to specify repo directory; double-quoted glob to avoid
    # bash stripping single quotes from the f-string
    posix_path = str(BACKUP_DIR).replace("\\", "/")
    existing_tags = run(f'git -C {posix_path} tag -l "v0.1.*"')

    if existing_tags:
        tags = sorted(existing_tags.splitlines())
        highest = 0
        for tag in tags:
            try:
                patch = int(tag.split(".")[-1])
                if patch > highest:
                    highest = patch
            except (ValueError, IndexError):
                pass
        next_ver = highest + 1
    else:
        next_ver = 0

    return f"v0.1.{next_ver}"


def clean_backup_dir():
    """Remove everything except .git, .gitignore, and README.md."""
    print(">>> Cleaning backup directory...")
    preserved = {".git", ".gitignore", "README.md"}
    for item in BACKUP_DIR.iterdir():
        if item.name in preserved:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    print("    Cleaned.")


def copy_main_files():
    """Copy main hermes SOUL.md, config.yaml, skills/, cron/, and memories/."""
    print(">>> Copying main files...")

    soul_src = HERMES_HOME / "SOUL.md"
    if soul_src.exists():
        shutil.copy2(soul_src, BACKUP_DIR / "SOUL.md")
        print(f"    Copied SOUL.md")

    cfg_src = HERMES_HOME / "config.yaml"
    if cfg_src.exists():
        shutil.copy2(cfg_src, BACKUP_DIR / "config.yaml")
        print(f"    Copied config.yaml")

    skills_src = HERMES_HOME / "skills"
    if skills_src.exists():
        skills_dest = BACKUP_DIR / "skills"
        if skills_dest.exists():
            shutil.rmtree(skills_dest)
        shutil.copytree(skills_src, skills_dest)
        print(f"    Copied skills/")

    cron_src = HERMES_HOME / "cron"
    if cron_src.exists():
        cron_dest = BACKUP_DIR / "cron"
        if cron_dest.exists():
            shutil.rmtree(cron_dest)
        shutil.copytree(cron_src, cron_dest)
        print(f"    Copied cron/")

    # memories/
    memories_src = HERMES_HOME / "memories"
    if memories_src.exists():
        memories_dest = BACKUP_DIR / "memories"
        if memories_dest.exists():
            shutil.rmtree(memories_dest)
        shutil.copytree(memories_src, memories_dest)
        print(f"    Copied memories/")


def copy_profile_files():
    """Copy SOUL.md, config.yaml, skills/, cron/, and memories/ from each profile."""
    print(">>> Copying profile files...")
    profiles_dest = BACKUP_DIR / "profiles"

    if not PROFILES_DIR.exists():
        print("    No profiles directory found. Skipping.")
        return

    for profile_dir in sorted(PROFILES_DIR.iterdir()):
        if not profile_dir.is_dir():
            continue
        profile_name = profile_dir.name
        profile_dest = profiles_dest / profile_name
        profile_dest.mkdir(parents=True, exist_ok=True)

        soul_src = profile_dir / "SOUL.md"
        if soul_src.exists():
            shutil.copy2(soul_src, profile_dest / "SOUL.md")
            print(f"    [{profile_name}] Copied SOUL.md")

        cfg_src = profile_dir / "config.yaml"
        if cfg_src.exists():
            shutil.copy2(cfg_src, profile_dest / "config.yaml")
            print(f"    [{profile_name}] Copied config.yaml")

        skills_src = profile_dir / "skills"
        if skills_src.exists():
            skills_dest = profile_dest / "skills"
            if skills_dest.exists():
                shutil.rmtree(skills_dest)
            shutil.copytree(skills_src, skills_dest)
            print(f"    [{profile_name}] Copied skills/")

        cron_src = profile_dir / "cron"
        if cron_src.exists():
            cron_dest = profile_dest / "cron"
            if cron_dest.exists():
                shutil.rmtree(cron_dest)
            shutil.copytree(cron_src, cron_dest)
            print(f"    [{profile_name}] Copied cron/")

        # memories/
        memories_src = profile_dir / "memories"
        if memories_src.exists():
            memories_dest = profile_dest / "memories"
            if memories_dest.exists():
                shutil.rmtree(memories_dest)
            shutil.copytree(memories_src, memories_dest)
            print(f"    [{profile_name}] Copied memories/")


def generate_skills_list():
    """Generate a markdown list of all skills organized by category.

    Handles two cases:
    1. Skills as subdirectories (e.g., skills/github/gh-auth/)
    2. SKILL.md directly in category folder (e.g., skills/profile-management/SKILL.md)
    """
    skills_by_category = {}
    skills_path = BACKUP_DIR / "skills"

    if not skills_path.exists():
        return ""

    for entry in sorted(skills_path.iterdir()):
        if not entry.is_dir():
            continue
        category = entry.name
        skills_by_category[category] = []

        # Case 1: Skills as subdirectories
        for skill_entry in sorted(entry.iterdir()):
            if skill_entry.is_dir():
                skill_name = skill_entry.name
                skills_by_category[category].append(f"- `{skill_name}`")

        # Case 2: SKILL.md directly in category folder
        if (entry / "SKILL.md").exists():
            skill_name = entry.name
            skills_by_category[category].append(f"- `{skill_name}`")

    lines = []
    for category, skills in sorted(skills_by_category.items()):
        if not skills:
            continue
        lines.append(f"### {category}")
        lines.append("")
        lines.extend(sorted(skills))
        lines.append("")

    return "\n".join(lines)


def update_readme():
    """Update README.md with skills list and metadata."""
    print(">>> Updating README.md...")

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    version = get_next_version()
    skills_md = generate_skills_list()

    readme = f"""# Agent Backup

Automated backup of Hermes environment configuration, skills, cron jobs, and memories.

## Metadata

- **Version:** {version}
- **Backup Date:** {timestamp}

## Structure

```
agent-backup/
├── .git/
├── .gitignore
├── README.md
├── config.yaml             # Main hermes config
├── SOUL.md                 # Main hermes SOUL.md
├── skills/                 # Main hermes skills
├── cron/                   # Main hermes cron
├── memories/               # Main hermes memories
└── profiles/
    ├── <profile>/
    │   ├── config.yaml     # <profile> config
    │   ├── SOUL.md         # <profile> SOUL.md
    │   ├── skills/         # <profile> skills
    │   ├── cron/           # <profile> cron
    │   └── memories/       # <profile> memories
```

## Skills Inventory

{skills_md}
"""

    readme_path = BACKUP_DIR / "README.md"
    readme_path.write_text(readme)
    print(f"    Updated README.md (version: {version})")

    return version


def commit_and_push(version):
    """Commit all changes and push with version tag."""
    print(f">>> Committing and pushing version {version}...")

    run("git add -A", cwd=str(BACKUP_DIR))

    diff = run("git diff --cached --name-only", cwd=str(BACKUP_DIR), check=False)
    if not diff:
        print("    No changes to commit.")
        return

    # Use a temp file for the commit message (handles multiline properly)
    commit_msg = f"backup: {version} — Hermes environment snapshot\n\nCopied config, skills, cron jobs, memories, and profile data."
    msg_file = Path("/tmp/.commit_msg")
    msg_file.write_text(commit_msg)
    run(f"git commit -F /tmp/.commit_msg", cwd=str(BACKUP_DIR))
    msg_file.unlink(missing_ok=True)

    run("git push origin master", cwd=str(BACKUP_DIR))

    run(f"git tag {version}", cwd=str(BACKUP_DIR))
    run(f"git push origin {version}", cwd=str(BACKUP_DIR))

    print(f"    Pushed to origin/master with tag {version}")


def ensure_remote():
    """Ensure the git remote points to the correct GitHub repo."""
    print(">>> Checking git remote...")
    result = run("git remote get-url origin", cwd=str(BACKUP_DIR), check=False)
    expected = f"https://github.com/{GITHUB_USER}/agent-backup.git"
    if result != expected:
        print(f"    Setting remote to {expected}")
        run(f"git remote set-url origin {expected}", cwd=str(BACKUP_DIR))
    else:
        print("    Remote already correct.")


def main():
    print("=" * 60)
    print("Hermes Agent Backup — agent-backup")
    print("=" * 60)
    print()

    # Detect paths dynamically
    global HERMES_HOME, BACKUP_DIR, PROFILES_DIR, GITHUB_USER
    HERMES_HOME = detect_hermes_home()
    BACKUP_DIR = detect_backup_dir(HERMES_HOME)
    PROFILES_DIR = HERMES_HOME / "profiles"
    GITHUB_USER = detect_github_user() or "unknown"

    print(f"  HERMES_HOME:  {HERMES_HOME}")
    print(f"  BACKUP_DIR:   {BACKUP_DIR}")
    print(f"  GitHub user:  {GITHUB_USER}")
    print()

    # Step 1: Clean
    clean_backup_dir()
    print()

    # Step 2: Copy main files
    copy_main_files()
    print()

    # Step 3: Copy profile files
    copy_profile_files()
    print()

    # Step 4: Update README and get version
    version = update_readme()
    print()

    # Step 5: Ensure remote and commit/push
    ensure_remote()
    commit_and_push(version)
    print()

    print("=" * 60)
    print(f"Backup complete! Version: {version}")
    print("=" * 60)


if __name__ == "__main__":
    main()
