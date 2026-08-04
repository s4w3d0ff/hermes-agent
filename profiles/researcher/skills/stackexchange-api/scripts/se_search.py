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
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API_BASE = "https://api.stackexchange.com/2.3"


def build_url(endpoint, site, params=None):
    """Build a fully-qualified Stack Exchange API URL."""
    url = f"{API_BASE}/{endpoint}"
    qs = {"site": site}
    if params:
        qs.update(params)
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

    Returns parsed dict. Raises SystemExit on non-retryable errors.
    """
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code == 502 or e.code == 503:
                wait = backoff_base ** attempt
                print(f"[WARN] HTTP {e.code} (attempt {attempt}/{retries}), retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            else:
                raise
        except (urllib.error.URLError, OSError) as e:
            wait = backoff_base ** attempt
            print(f"[WARN] Network error (attempt {attempt}/{retries}): {e}, retrying in {wait}s...", file=sys.stderr)
            time.sleep(wait)

    print("[ERROR] Failed after all retries", file=sys.stderr)
    sys.exit(1)


def check_wrapper(resp):
    """Check the common wrapper for errors and throttle signals."""
    if "error_id" in resp:
        err = resp["error_name"] or "unknown"
        msg = resp.get("error_message", "no message")
        eid = resp.get("error_id", "?")
        print(f"[ERROR] Stack Exchange API error {eid} ({err}): {msg}", file=sys.stderr)
        sys.exit(2)

    quota_max = resp.get("quota_max", 300)
    quota_remaining = resp.get("quota_remaining", "?")
    if isinstance(quota_remaining, (int, float)):
        pct = quota_remaining / quota_max * 100
        if pct < 20 and pct > 0:
            print(f"[WARN] API quota low: {quota_remaining}/{quota_max} remaining ({pct:.0f}%)", file=sys.stderr)

    backoff = resp.get("backoff")
    if backoff:
        print(f"[INFO] API requested backoff of {backoff}s, waiting...", file=sys.stderr)
        time.sleep(backoff)


def unix_to_iso(ts):
    """Convert unix timestamp to ISO-like string."""
    if ts is None:
        return "N/A"
    from datetime import datetime, timezone
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def strip_html(text):
    """Strip HTML tags and unescape common entities."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&amp;", "&").replace("&quot;", '"')
    text = text.replace("&#39;", "'").replace("&apos;", "'")
    return text.strip()


def scrub_question(q, show_body=True):
    """Format a single question object for display."""
    lines = []
    title = q.get("title", "(no title)")
    link = q.get("link", "")
    lines.append(f"  {title}")
    if link:
        lines.append(f"  Link: {link}")

    tags = q.get("tags", [])
    if tags:
        lines.append(f"  Tags: {', '.join(tags)}")

    score = q.get("score", "?")
    ans = q.get("answer_count", "?")
    is_answered = q.get("is_answered", False)
    answered_str = " [ANSWERED]" if is_answered else ""
    lines.append(f"  Score: {score} | Answers: {ans}{answered_str}")

    closed_reason = q.get("closed_reason")
    if closed_reason:
        lines.append(f"  Closed reason: {closed_reason}")

    created = unix_to_iso(q.get("creation_date"))
    last_active = unix_to_iso(q.get("last_activity_date"))
    lines.append(f"  Created: {created} | Last active: {last_active}")

    if show_body:
        body = q.get("body", "")
        if body:
            text = strip_html(body)
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

    owner = a.get("owner", {})
    author = owner.get("display_name", "Anonymous")
    rep = owner.get("reputation", "?")

    lines.append(f"  Answer (by {author}, rep {rep}){' [ACCEPTED]' if is_accepted else ''}")
    lines.append(f"  Score: {score} | Question ID: {qid}")

    if show_body:
        body = a.get("body", "")
        if body:
            text = strip_html(body)
            if len(text) > 500:
                text = text[:497] + "..."
            lines.append("")
            lines.append(f"  Body:\n{text}")

    return "\n".join(lines)


def scrub_tag(t):
    """Format a single tag object."""
    name = t.get("name", "?")
    count = t.get("count", "?")
    has_synonyms = t.get("has_synonyms", False)
    lines = [f"  {name}: {count} questions"]
    if has_synonyms:
        lines.append(f"  (has synonyms)")
    return "\n".join(lines)


