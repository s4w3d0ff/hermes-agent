# Stack Exchange API v2.3 — Research Notes

Key findings from live documentation crawl and testing (July 2026).

## Endpoint quirks

### /search/advanced sorts by popularity, not relevance
On many sites (especially AskUbuntu), `/search/advanced` returns results sorted by score/popularity rather than true text-relevance. A query like "fingerprint reader" can surface a popular unrelated question at the top.

**Fix:** Fetch `pagesize=4*N` (up to 100), then re-rank client-side:
- Exact query match in title: +100
- Each query term in title: +10
- Each query term matching a tag: +20
- Each query term in body: +1

### /questions?q= is unreliable on some sites
The plain `/questions` endpoint with `q=` does full-text search but has broken relevance sorting on AskUbuntu — returns unrelated popular questions. Prefer `/search/advanced`.

### /answers does NOT support per-question filtering without auth
The unauthenticated `/answers` endpoint returns ALL answers on the site. You cannot filter by question ID without OAuth. Workaround: use `questions` endpoint and check `is_answered`.

### /sites is global — no site parameter
The `/sites` listing endpoint does not accept a `site` query param. Pass it directly: `https://api.stackexchange.com/2.3/sites?pagesize=100`.

## Rate limits (unauthenticated)

| Scope | Limit |
|-------|-------|
| Per IP per second | 30 concurrent requests; exceeded = dropped for 30s–5min |
| Daily quota | 300 req/day (shared by all apps on same IP+key) |
| With access_token | 10,000 req/day per user/app pair |

Check `quota_remaining` and `quota_max` in every response wrapper. Warn at <20%.

## Backoff behavior

API may return `"backoff": N` in the wrapper object on ANY method. You MUST wait N seconds before calling that same method again. All `/me` routes count as their `/users/{ids}` equivalent for backoff purposes.

## Error taxonomy (method calls)

| HTTP | error_name | Meaning |
|------|-----------|---------|
| 400 | bad_parameter | Invalid param value (key, site, etc.) |
| 401 | access_token_required | Auth needed for this method |
| 402 | invalid_access_token | Token is bad |
| 403 | access_denied | Token lacks required scope |
| 404 | no_method | Unknown endpoint or non-numeric ID passed where numeric expected |
| 405 | key_required | Method needs app key but none provided |
| 406 | access_token_compromised | Token invalidated (used over non-HTTPS) |
| 407 | write_failed | Write rejected; read error_message for details |
| 409 | duplicate_request | Same request_id submitted twice |
| 500 | internal_error | Unexpected server error |
| 502 | throttle_violation | Hit rate limit hard wall |
| 503 | temporarily_unavailable | Partial API outage; back off |

## Tag filtering on /questions

The `tagged` parameter accepts semicolon-separated tags and applies an AND constraint. Passing more than 5 tags always returns zero results.

## Built-in filters

| Filter | Meaning |
|--------|---------|
| `default` | Standard fields per type |
| `withbody` | default + body text included |
| `none` | No data fields |
| `total` | Only `.total` count |

For CLI output, always use `filter=withbody` so bodies are included.

## Common site parameters

| Parameter | Site | Use case |
|-----------|------|----------|
| askubuntu | Ask Ubuntu | Ubuntu questions |
| stackoverflow | Stack Overflow | Programming Q&A |
| serverfault | Server Fault | Sysadmin/networking |
| superuser | Super User | Consumer PC/hardware |
| unix | Unix & Linux | POSIX/Linux admin |

Use `se_search.py sites` to discover all 365+ sites.
