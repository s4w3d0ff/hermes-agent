"""HTTP client for camofox-browser API at localhost:9377."""

import logging
import requests

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:9377"


class CamofoxError(Exception):
    """Base error for camofox operations."""


class CamofoxNotRunning(CamofoxError):
    """Camofox server is not reachable."""


class TabError(CamofoxError):
    """Tab operation failed."""


def _check_health(base_url: str) -> bool:
    """Verify camofox is running by hitting /health."""
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        return resp.status_code == 200 and resp.json().get("ok") is True
    except Exception:
        return False


def _post(base_url: str, path: str, tab_id: str | None, body: dict, user_id: str = "main", session_key: str = "main") -> dict:
    """POST JSON to a camofox endpoint."""
    url = f"{base_url}/tabs/{tab_id}/{path}" if tab_id else f"{base_url}/{path}"
    # Merge userId and sessionKey into body (required by API)
    payload = {"userId": user_id, "sessionKey": session_key}
    payload.update(body)
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        raise CamofoxNotRunning("Cannot connect to camofox at {}. Is it running?".format(base_url))
    except requests.exceptions.Timeout:
        raise TabError("Request to camofox timed out after 30s")
    except requests.exceptions.HTTPError as exc:
        raise TabError(f"HTTP {resp.status_code}: {exc}")


def create_tab(base_url: str, user_id: str = "main", url: str | None = None, session_key: str = "main") -> str:
    """Create a tab and optionally navigate to a URL. Returns tab_id."""
    if not _check_health(base_url):
        raise CamofoxNotRunning("Camofox server is not reachable at {}".format(base_url))

    body: dict = {}
    if url:
        body["url"] = url

    result = _post(base_url, "tabs", None, body, user_id, session_key)

    tab_id = result.get("tabId") or result.get("id")
    if not tab_id:
        raise TabError(f"create_tab returned no tabId: {result}")
    return tab_id


def navigate(base_url: str, tab_id: str, url: str, user_id: str = "main", session_key: str = "main") -> dict:
    """Navigate an existing tab to a URL."""
    return _post(base_url, "navigate", tab_id, {"url": url}, user_id, session_key)


def get_html(base_url: str, tab_id: str, user_id: str = "main", session_key: str = "main") -> str:
    """Evaluate document.documentElement.outerHTML and return the raw HTML string."""
    result = _post(base_url, "evaluate", tab_id, {"expression": "document.documentElement.outerHTML"}, user_id, session_key)
    html = result.get("result")
    if not html:
        raise TabError("get_html returned empty result for tab {}".format(tab_id))
    return html


def get_rendered_text(base_url: str, tab_id: str, user_id: str = "main", session_key: str = "main") -> str:
    """Extract rendered text content from a JS-rendered page.

    Uses document.body.innerText to get the browser's accessible text.
    This works for SPA/React/Vue pages that require JavaScript rendering.

    For structured output (links, headings, code blocks), use get_html()
    followed by extract_content(html, format) in extractor.py which
    handles markup conversion via BeautifulSoup4.
    """
    # Use innerText instead of outerHTML for rendered text extraction.
    # This is simpler, more reliable, and avoids the complex JS that
    # caused HTTP 500 errors on the camofox evaluate endpoint.
    result = _post(
        base_url, "evaluate", tab_id,
        {"expression": "document.body.innerText"},
        user_id, session_key,
    )
    text = result.get("result")
    if not text:
        raise TabError("get_rendered_text returned empty for tab {}".format(tab_id))
    return text.strip()


def close_tab(base_url: str, tab_id: str, user_id: str = "main", session_key: str = "main") -> bool:
    """Close a tab. Returns True on success."""
    url = f"{base_url}/tabs/{tab_id}?userId={user_id}&sessionKey={session_key}"
    try:
        resp = requests.delete(url, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("Failed to close tab %s at %s: %s", tab_id, base_url, exc)
        return False


class CamofoxSession:
    """Context-manager session for camofox tab lifecycle."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, user_id: str = "main"):
        self.base_url = base_url
        self.user_id = user_id
        self.tab_id: str | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.tab_id:
            close_tab(self.base_url, self.tab_id)
            self.tab_id = None
        return False

    def open(self, url: str | None = None) -> str:
        """Create a tab and optionally navigate. Returns tab_id."""
        self.tab_id = create_tab(self.base_url, self.user_id, url)
        return self.tab_id

    def navigate(self, url: str) -> dict:
        """Navigate to URL."""
        if not self.tab_id:
            raise TabError("No open tab. Call open() first.")
        return navigate(self.base_url, self.tab_id, url)

    def get_html(self) -> str:
        """Get raw HTML of current page."""
        if not self.tab_id:
            raise TabError("No open tab. Call open() first.")
        return get_html(self.base_url, self.tab_id)

    def get_rendered_text(self) -> str:
        """Get rendered text content via JS evaluation."""
        if not self.tab_id:
            raise TabError("No open tab. Call open() first.")
        return get_rendered_text(self.base_url, self.tab_id)