def cmd_questions(site, query, **kwargs):
    """Search for questions on the given site using /search/advanced."""
    params = {
        "order": kwargs.get("order", "desc"),
        "sort": kwargs.get("sort", "activity"),
        "filter": "withbody",
        "q": query,
        "pagesize": str(min(kwargs.get("limit", 5), 100)),
    }

    if kwargs.get("tags"):
        params["tagged"] = ";".join(kwargs["tags"])

    # Use /search/advanced for reliable full-text search.
    # The plain /questions?q= endpoint has unreliable text matching on some
    # sites (notably AskUbuntu), so we prefer the advanced search endpoint.
    url = build_url("search/advanced", site, params)
    resp = fetch_json(url)
    check_wrapper(resp)

    items = resp.get("items", [])
    has_more = resp.get("has_more", False)

    print(f"\nQuestions on {site} matching '{query}' ({len(items)} results shown):")
    for i, item in enumerate(items, 1):
        if i > 1:
            print("---")
        print(scrub_question(item, show_body=not kwargs.get("no_body")))

    if has_more:
        print(f"\n[NOTE] More results available (has_more=true). Use --limit to fetch more.")


def cmd_answers(site, **kwargs):
    """Search for answers on the given site."""
    params = {
        "order": kwargs.get("order", "desc"),
        "sort": kwargs.get("sort", "activity"),
        "filter": "withbody",
        "pagesize": str(min(kwargs.get("limit", 5), 100)),
    }

    if kwargs.get("question_id"):
        params["ids"] = str(kwargs["question_id"])

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
    url = build_url("sites", "stackoverflow", {"pagesize": "100"})
    resp = fetch_json(url)
    check_wrapper(resp)

    items = resp.get("items", [])
    has_more = resp.get("has_more", False)
    page = 1

    while has_more:
        page += 1
        url = build_url("sites", "stackoverflow", {"pagesize": "100", "page": str(page)})
        resp = fetch_json(url)
        check_wrapper(resp)
        items.extend(resp.get("items", []))
        has_more = resp.get("has_more", False)

    print(f"\nStack Exchange sites ({len(items)} total):")
    for site in sorted(items, key=lambda s: s.get("name", "")):
        name = site.get("name", "?")
        api_param = site.get("api_site_parameter", "?")
        audience = site.get("audience", "")
        url_site = site.get("site_url", "?")
        print(f"  {api_param:30s} | {name:30s} | {audience}")


def main():
    parser = argparse.ArgumentParser(
        description="Query Stack Exchange sites via the v2.3 API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s askubuntu "ssh connection timeout" --tags networking,server --sort votes --limit 5
  %(prog)s stackoverflow "python asyncio tutorial" --tags python --limit 3
  %(prog)s askubuntu answers --question-id 1034838 --limit 3
  %(prog)s askubuntu tags --inname ubuntu --limit 20
  %(prog)s sites
        """,
    )

    parser.add_argument("site", help="Stack Exchange site parameter (e.g. askubuntu, stackoverflow)")
    sub = parser.add_subparsers(dest="command", required=True)

    # questions subcommand
    qp = sub.add_parser("questions", aliases=["q"], help="Search for questions")
    qp.add_argument("query", help="Full-text search query")
    qp.add_argument("--tags", help="Comma-separated tags to filter (AND constraint)")
    qp.add_argument("--sort", choices=["activity", "votes", "creation", "hot", "week", "month"], default="activity")
    qp.add_argument("--limit", type=int, default=5, help="Max results (default: 5, max: 100)")
    qp.add_argument("--no-body", action="store_true", help="Omit body text from output")

    # answers subcommand
    ap = sub.add_parser("answers", aliases=["a"], help="Search for answers")
    ap.add_argument("--question-id", type=int, default=None, help="Filter to answers on this question ID")
    ap.add_argument("--sort", choices=["activity", "creation", "votes"], default="activity")
    ap.add_argument("--limit", type=int, default=5, help="Max results (default: 5, max: 100)")
    ap.add_argument("--no-body", action="store_true", help="Omit body text from output")

    # tags subcommand
    tp = sub.add_parser("tags", aliases=["t"], help="List tags on the site")
    tp.add_argument("--inname", help="Filter tags containing this substring")
    tp.add_argument("--sort", choices=["popular", "activity", "name"], default="popular")
    tp.add_argument("--limit", type=int, default=50, help="Max results (default: 50, max: 100)")

    # sites subcommand
    sub.add_parser("sites", help="List all Stack Exchange sites")

    args = parser.parse_args()

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
            question_id=args.question_id,
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
