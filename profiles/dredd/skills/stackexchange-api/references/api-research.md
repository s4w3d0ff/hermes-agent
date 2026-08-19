# Stack Exchange API v2.3 - Key Research Findings

Base: `https://api.stackexchange.com/2.3`
Auth: None required for read-only queries (300 req/day). Authenticated apps get 10k/day.

## CRITICAL PITFALL: Use `/search/advanced` not `/questions?q=` for text search

The plain `/questions?q=...` endpoint has **unreliable full-text matching** on several sites (notably AskUbuntu). It returns high-score results sorted by site-wide popularity, NOT by query relevance. The content of matched questions often bears no relation to the search term.

**Fix:** Always use `GET /search/advanced?q=...` for semantic text search across all sites.

## Response Wrapper (every response has these fields)

| Field | Type | Notes |
|-------|------|-------|
| `items` | array | The actual results |
| `has_more` | bool | More pages available |
| `page` / `page_size` | int | Echo of request params |
| `quota_max` | int | Daily quota (300 unauth, 10k auth) |
| `quota_remaining` | int | Remaining requests today |
| `backoff` | int | Must wait N seconds before calling this method again |
| `error_id` / `error_message` / `error_name` | present on error | Always present even if filtered out (by design) |

## Errors (HTTP 400 unless JSONP)

| error_name | HTTP Code | Meaning |
|------------|-----------|---------|
| `bad_parameter` | 400 | Invalid param (key, site, etc.) |
| `access_token_required` | 401 | Auth needed |
| `invalid_access_token` | 402 | Bad token |
| `access_denied` | 403 | Missing permissions |
| `no_method` | 404 | Endpoint doesn't exist (or non-numeric ID on /users/ endpoint) |
| `key_required` | 405 | App key needed |
| `internal_error` | 500 | API crash - retry |
| `throttle_violation` | 502 | Too many requests - retry with backoff |
| `temporarily_unavailable` | 503 | API down - retry with backoff |

## Questions Endpoint (`/questions`)

Parameters: `order` (asc/desc), `sort` (activity/votes/creation/hot/week/month), `tagged` (AND constraint, semicolons, max 5), `min`, `max`, `fromdate`, `todate`, `pagesize` (0-100).

Returns: question objects with title, link, tags, score, answer_count, is_answered, body, owner info, dates.

## Answers Endpoint (`/answers`)

Parameters: same paging + `order`, `sort` (activity/creation/votes), `min`, `max`.
Also supports `ids` to get answers for specific question IDs.

Returns: answer objects with body, score, is_accepted, owner info.

## Tags Endpoint (`/tags`)

Parameters: `inname` (substring filter), `sort` (popular/activity/name), paging params.

Returns: tag objects with name, count, has_synonyms.

## Sites Listing (`/sites`)

Fetches all SE sites. Paginated at 100 per page. Returns api_site_parameter, name, audience, site_url, site_type (main_site/meta_site), and related_sites links.

## Rate Limiting Rules

- >30 req/sec from single IP: dropped immediately (ban 30s–few min)
- Unauthenticated: shared IP quota, max of daily limits across apps on that IP (default 10k per app)
- Authenticated: per user/app pair, 10k/day (up to 5 distinct quotas per user)
- Per-method backoff: honor the `backoff` field - wait N seconds before calling that method again
- No semantically identical requests within 60s (heavy caching makes this wasteful)

## Filter System

| Built-in filter | Effect |
|-----------------|--------|
| `default` | Standard fields per type |
| `withbody` | Default + body text included |
| `none` | Empty, no fields |
| `total` | Only the `.total` count field |

## Date Format

All dates are unix epoch timestamps (seconds since 1970-01-01 UTC).
