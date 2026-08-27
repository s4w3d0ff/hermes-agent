---
name: camofox-browser
description: "Automate headless browser via REST API - create tabs, navigate, extract content, take screenshots."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [browser, automation, camofox, web-scraping, headless-browser, rest-api]
    related_skills: [dogfood]
---

# Camofox Browser Automation via REST API

## Overview

Use `camofox-browser` as a headless browser controller through its local REST API (port 9377). This skill covers the proven workflow for this Windows environment.

## Prerequisites

- camofox-browser must be installed and running: `which camofox-browser`
- Server listens on `http://localhost:9377` by default
- Node.js ≥ 18 required (this system has v24)

## Quick Start

### 1. Verify server is healthy

```bash
curl -s http://localhost:9377/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('ok') else 'FAIL')"
```

If the health check passes but `browserRunning` is false, the server is up - just no active browser session yet. That's normal; sessions are created on first tab creation.

### 2. Create a tab + navigate (two-step)

**Step A: Create a tab**
```bash
curl -s 'http://localhost:9377/tabs' \
  -X POST -H 'Content-Type: application/json' \
  -d '{"userId":"demo","sessionKey":"mykey"}'
# → {"tabId":"<uuid>","url":"about:blank"}
```

**Step B: Navigate to a URL** (replace `$TAB_ID` with the returned tab ID)
```bash
curl -s "http://localhost:9377/tabs/$TAB_ID/navigate?userId=demo" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","userId":"demo"}'
# → {"ok":true,"tabId":"<uuid>","url":"https://example.com/","refsAvailable":true}
```

### 3. Extract content and screenshots

**Text snapshot:**
```bash
curl -s "http://localhost:9377/tabs/$TAB_ID/snapshot?userId=demo&full=true"
# → {"url":"...","snapshot":"- heading \"Example Domain\" [level=1]\n- paragraph:...","refsCount":5}
```

**Screenshot:**
```bash
curl -s "http://localhost:9377/tabs/$TAB_ID/screenshot?userId=demo&fullPage=true" -o screenshot.png
# → binary PNG data
```

## Full API Reference

| Method | Endpoint | Body | Purpose |
|--------|----------|------|---------|
| `POST` | `/tabs` | `{"userId":"x","sessionKey":"y"}` | Create a tab (returns `tabId`) |
| `POST` | `/tabs/:id/navigate?userId=x` | `{"url":"https://..."}` | Navigate to URL |
| `GET`  | `/tabs/:id/snapshot?userId=x&full=true` | - | Text content + element refs |
| `GET`  | `/tabs/:id/screenshot?userId=x&fullPage=true` | - | PNG screenshot (binary) |
| `POST` | `/tabs/:id/click?userId=x` | `{"ref":"@e3"}` | Click an element by ref |
| `POST` | `/tabs/:id/type?userId=x` | `{"ref":"@e2","text":"hello"}` | Type into input field |
| `POST` | `/tabs/:id/press?userId=x` | `{"key":"Enter"}` | Press a key |
| `GET`  | `/tabs/:id/images?userId=x` | - | List images with URLs and alt text |
| `DELETE` | `/tabs/:id?userId=x` | - | Close tab |

### Key parameters

- **`userId`** (required): Session identifier string. Must be passed in the query string for GET requests, or body for POST/PUT.
- **`sessionKey`**: Groups tabs into sessions. Use a unique value per user/browser context.
- **`full=true`** on snapshot: Returns complete accessibility tree instead of interactive elements only.

### Response fields to watch

- `snapshot.refsCount`: Number of interactive element refs (`@e1`, `@e2`, ...). Use these with `/click` and `/type`.
- `snapshot.truncated`: If true, the page is too large for a single snapshot - scroll or paginate.
- `screenshot`: Binary PNG when using the screenshot endpoint.

## Common Patterns

### Pattern 1: Extract all links from a page

```bash
SNAP=$(curl -s "http://localhost:9377/tabs/$TAB_ID/snapshot?userId=demo&full=true")
echo "$SNAP" | grep 'link' 
# or parse the snapshot JSON for link elements
```

### Pattern 2: Click a link and wait for navigation

```bash
# 1. Get snapshot to find ref IDs
SNAP=$(curl -s "http://localhost:9377/tabs/$TAB_ID/snapshot?userId=demo&full=true")

# 2. Click the element (e.g., @e3)
curl -s "http://localhost:9377/tabs/$TAB_ID/click?userId=demo" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"ref":"@e3","userId":"demo"}'

# 3. Wait for navigation (wait a moment, then snapshot again)
sleep 2
curl -s "http://localhost:9377/tabs/$TAB_ID/snapshot?userId=demo&full=true"
```

### Pattern 3: Fill a form and submit

```bash
# 1. Snapshot to find field refs
SNAP=$(curl -s "http://localhost:9377/tabs/$TAB_ID/snapshot?userId=demo&full=true")
# → finds @e2 (input), @e5 (submit button)

# 2. Type into fields
curl -s "http://localhost:9377/tabs/$TAB_ID/type?userId=demo" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"ref":"@e2","text":"username","userId":"demo"}'

# 3. Submit (press Enter on the field or click submit)
curl -s "http://localhost:9377/tabs/$TAB_ID/press?userId=demo" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"key":"Enter","userId":"demo"}'
```

## Pitfalls & Troubleshooting

### Port already in use
If you see `{"error":"port in use","port":9377}`, another camofox-browser process is running. Kill it or use a different port in config.

### Session vs userId confusion
The API requires **both** `userId` (string) and `sessionKey` (or `listItemId`). The `userId` identifies the browser session; `sessionKey` groups tabs within that session. Pass them consistently - mismatched values cause `400 Bad Request`.

### Snapshot refs change between calls
Element ref IDs (`@e1`, `@e2`, ...) are **not stable** across requests. Always snapshot immediately before clicking or typing to get the current refs.

### Truncated snapshots
If a page is very large, `snapshot.truncated` will be true. Use `full=false` (default) for interactive elements only, or scroll through the page first.

### No system Firefox needed
camofox-browser bundles its own browser binary - do not look for a system `firefox` installation. The Node.js package handles everything.

## Related Skills

- **dogfood** - Use camofox-browser as an alternative to the built-in browser tools for QA testing and web scraping workflows.
