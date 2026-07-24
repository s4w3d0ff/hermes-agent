---
name: web-scrape
description: Fetch web pages via camofox-browser and extract clean text.
version: 0.3.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [web-scraping, browser-automation, text-extraction, camofox, web_extract, scrape]
---

## When to Use
- Need to scrape/extract content from a URL and get clean, noise-free text output
- Need markdown-formatted output from a web page
- Want browser-rendered content (JS-dependent pages) via camofox-browser
- The built-in `web_extract` tool does not work or is disabled
- You need JavaScript-rendered pages (React/Vue/SPAs) that static fetch cannot handle

## Prerequisites
- camofox-browser service running at localhost:9377
- Python 3.11+ installed (system python3)
- Dependencies (`requests`, `beautifulsoup4`, `lxml`) installed in the hermes agent venv

### Verify camofox is running
```bash
curl -s http://localhost:9377/health
```
Expect: `{"ok":true, ...}`. If `browserConnected:false`, camofox server is up but no browser instance is attached, this is normal on first use; the first scrape will trigger a fresh browser launch.

### Install dependencies (one-time)
The dependencies are installed in the hermes agent venv. Check they are present:
```bash
~/.hermes/hermes-agent/venv/bin/pip list | grep -E 'bs4|lxml|requests'
```

If missing, install them in the hermes venv:
```bash
~/.hermes/hermes-agent/venv/bin/pip install requests beautifulsoup4 lxml
```

Do NOT create a local venv inside the skill folder. Always use the shared hermes agent venv.

## How to Run (use the wrapper)

The `camosoup.sh` wrapper handles venv activation and environment setup automatically. Run it from anywhere:

```bash
/path/to/web-scrape/scripts/camosoup.sh scrape https://example.com
```

No need to manually source the venv or set PYTHONPATH, the script resolves `$HOME/.hermes/hermes-agent/venv/bin/python3` at runtime.
