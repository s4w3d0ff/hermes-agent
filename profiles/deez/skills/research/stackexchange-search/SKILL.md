---
name: stackexchange-search
description: "Search Stack Exchange sites (AskUbuntu, Stack Overflow, Server Fault, Super User, etc.) via the v2.3 API with clean output, rate-limit awareness, and error handling."
version: 1.0.0
author: hermes-agent
---

# Stack Exchange Search

Query any Stack Exchange site for questions, answers, or tags using the official API v2.3. The script handles rate limits, backoffs, retries, and scrubs output to show only what matters.

## Prerequisites

- Python 3.10+ (uses only stdlib: urllib, json, argparse - no pip installs needed)
- Internet access to `api.stackexchange.com`

## Quick start

```bash
# Search AskUbuntu for Ubuntu server problems
se_search.py askubuntu questions "ssh connection timeout" --sort votes --limit 5

# Search Stack Overflow for Python asyncio issues
se_search.py stackoverflow "python asyncio event loop" --tags python --sort votes --limit 3

# List tags containing "ubuntu" on AskUbuntu
se_search.py askubuntu tags --inname ubuntu --limit 20

# List latest answers across a site
se_search.py askubuntu answers --sort votes --limit 3

# Show all Stack Exchange sites and their parameters
se_search.py sites
```

## Subcommands

### questions (q) - Search for questions
```
se_search.py <site> questions "search query" [options]
```
Uses `/search/advanced` for reliable full-text search across the site's question corpus.

**Options:**
- `--tags TAG1,TAG2` - Filter to questions with ALL specified tags (AND constraint, semicolon-separated internally)
- `--sort votes|activity|creation` - Sort order (default: activity)
- `--limit N` - Max results, 1-100 (default: 5)
- `--no-body` - Omit body text from output for compact display

### answers (a) - List latest answers
```
se_search.py <site> answers [options]
```
Lists the most recent answers on the site sorted by votes/activity/creation. Without authentication, filtering by question ID is not supported.

**Options:**
- `--sort activity|creation|votes` - Sort order (default: activity)
- `--limit N` - Max results, 1-100 (default: 5)
- `--no-body` - Omit body text from output

### tags (t) - List tags on a site
```
se_search.py <site> tags [options]
```
Lists tags sorted by popularity, activity, or name.

**Options:**
- `--inname SUBSTRING` - Filter to tags containing this substring (e.g., `--inname ubuntu` returns kubuntu, xubuntu, lubuntu, ...)
- `--sort popular|activity|name` - Sort order (default: popular)
- `--limit N` - Max results, 1-100 (default: 50)

### sites - List all Stack Exchange sites
```
se_search.py sites
```
Fetches and displays every Stack Exchange site with its API parameter, display name, target audience, and URL. Useful for discovering new sites beyond the common ones.

## Supported sites (common)

| Site param      | Display name     | Use case                              |
|-----------------|------------------|---------------------------------------|
| askubuntu       | Ask Ubuntu       | Ubuntu user/developer questions       |
| stackoverflow   | Stack Overflow   | General programming                   |
| serverfault     | Server Fault     | Sysadmin/networking                   |
| superuser       | Super User       | Consumer PC/hardware enthusiasts      |
| unix            | Unix & Linux     | POSIX/Linux administration            |

Run `se_search.py sites` for the full list of 180+ sites.

## Rate limits and API key

- **Unauthenticated:** 300 requests/day shared quota per IP + app key
- **Authenticated:** 10,000 requests/day per user/app pair
- Set `SE_API_KEY` env var with your registered app key for higher limits:
  ```bash
  export SE_API_KEY=your-app-key-here
  se_search.py askubuntu questions "gnome settings" --limit 5
  ```

## Error handling

The script handles these API error conditions gracefully:

| HTTP    | API error_name         | Behavior                          |
|---------|------------------------|-----------------------------------|
| 400     | bad_parameter          | Clean error message, exit code 2  |
| 401     | access_token_required  | Auth required                     |
| 502     | throttle_violation     | Retries with backoff              |
| 503     | temporarily_unavailable| Retries with backoff              |
| Any     | (backoff field)        | Waits specified seconds           |

Quota warnings fire when remaining quota drops below 20%.

## Output format

Each result shows:
- Title and link
- Tags
- Score and answer count (+ [ANSWERED] flag if applicable)
- Closed reason (if question was closed)
- Creation date and last activity date
- Body text (HTML-stripped, truncated to ~500 chars unless `--no-body`)

## Design notes

- **`/search/advanced` over `/questions?q=`**: The plain questions endpoint has unreliable full-text matching on some sites (especially AskUbuntu), returning unrelated results. The search/advanced endpoint provides proper relevance sorting.
- **No question-ID filter for answers without auth**: The unauthenticated `/answers` endpoint returns all answers site-wide and doesn't support per-question filtering. For finding answers to a specific question, use the questions subcommand and check `is_answered`.
- **Tags are AND-constrained**: When using `--tags foo,bar`, results must have BOTH tags. More than 5 tags will always return zero results (API limitation).
- **Bodies are HTML-stripped**: Raw API bodies contain Markdown/HTML. The script strips tags, decodes entities, and truncates to prevent terminal overflow.
