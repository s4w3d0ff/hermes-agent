---
name: stackexchange-api
description: Query Stack Exchange sites (AskUbuntu, StackOverflow, etc.) via the v2.3 API — search questions, answers, tags; handle rate limits, backoff, and error recovery with clean terminal output.
version: 1.0.0
author: Hermes Agent + user
platforms: [linux]
---

# Stack Exchange API Skill

Query any Stack Exchange site via the v2.3 REST API for questions, answers, or tags. Outputs scrubbed, human-readable terminal text — no HTML, no fluff.

## Quick Reference

```bash
# Search questions on AskUbuntu
se_search.py askubuntu questions "ssh connection timeout" --sort votes --limit 5

# Search with tag filter (AND constraint)
se_search.py askubuntu questions "wifi disconnect" --tags networking,wireless --sort votes

# Fetch answers for a specific question
se_search.py askubuntu answers --question-id 1034838 --limit 3

# List tags on a site
se_search.py askubuntu tags --inname ubuntu --limit 20

# Search StackOverflow for Python asyncio questions
se_search.py stackoverflow "python asyncio tutorial" --tags python --sort votes --limit 5

# List all SE sites
se_search.py sites

# Strip body text from output (--no-body)
se_search.py askubuntu questions "gnome shell freeze" --no-body
```

## Supported Sites (site parameter)

| Parameter | Site | Description |
|-----------|------|-------------|
| `askubuntu` | Ask Ubuntu | Ubuntu users and developers |
| `stackoverflow` | Stack Overflow | Professional programmers |
| `serverfault` | Server Fault | System/network admins |
| `superuser` | Super User | Computer enthusiasts |
| `unix` | Unix & Linux | Unix OS users |

Run `se_search.py sites` for the full list of 170+ sites.

## Script Location

`~/.hermes/skills/data-science/stackexchange-search/se_search.py`

Make it executable if you want direct invocation:
```bash
chmod +x ~/.hermes/skills/data-science/stackexchange-search/se_search.py
```

Or invoke via Python:
```bash
python3 se_search.py <site> <command> ...
```

## Architecture & API Design Decisions

### Always use `/search/advanced` for question text search
The plain `GET /questions?q=...` endpoint has **unreliable full-text matching** on several sites (notably AskUbuntu). It returns high-score results that don't actually match the query text, sorted by site-wide popularity rather than relevance. The `/search/advanced` endpoint gives correct semantic matching across all sites.

### Output scrubbing
The script strips HTML from body text, converts entities (`&lt;` → `<`, etc.), truncates bodies to 500 chars for terminal readability, and only shows essential fields: title, link, tags, score, answer count, dates. Use `--no-body` to suppress body text entirely.

### Rate limiting
- Unauthenticated: 300 requests/day per IP (shared quota)
- Authenticated with app key (`SE_API_KEY` env var): 10,000/day
- The script checks `quota_remaining` in every response wrapper and warns at <20% remaining.
- Respects the `backoff` field if returned by the API — waits that many seconds before continuing.

### Error handling
Retries on HTTP 502 (throttle_violation) and 503 (temporarily_unavailable) with exponential backoff. Exits cleanly on non-retryable errors (400 bad_parameter, 401 auth required).

## Supported Commands

| Command | Description |
|---------|-------------|
| `questions` / `q` | Full-text search for questions |
| `answers` / `a` | Search or filter answers |
| `tags` / `t` | List tags on a site |
| `sites` | List all Stack Exchange sites |

### Questions subcommand options

| Flag | Description |
|------|-------------|
| `--tags TAG1,TAG2` | Filter by tags (AND constraint; semicolons in URL) |
| `--sort activity\|votes\|creation\|hot\|week\|month` | Sort order (default: activity) |
| `--limit N` | Max results (1-100, default: 5) |
| `--no-body` | Omit body text from output |

### Answers subcommand options

| Flag | Description |
|------|-------------|
| `--question-id ID` | Filter to answers on this specific question |
| `--sort activity\|creation\|votes` | Sort order (default: activity) |
| `--limit N` | Max results (1-100, default: 5) |
| `--no-body` | Omit body text from output |

### Tags subcommand options

| Flag | Description |
|------|-------------|
| `--inname SUBSTRING` | Filter tags containing this substring |
| `--sort popular\|activity\|name` | Sort order (default: popular) |
| `--limit N` | Max results (1-100, default: 50) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SE_API_KEY` | Optional app key for higher rate limits (10k/day vs 300/day) |

## Response Data Fields Scrubbed

The script shows only these fields per item — all others are hidden:

**Questions:** title, link, tags, score, answer_count, is_answered, closed_reason, creation_date, last_activity_date, body (optional, HTML-stripped).

**Answers:** author name/reputation, score, question_id, is_accepted, body (optional, HTML-stripped).

**Tags:** tag name, question count.

## Rate Limit Best Practices

- Cache results locally for identical queries — the API docs say semantically identical requests should not be made more than once per minute due to heavy caching.
- Use `--limit` conservatively; each page fetch is one API call.
- Set `SE_API_KEY` if doing bulk work across multiple sites or days.
