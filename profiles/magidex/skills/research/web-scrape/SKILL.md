---
name: web-scrape
description: Fetch web pages via camofox-browser and extract clean text.
version: 0.1.0
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
- CLI or Python script invocation for headless scraping workflows
- When the built-in `web_extract` tool does not work/disabled

## Prerequisites
1. camofox-browser service must be running
2. camosoup installed somewhere on system (~/Projects/camosoup)
3. Python 3.11+ with dependencies: requests>=2.31.0, beautifulsoup4>=4.12.0, lxml>=5.0.0

Verify camofox is running before scraping:
```bash
curl -s http://localhost:9377/health                # expect {"ok":true}
```

## How to Run

### CLI (recommended for one-off scrapes)
Invoke through the `terminal` tool:

Scrape a URL and print text to stdout:
```bash
python -m camosoup scrape https://example.com
```

Save to file in markdown format:
```bash
python -m camosoup scrape https://example.com -o output.md -f markdown
```

Custom base URL or user ID:
```bash
python -m camosoup scrape https://example.com -b http://localhost:9377 --user-id main
```

### Python API (for scripts)
```python
from camosoup.fetcher import CamofoxSession
from camosoup.extractor import extract_content

# Context-manager style (auto-closes tab on exit)
with CamofoxSession(base_url="http://localhost:9377", user_id="main") as session:
    tab_id = session.open("https://example.com")
    html = session.get_html()
    text = extract_content(html, output_format="text")
    # markdown = extract_content(html, output_format="markdown")
# Tab is automatically closed here

# Or use low-level functions directly
from camosoup.fetcher import create_tab, get_html, close_tab
tab_id = create_tab(base_url="http://localhost:9377", user_id="main", url="https://example.com")
html = get_html(base_url="http://localhost:9377", tab_id=tab_id, user_id="main")
text = extract_content(html, output_format="text")
close_tab(base_url="http://localhost:9377", tab_id=tab_id, user_id="main")
```

## Quick Reference
CLI invocations (run from ~/Projects/camosoup):
```
python -m camosoup scrape <url>                        # text to stdout
python -m camosoup scrape <url> -o <file>              # text to file
python -m camosoup scrape <url> -f markdown            # markdown to stdout
python -m camosoup scrape <url> -o <file> -f markdown  # markdown to file
python -m camosoup scrape <url> --user-id <id>         # custom user ID
python -m camosoup scrape <url> -b http://host:port    # custom base URL
```

## Pitfalls
- camofox-browser must be running before scraping; otherwise CamofoxNotRunning is raised
- The service may report browserConnected:false in logs - this means no browser instance is attached yet, but the API is still reachable. First scrape may need a moment to start the browser.
- Tab IDs and sessions use user_id="main" by default; specify --user-id if managing multiple sessions
- The CamofoxSession context manager auto-closes tabs on exit (even on exception)
- Output format is only "text" or "markdown"; any other value will be rejected by argparse
- Noise removal strips: script, style, noscript, nav, header, footer, aside, cookie-banner, ad, sidebar, menu, breadcrumb, pagination, share, social, widget, comments-section, and more

## Verification
```bash
python -m camosoup scrape https://example.com -f markdown | head -5
```
Should return a short markdown-formatted excerpt from example.com with no ads or navigation elements.