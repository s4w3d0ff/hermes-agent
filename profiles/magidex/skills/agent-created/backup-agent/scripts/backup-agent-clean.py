#!/usr/bin/env python3
"""Backup Hermes environment to GitHub repository.
Pure Python - no shell subprocess for file operations.
Cross-platform: handles Windows+MSYS path quirks."""

import os, sys, subprocess, fnmatch, datetime, shutil

# Auto-detect Hermes home directory
def detect_hermes_home():
    """Detect Hermes home directory across platforms."""
    home = os.environ.get("HOME", "")
    candidates = [
        os.path.join(home, "AppData", "Local", "hermes"),  # Windows
        os.path.join(home, ".hermes"),                      # POSIX
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    # Fallback: try USERPROFILE on Windows
    up = os.environ.get("USERPROFILE", "")
    alt = os.path.join(up, "AppData", "Local", "hermes")
    if os.path.isdir(alt):
        return alt
    return os.path.join(home, ".hermes")  # default fallback

HERMES_HOME = detect_hermes_home()
BACKUP_DIR = os.path.join(HERMES_HOME, "agent-backup")

# GitHub user — auto-detected from remote if possible
GITHUB_USER = "s4w3d0ff"  # Override detected from remote URL


def run(cmd):
    """Run a command and return (exit_code, stdout, stderr).
    
    On Windows+MSYS, backslashes in paths get interpreted as shell escape sequences.
    Convert Windows paths to forward slashes before passing to subprocess.
    """
    converted = []
    for arg in cmd:
        if "\\" in arg:
            arg = arg.replace("\\", "/")
        converted.append(arg)
    result = subprocess.run(converted, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def clean_dir():
    """Clean backup directory keeping .git, .gitignore, README.md."""
    keep = {".git", ".gitignore", "README.md"}
    for entry in os.listdir(BACKUP_DIR):
        if entry not in keep:
            path = os.path.join(BACKUP_DIR, entry)
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                try:
                    os.remove(path)
                except OSError:
                    pass
    print("  Directory cleaned.")


def write_gitignore():
    content = """# Runtime / generated artifacts
*.lock
.usage*
*.usage*
*manifest*

# Python artifacts
__pycache__/
*.pyc
*.pyo
*.egg-info/
.eggs/
dist/
build/
*.whl

# IDE / editor
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Logs
*.log

# Temporary files
*.tmp
*.temp
"""
    with open(os.path.join(BACKUP_DIR, ".gitignore"), "w") as f:
        f.write(content)
    print("  .gitignore written.")


def copy_file_safe(src, dst):
    """Copy a single file using shutil.copy2."""
    try:
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"  Warning: copy failed for {src}: {e}")
        return False


def copy_dir_safe(src, dst):
    """Copy directory tree using pure Python shutil.copytree."""
    if not os.path.isdir(src):
        return False
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"  Copied: {src} -> {dst}")
    return True


def copy_main_files():
    """Copy main Hermes files from AppData/Local/hermes."""
    print("Copying main files...")
    for fname in ["SOUL.md", "config.yaml"]:
        src = os.path.join(HERMES_HOME, fname)
        dst = os.path.join(BACKUP_DIR, fname)
        if os.path.exists(src):
            copy_file_safe(src, dst)
    for dname in ["skills", "cron", "memories"]:
        src = os.path.join(HERMES_HOME, dname)
        if os.path.isdir(src):
            dst = os.path.join(BACKUP_DIR, dname)
            copy_dir_safe(src, dst)
    print("  Main files copied.")


def copy_profile_files():
    """Copy profile directories."""
    profiles_dir = os.path.join(HERMES_HOME, "profiles")
    if not os.path.isdir(profiles_dir):
        print("  No profiles directory found.")
        return
    dst_profiles = os.path.join(BACKUP_DIR, "profiles")
    os.makedirs(dst_profiles, exist_ok=True)
    for profile_name in sorted(os.listdir(profiles_dir)):
        profile_src = os.path.join(profiles_dir, profile_name)
        if not os.path.isdir(profile_src):
            continue
        profile_dst = os.path.join(dst_profiles, profile_name)
        copy_dir_safe(profile_src, profile_dst)
    print("  Profiles copied.")


