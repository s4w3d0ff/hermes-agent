"""CLI interface for camosoup."""

import argparse
import sys

from .fetcher import CamofoxNotRunning, TabError, create_tab, close_tab, get_html
from .extractor import extract_content


def scrape_url(url: str, output_file: str | None, output_format: str, user_id: str, base_url: str) -> int:
    """Scrape a URL and output extracted content."""
    tab_id = None
    session_key = "main"
    try:
        # Create tab and navigate
        tab_id = create_tab(base_url, user_id=user_id, url=url, session_key=session_key)

        # Wait briefly for page load then get HTML
        html = get_html(base_url, tab_id, user_id=user_id, session_key=session_key)

        # Extract clean content
        result = extract_content(html, output_format)

        # Output
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"Saved to {output_file}", file=sys.stderr)
        else:
            print(result)

        return 0

    except CamofoxNotRunning as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except TabError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if tab_id:
            close_tab(base_url, tab_id)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="camosoup",
        description="Fetch web pages via camofox-browser and extract clean text.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    scrape_parser = subparsers.add_parser("scrape", help="Scrape a URL and extract content")
    scrape_parser.add_argument("url", help="URL to scrape")
    scrape_parser.add_argument("-o", "--output", help="Output filename (default: stdout)")
    scrape_parser.add_argument(
        "-f", "--format",
        choices=["text", "markdown"],
        default="text",
        dest="fmt",
        help="Output format: text or markdown (default: text)",
    )
    scrape_parser.add_argument("--user-id", default="main", help="Camofox user ID (default: main)")
    scrape_parser.add_argument(
        "-b", "--base-url",
        default="http://localhost:9377",
        help="Camofox API base URL (default: http://localhost:9377)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    base_url = args.base_url

    return scrape_url(
        url=args.url,
        output_file=args.output,
        output_format=args.fmt,
        user_id=args.user_id,
        base_url=base_url,
    )
