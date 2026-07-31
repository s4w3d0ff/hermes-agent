#!/usr/bin/env python3
"""Scrape Twitch documentation pages and save as markdown files."""

import os
import subprocess
from pathlib import Path

# Configuration - update these paths for your environment
CAMOSOUPE_PATH = "/home/s4w3d0ff/.hermes/profiles/poolguy/skills/web-scrape/scripts"
OUTPUT_DIR = Path(__file__).parent / "output"

# Define all pages to scrape with proper directory structure
PAGES_TO_SCRAPE = [
    # Main reference page (root level)
    ("https://dev.twitch.tv/docs/api/reference/", "reference"),
    
    # EventSub section - files go into eventsub/ subdirectory
    ("https://dev.twitch.tv/docs/eventsub/", "eventsub/index"),
    ("https://dev.twitch.tv/docs/eventsub/handling-websocket-events/", "eventsub/handling-websocket-events"),
    ("https://dev.twitch.tv/docs/eventsub/handling-webhook-events/", "eventsub/handling-webhook-events"),
    ("https://dev.twitch.tv/docs/eventsub/handling-conduit-events/", "eventsub/handling-conduit-events"),
    ("https://dev.twitch.tv/docs/eventsub/manage-subscriptions/", "eventsub/manage-subscriptions"),
    ("https://dev.twitch.tv/docs/eventsub/websocket-reference/", "eventsub/websocket-reference"),
    ("https://dev.twitch.tv/docs/eventsub/eventsub-reference/", "eventsub/eventsub-reference"),
    ("https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/", "eventsub/eventsub-subscription-types"),
    
    # Authentication section - files go into authentication/ subdirectory
    ("https://dev.twitch.tv/docs/authentication/", "authentication/index"),
    ("https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/", "authentication/getting-tokens-oauth"),
    ("https://dev.twitch.tv/docs/authentication/getting-tokens-oidc/", "authentication/getting-tokens-oidc"),
    ("https://dev.twitch.tv/docs/authentication/refresh-tokens/", "authentication/refresh-tokens"),
    ("https://dev.twitch.tv/docs/authentication/register-app/", "authentication/register-app"),
    ("https://dev.twitch.tv/docs/authentication/revoke-tokens/", "authentication/revoke-tokens"),
    ("https://dev.twitch.tv/docs/authentication/scopes/", "authentication/scopes"),
    ("https://dev.twitch.tv/docs/authentication/validate-tokens/", "authentication/validate-tokens"),
    
    # Chat section - files go into chat/ subdirectory
    ("https://dev.twitch.tv/docs/chat/", "chat/index"),
    ("https://dev.twitch.tv/docs/chat/authenticating/", "chat/authenticating"),
    ("https://dev.twitch.tv/docs/chat/chatbot-guide/", "chat/chatbot-guide"),
    ("https://dev.twitch.tv/docs/chat/irc/", "chat/irc"),
    ("https://dev.twitch.tv/docs/chat/irc-migration/", "chat/irc-migration"),
    ("https://dev.twitch.tv/docs/chat/moderation/", "chat/moderation"),
    ("https://dev.twitch.tv/docs/chat/send-receive-messages/", "chat/send-receive-messages"),
    ("https://dev.twitch.tv/docs/chat/whispers/", "chat/whispers"),
]


def scrape_url(url: str, output_file: Path) -> bool:
    """Scrape a URL and save as markdown."""
    print(f"Scraping: {url}")

    # Set PYTHONPATH in environment for subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = CAMOSOUPE_PATH

    cmd = [
        "/home/s4w3d0ff/.hermes/hermes-agent/venv/bin/python",
        "-m", "camosoup", "scrape",
        url,
        "-f", "markdown",
        "-o", str(output_file),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        if result.returncode == 0:
            print(f"✓ Saved to: {output_file}")
            return True
        else:
            print(f"✗ Error scraping {url}: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Exception scraping {url}: {e}")
        return False


def main():
    """Main scraping logic."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0

    for url, rel_path in PAGES_TO_SCRAPE:
        # Create subdirectory structure if needed
        output_file = OUTPUT_DIR / f"{rel_path}.md"
        
        if scrape_url(url, output_file):
            success_count += 1
        else:
            fail_count += 1

    print(f"\n=== Done! ===")
    print(f"All documentation saved to: {OUTPUT_DIR}")
    print(f"Success: {success_count}, Failed: {fail_count}")


if __name__ == "__main__":
    main()