def generate_skills_list():
    """Generate markdown inventory of skills from backup dir."""
    skills_path = os.path.join(BACKUP_DIR, "skills")
    if not os.path.isdir(skills_path):
        return ""
    lines = []
    for entry in sorted(os.listdir(skills_path)):
        entry_path = os.path.join(skills_path, entry)
        if not os.path.isdir(entry_path):
            continue
        lines.append(f"### {entry}")
        lines.append("")
        for skill_entry in sorted(os.listdir(entry_path)):
            skill_path = os.path.join(entry_path, skill_entry)
            if os.path.isdir(skill_path):
                lines.append(f"- `{skill_entry}`")
            elif os.path.isfile(skill_path) and skill_entry == "SKILL.md":
                lines.append(f"- `{entry}`")
        lines.append("")
    return "\n".join(lines)


def determine_version():
    """Determine next version number by checking remote tags.
    
    Always fetch remote tags first to avoid stale local state.
    Use fnmatch instead of shell glob to avoid MSYS quote stripping.
    """
    # Fetch remote tags to ensure we have the latest
    run(["git", "-C", BACKUP_DIR, "fetch", "origin", "--tags"])
    
    rc, output, _ = run(["git", "-C", BACKUP_DIR, "tag", "-l"])
    if rc != 0 or not output:
        return "v0.1.0"
    
    tags = [t.strip() for t in output.split('\n') if t.strip()]
    v01_tags = [t for t in tags if fnmatch.fnmatch(t, 'v0.1.*')]
    if not v01_tags:
        return "v0.1.0"
    
    highest = 0
    for tag in v01_tags:
        try:
            num = int(tag.split(".")[-1])
            if num > highest:
                highest = num
        except ValueError:
            pass
    
    return f"v0.1.{highest + 1}"


def write_readme(version):
    """Generate and write README.md with skills inventory."""
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    skills_list = generate_skills_list()
    
    readme = f"""# Agent Backup

Automated backup of Hermes environment configuration, skills, and cron jobs.

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
    │   ├── config.yaml
    │   ├── SOUL.md
    │   ├── skills/
    │   ├── cron/
    │   └── memories/
```

## Skills Inventory

{skills_list}
"""
    with open(os.path.join(BACKUP_DIR, "README.md"), "w") as f:
        f.write(readme)
    print(f"  Written README.md (version {version})")


def commit_and_push(version):
    """Stage, commit, push, and tag."""
    print(f"Committing and pushing version {version}...")
    
    # Add all changes
    run(["git", "-C", BACKUP_DIR, "add", "-A"])
    
    # Check if there are changes
    rc, _, _ = run(["git", "-C", BACKUP_DIR, "diff", "--cached", "--quiet"])
    if rc == 0:
        print("  No changes to commit.")
        return False
    
    # Commit
    message = f"backup: {version} - Hermes environment snapshot"
    run(["git", "-C", BACKUP_DIR, "commit", "-m", message])
    print(f"  Committed: {message}")
    
    # Push to master
    rc, stdout, stderr = run(["git", "-C", BACKUP_DIR, "push", "origin", "master"])
    if rc != 0:
        print(f"  Push warning: {stderr[:300]}")
        # Try force push if there are conflicts
        print("  Trying force push...")
        rc, stdout, stderr = run(["git", "-C", BACKUP_DIR, "push", "-f", "origin", "master"])
        if rc != 0:
            print(f"  Force push failed: {stderr[:300]}")
    else:
        print("  Pushed to master.")
    
    # Create and push tag
    run(["git", "-C", BACKUP_DIR, "tag", version])
    rc, stdout, stderr = run(["git", "-C", BACKUP_DIR, "push", "origin", version])
    if rc != 0:
        print(f"  Tag push failed: {stderr[:300]}")
    else:
        print(f"  Pushed tag: {version}")
    
    return True


def main():
    print("=" * 60)
    print("Hermes Environment Backup Agent")
    print("=" * 60)
    print(f"Hermes home: {HERMES_HOME}")
    print(f"Backup dir:  {BACKUP_DIR}")
    print(f"GitHub user: {GITHUB_USER}")
    print()
    
    # Step 3: Write .gitignore
    write_gitignore()
    
    # Step 4: Clean directory
    clean_dir()
    
    # Step 5: Copy main files
    copy_main_files()
    
    # Step 6: Copy profile files
    copy_profile_files()
    
    # Step 7: Determine version and generate README
    version = determine_version()
    print(f"Version: {version}")
    write_readme(version)
    
    # Step 8: Commit and push
    changed = commit_and_push(version)
    
    print()
    if changed:
        print(f"Backup complete! Version: {version}")
    else:
        print("No changes detected. Backup skipped.")
    print("=" * 60)


if __name__ == "__main__":
    main()
