#!/usr/bin/env python3
"""
Stack Exchange API CLI client.
Query any Stack Exchange site for questions, answers, or tags with clean output.

Usage:
    se_search.py site question [--tags TAG1,TAG2] [--sort votes|activity|creation] [--limit N] [--no-body]
    se_search.py site answers  --question-id ID [--limit N] [--no-body]
    se_search.py site tags     [--inname SUBSTRING] [--sort popular|activity|name] [--limit N]
    se_search.py site list                          # list all SE sites and exit

Supported sites (site parameter): askubuntu, stackoverflow, serverfault, superuser, unix, codegolf, ...
  Run "se_search.py sites" to see the full discoverable list.

Design decisions:
  - No auth required for read-only queries; uses unauthenticated API (300 req/day quota).
  - Always requests filter=withbody so question/answer bodies are included by default.
    Pass --no-body to strip body text from output.
  - Output is scrubbed: only title, tags, score, answer_count, link, and optional body are shown.
  - Rate-limit aware: checks quota_remaining in wrapper; warns when below 20%.
  - Handles backoff field: if the API returns a backoff seconds value, waits before continuing.
  - Handles throttling errors (502) and temporary unavailability (503) with retries.
  - All dates are unix epoch; converted to human-readable in output.

Environment variables:
    SE_API_KEY   (optional) App key for higher rate limits. Passed as &key= parameter.
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API_BASE = "https://api.stackexchange.com/2.3"

# Sites we know about without needing to hit the API.
KNOWN_SITES = {
    "askubuntu": ("Ask Ubuntu", "Ubuntu users and developers"),
    "stackoverflow": ("Stack Overflow", "Professional and enthusiast programmers"),
    "serverfault": ("Server Fault", "System and network administrators"),
    "superuser": ("Super User", "Computer enthusiasts and power users"),
    "unix": ("Unix & Linux", "Users of Unix-based operating systems"),
    "askubuntu.com": ("Ask Ubuntu", "Ubuntu users and developers"),
    "stackoverflow.com": ("Stack Overflow", "Professional and enthusiast programmers"),
    "serverfault.com": ("Server Fault", "System and network administrators"),
    "superuser.com": ("Super User", "Computer enthusiasts and power users"),
    "unix.stackexchange.com": ("Unix & Linux", "Users of Unix-based operating systems"),
}


def build_url(endpoint, site, params=None):
    """Build a fully-qualified Stack Exchange API URL."""
    url = f"{API_BASE}/{endpoint}"
    qs = {"site": site}
    if params:
        qs.update(params)
    # Inject optional app key from env
    api_key = os.environ.get("SE_API_KEY")
    if api_key:
        qs["key"] = api_key
    return f"{url}?{urllib.parse.urlencode(qs)}"


def fetch_json(url, retries=3, backoff_base=2):
    """
    Fetch a JSON response from the API with retry logic for transient errors.

    Retries on:
      - HTTP 502 (throttle_violation)
      - HTTP 503 (temporarily_unavailable)
      - Connection errors / timeouts

    Returns parsed dict. Exits on non-retryable errors (400, 401, etc.)
    after parsing the JSON error response from the API.
    """
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                # Handle gzip transparently (urllib does this automatically in py3)
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            # Try to parse the API's JSON error body for a friendly message
            err_body = None
            try:
                err_body = json.loads(e.read())
            except Exception:
                pass

            if e.code == 502 or e.code == 503:
                wait = backoff_base ** attempt
                msg = f"[WARN] HTTP {e.code} (attempt {attempt}/{retries})"
                if err_body and "error_message" in err_body:
                    msg += f": {err_body['error_message']}"
                print(msg + f", retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            else:
                # Non-retryable: 400 bad_parameter, 401 auth, etc.
                if err_body and "error_message" in err_body:
                    print(f"[ERROR] {err_body.get('error_name', 'api_error')}: {err_body['error_message']}", file=sys.stderr)
                else:
                    print(f"[ERROR] HTTP {e.code}: {e.reason}", file=sys.stderr)
                sys.exit(2)
        except (urllib.error.URLError, OSError) as e:
            wait = backoff_base ** attempt
            print(f"[WARN] Network error (attempt {attempt}/{retries}): {e}, retrying in {wait}s...", file=sys.stderr)
            time.sleep(wait)

    print("[ERROR] Failed after all retries", file=sys.stderr)
    sys.exit(1)


def check_wrapper(resp):
    """Check the common wrapper for errors and throttle signals."""
    # Error fields are always present on error responses (even if filtered out normally)
    if "error_id" in resp:
        err = resp["error_name"] or "unknown"
        msg = resp.get("error_message", "no message")
        eid = resp.get("error_id", "?")
        print(f"[ERROR] Stack Exchange API error {eid} ({err}): {msg}", file=sys.stderr)
        sys.exit(2)

    # Quota tracking
    quota_max = resp.get("quota_max", 300)
    quota_remaining = resp.get("quota_remaining", "?")
    if isinstance(quota_remaining, (int, float)):
        pct = quota_remaining / quota_max * 100
        if pct < 20 and pct > 0:
            print(f"[WARN] API quota low: {quota_remaining}/{quota_max} remaining ({pct:.0f}%)", file=sys.stderr)

    # Backoff field: must wait before calling this method again
    backoff = resp.get("backoff")
    if backoff:
        print(f"[INFO] API requested backoff of {backoff}s, waiting...", file=sys.stderr)
        time.sleep(backoff)


def unix_to_iso(ts):
    """Convert unix timestamp to ISO-like string."""
    if ts is None:
        return "N/A"
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def scrub_question(q, show_body=True):
    """Format a single question object for display."""
    lines = []
    # Title and link
    title = q.get("title", "(no title)")
    link = q.get("link", "")
    lines.append(f"  {title}")
    if link:
        lines.append(f"  Link: {link}")

    # Tags
    tags = q.get("tags", [])
    if tags:
        lines.append(f"  Tags: {', '.join(tags)}")

    # Score and answers
    score = q.get("score", "?")
    ans = q.get("answer_count", "?")
    is_answered = q.get("is_answered", False)
    answered_str = " [ANSWERED]" if is_answered else ""
    lines.append(f"  Score: {score} | Answers: {ans}{answered_str}")

    # Closed info
    closed_reason = q.get("closed_reason")
    if closed_reason:
        lines.append(f"  Closed reason: {closed_reason}")

    # Dates
    created = unix_to_iso(q.get("creation_date"))
    last_active = unix_to_iso(q.get("last_activity_date"))
    lines.append(f"  Created: {created} | Last active: {last_active}")

    # Body (scrubbed of HTML, shown only if requested)
    if show_body:
        body = q.get("body", "")
        if body:
            # Strip HTML tags for readability
            import re
            text = re.sub(r"<[^>]+>", "", body)
            text = text.replace("&lt;", "<").replace("&gt;", ">")
            text = text.replace("&amp;", "&").replace("&quot;", '"')
            # Truncate to ~500 chars for terminal readability
            if len(text) > 500:
                text = text[:497] + "..."
            lines.append("")
            lines.append(f"  Body:\n{text}")

    return "\n".join(lines)


def scrub_answer(a, show_body=True):
    """Format a single answer object for display."""
    lines = []
    qid = a.get("question_id", "?")
    is_accepted = a.get("is_accepted", False)
    score = a.get("score", "?")

    # Owner info
    owner = a.get("owner", {})
    author = owner.get("display_name", "Anonymous")
    rep = owner.get("reputation", "?")

    lines.append(f"  Answer (by {author}, rep {rep}){' [ACCEPTED]' if is_accepted else ''}")
    lines.append(f"  Score: {score} | Question ID: {qid}")

    if show_body:
        body = a.get("body", "")
        if body:
            import re
            text = re.sub(r"<[^>]+>", "", body)
            text = text.replace("&lt;", "<").replace("&gt;", ">")
            text = text.replace("&amp;", "&").replace("&quot;", '"')
            if len(text) > 500:
                text = text[:497] + "..."
            lines.append("")
            lines.append(f"  Body:\n{text}")

    return "\n".join(lines)


def scrub_tag(t):
    """Format a single tag object."""
    name = t.get("name", "?")
    count = t.get("count", "?")
    is_rquestion = t.get("is_rquestion", False)
    rquestion_count = t.get("has_synonyms", False)
    lines = [f"  {name}: {count} questions"]
    if is_rquestion:
        lines.append(f"  (has synonym)")
    return "\n".join(lines)


def cmd_questions(site, query, **kwargs):
    """Search for questions on the given site using /search/advanced with client-side relevance filtering."""
    # Fetch more results to allow client-side relevance scoring
    fetch_limit = min(kwargs.get("limit", 5), 100) * 4  # fetch up to 4x more for scoring
    params = {
        "order": kwargs.get("order", "desc"),
        "sort": kwargs.get("sort", "votes"),  # use votes so we get popular+relevant results
        "filter": "withbody",
        "q": query,
        "pagesize": str(min(fetch_limit, 100)),
    }

    # Optional tag filter: AND constraint (semicolon-separated)
    if kwargs.get("tags"):
        params["tagged"] = ";".join(kwargs["tags"])

    url = build_url("search/advanced", site, params)
    resp = fetch_json(url)
    check_wrapper(resp)

    items = resp.get("items", [])

    # Client-side relevance scoring: match query terms against title + tags + body.
    # The API returns results sorted by popularity (not true relevance), so we re-rank.
    query_terms = [t.lower() for t in query.split() if len(t) > 2]
    scored = []
    for q in items:
        score = 0
        title_lower = (q.get("title", "") or "").lower()
        tags = [t.lower() for t in q.get("tags", [])]
        body_lower = (q.get("body", "") or "").lower()

        # Exact match on query string in title gets highest weight
        if query.strip().lower() in title_lower:
            score += 100
        else:
            # Each query term found in title
            for term in query_terms:
                if term in title_lower:
                    score += 10

            # Tags matching query terms (high signal)
            for term in query_terms:
                if term in tags:
                    score += 20

            # Body matches (lower weight)
            for term in query_terms:
                if term in body_lower:
                    score += 1

        scored.append((score, q))

    # Sort by relevance score descending, then take top N
    scored.sort(key=lambda x: (-x[0], x[1].get("score", 0)))
    items = [q for _, q in scored[:fetch_limit]]

    has_more = resp.get("has_more", False)

    print(f"\nQuestions on {site} matching '{query}' ({len(items)} results shown):")
    for i, item in enumerate(items, 1):
        if i > 1:
            print("---")
        print(scrub_question(item, show_body=not kwargs.get("no_body")))

    if has_more:
        print(f"\n[NOTE] More results available (has_more=true). Use --limit to fetch more.")


def cmd_answers(site, **kwargs):
    """Search for answers on the given site.

    Note: The unauthenticated /answers endpoint returns ALL answers on the
    site and does NOT support filtering by question ID. To find answers for a
    specific question without auth, use 'se_search.py questions <query>' and
    look at is_answered in results. Authenticated sessions can create custom
    filters that include answer data per-question.
    """
    params = {
        "order": kwargs.get("order", "desc"),
        "sort": kwargs.get("sort", "activity"),
        "filter": "withbody",
        "pagesize": str(min(kwargs.get("limit", 5), 100)),
    }

    url = build_url("answers", site, params)
    resp = fetch_json(url)
    check_wrapper(resp)

    items = resp.get("items", [])
    print(f"\nAnswers on {site} ({len(items)} results shown):")
    for i, item in enumerate(items, 1):
        if i > 1:
            print("---")
        print(scrub_answer(item, show_body=not kwargs.get("no_body")))


def cmd_tags(site, **kwargs):
    """List tags on the given site."""
    params = {
        "order": kwargs.get("order", "desc"),
        "sort": kwargs.get("sort", "popular"),
        "pagesize": str(min(kwargs.get("limit", 50), 100)),
    }

    if kwargs.get("inname"):
        params["inname"] = kwargs["inname"]

    url = build_url("tags", site, params)
    resp = fetch_json(url)
    check_wrapper(resp)

    items = resp.get("items", [])
    print(f"\nTags on {site} ({len(items)} results shown):")
    for i, item in enumerate(items, 1):
        if i > 1:
            print("---")
        print(scrub_tag(item))


def cmd_list_sites():
    """Fetch and display all Stack Exchange sites."""
    # /sites is a global endpoint — no site parameter needed
    url = f"{API_BASE}/sites?pagesize=100"
    api_key = os.environ.get("SE_API_KEY")
    if api_key:
        url += f"&key={api_key}"
    resp = fetch_json(url)
    check_wrapper(resp)

    items = resp.get("items", [])
    has_more = resp.get("has_more", False)
    page = 1

    while has_more:
        page += 1
        url = f"{API_BASE}/sites?pagesize=100&page={page}"
        if api_key:
            url += f"&key={api_key}"
        resp = fetch_json(url)
        check_wrapper(resp)
        items.extend(resp.get("items", []))
        has_more = resp.get("has_more", False)

    print(f"\nStack Exchange sites ({len(items)} total):")
    for site in sorted(items, key=lambda s: s.get("name", "")):
        name = site.get("name", "?")
        api_param = site.get("api_site_parameter", "?")
        audience = site.get("audience", "")
        print(f"  {api_param:30s} | {name:30s} | {audience}")


def main():
    global os
    import os

    parser = argparse.ArgumentParser(
        description="Query Stack Exchange sites via the v2.3 API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s askubuntu "ssh connection timeout" --tags networking,server --sort votes --limit 5
  %(prog)s stackoverflow "python asyncio tutorial" --tags python --limit 3
  %(prog)s askubuntu answers --sort votes --limit 3
  %(prog)s askubuntu tags --inname ubuntu --limit 20
  %(prog)s sites
        """,
    )

    parser.add_argument("site", nargs="?", default=None, help="Stack Exchange site parameter (e.g. askubuntu, stackoverflow)")
    sub = parser.add_subparsers(dest="command", required=True)

    # questions subcommand
    qp = sub.add_parser("questions", aliases=["q"], help="Search for questions")
    qp.add_argument("query", help="Full-text search query")
    qp.add_argument("--tags", help="Comma-separated tags to filter (AND constraint)")
    qp.add_argument("--sort", choices=["activity", "votes", "creation", "hot", "week", "month"], default="votes")
    qp.add_argument("--limit", type=int, default=5, help="Max results (default: 5, max: 100)")
    qp.add_argument("--no-body", action="store_true", help="Omit body text from output")

    # answers subcommand
    ap = sub.add_parser("answers", aliases=["a"], help="List latest answers on the site")
    ap.add_argument("--sort", choices=["activity", "creation", "votes"], default="activity")
    ap.add_argument("--limit", type=int, default=5, help="Max results (default: 5, max: 100)")
    ap.add_argument("--no-body", action="store_true", help="Omit body text from output")

    # tags subcommand
    tp = sub.add_parser("tags", aliases=["t"], help="List tags on the site")
    tp.add_argument("--inname", help="Filter tags containing this substring")
    tp.add_argument("--sort", choices=["popular", "activity", "name"], default="popular")
    tp.add_argument("--limit", type=int, default=50, help="Max results (default: 50, max: 100)")

    # sites subcommand — takes no site arg
    sp = sub.add_parser("sites", help="List all Stack Exchange sites")

    args = parser.parse_args()

    # Dispatch
    if args.command in ("questions", "q"):
        cmd_questions(
            site=args.site,
            query=args.query,
            tags=args.tags.split(",") if args.tags else [],
            sort=args.sort,
            limit=args.limit,
            no_body=args.no_body,
        )
    elif args.command in ("answers", "a"):
        cmd_answers(
            site=args.site,
            sort=args.sort,
            limit=args.limit,
            no_body=args.no_body,
        )
    elif args.command in ("tags", "t"):
        cmd_tags(
            site=args.site,
            inname=args.inname,
            sort=args.sort,
            limit=args.limit,
        )
    elif args.command == "sites":
        cmd_list_sites()


if __name__ == "__main__":
    main()
