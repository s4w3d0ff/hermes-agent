---
name: doc-scraping
description: Scrape multi-page docs into organized markdown files.
version: 0.1.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [documentation, scraping, web-extraction, batch-scraping, docs-site]
---

## When to Use
- Need to scrape an entire documentation site (multiple pages) into organized markdown files
- Documentation has a clear section hierarchy (e.g., /docs/api/, /docs/eventsub/, /docs/authentication/)
- You want each section in its own subdirectory with proper file naming
- The built-in `web_extract` tool doesn't handle the full site structure

## Prerequisites
- camofox-browser service running at localhost:9377 (verify with `curl -s http://localhost:9377/health`)
- Python 3.11+ installed
- Dependencies (`requests`, `beautifulsoup4`, `lxml`) in hermes agent venv

## Workflow

### Step 1: Discover URL structure from main pages

Documentation sites often have sub-pages that aren't obvious from the top-level URL. Parse the HTML of each main section to extract internal links:

```bash
curl -s https://dev.twitch.tv/docs/authentication/ | grep -oP 'href="(/docs/[^\"]+)"' | sort -u
```

This reveals the actual sub-page structure (e.g., `/docs/authentication/getting-tokens-oauth/`, not guessed paths).

### Step 2: Create output directory structure

Before scraping, create all necessary subdirectories. camosoup cannot create parent directories:

```bash
mkdir -p output/eventsub
mkdir -p output/authentication  
mkdir -p output/chat
```

### Step 3: Build scraper script with proper PYTHONPATH

When running camosoup via subprocess from Python, you MUST set PYTHONPATH explicitly (the wrapper doesn't do this):

```python
import os
import subprocess
from pathlib import Path

CAMOSOUPE_PATH = "/path/to/web-scrape/scripts"
OUTPUT_DIR = Path(__file__).parent / "output"

PAGES_TO_SCRAPE = [
    ("https://dev.twitch.tv/docs/api/reference/", "reference"),
    ("https://dev.twitch.tv/docs/eventsub/", "eventsub/index"),
    ("https://dev.twitch.tv/docs/eventsub/handling-websocket-events/", "eventsub/handling-websocket-events"),
]

def scrape_url(url: str, output_file: Path) -> bool:
    env = os.environ.copy()
    env["PYTHONPATH"] = CAMOSOUPE_PATH  # CRITICAL: must be set explicitly
    
    cmd = [
        "/home/s4w3d0ff/.hermes/hermes-agent/venv/bin/python",
        "-m", "camosoup", "scrape",
        url,
        "-f", "markdown",
        "-o", str(output_file),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
    return result.returncode == 0

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for url, rel_path in PAGES_TO_SCRAPE:
        output_file = OUTPUT_DIR / f"{rel_path}.md"
        scrape_url(url, output_file)
```

### Step 4: Run and verify

Execute the script and check for AccessDenied responses. Some pages may return access denied (XML error response). Verify all files have actual content, not just "AccessDenied".

## Pitfalls

- **PYTHONPATH must be explicit**: The `camosoup.sh` wrapper doesn't set PYTHONPATH for module resolution. When running via subprocess, you MUST pass it in the environment or get `[Errno 2] No such file or directory`.
- **Subdirectories must exist first**: camosoup cannot create parent directories. Pre-create all subdirs before scraping into them.
- **AccessDenied responses**: Some pages return HTTP-level access denied (XML `<Error><Code>AccessDenied</Code></Error>`). Check output files for this and skip or retry those URLs.
- **Don't guess URL paths**: Always parse the main page HTML to discover actual sub-page structure rather than guessing based on section names.

## Related Skills
- `web-scrape` - Single-page scraping via camofox-browser
