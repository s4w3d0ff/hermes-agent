"""BeautifulSoup4-based content extraction from HTML."""

import re
from bs4 import BeautifulSoup, Tag


# Tags to strip as noise
_NOISE_TAGS = ["script", "style", "noscript", "nav", "header", "footer", "aside"]

# Class-name patterns that indicate noise elements (exact set membership)
_NOISE_CLASSES_SET = {
    "cookie-banner", "ad", "ads", "advertisement",
    "sidebar", "side-bar", "navigation",
    "menu", "breadcrumb", "pagination", "pager",
    "share", "social", "widget", "related",
    "comments-section", "comment",
    "bottom-bar", "top-bar", "banner",
}

# Attribute patterns for hidden content
_HIDDEN_ATTRS = {"aria-hidden": "true", "hidden": "", "data-hidden": "true"}


def _strip_noise(soup: BeautifulSoup) -> None:
    """Remove noise tags, class-matched elements, and hidden content."""
    # Remove noise tags
    for tag_name in _NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    def _safe_get_attr(tag, attr_name):
        """Safely get an attribute from any BS4 node."""
        try:
            if hasattr(tag, 'attrs') and tag.attrs:
                return tag.attrs.get(attr_name)
        except Exception:
            pass
        return None

    # Remove elements with noise classes (exact match)
    for tag in soup.find_all(True):
        classes = _safe_get_attr(tag, "class") or []
        if not isinstance(classes, list):
            continue
        for cls in classes:
            if cls.lower() in _NOISE_CLASSES_SET:
                try:
                    tag.decompose()
                except Exception:
                    pass
                break  # Element was decomposed, move to next element

    # Remove hidden elements
    for tag in soup.find_all(True):
        for attr, val in _HIDDEN_ATTRS.items():
            try:
                has = tag.has_attr(attr)
            except (TypeError, AttributeError):
                continue
            if not has:
                continue
            tag_val = str(tag.attrs.get(attr, "")).lower()
            if val == "" or tag_val == val:
                try:
                    tag.decompose()
                except Exception:
                    pass


def _find_content_area(soup: BeautifulSoup) -> Tag | None:
    """Find the main content area using heuristics."""
    # Try common content selectors in order of priority
    selectors = [
        "article",
        "main",
        "#content",
        ".content",
        ".post",
        ".entry",
        '.post-content',
        '.article-content',
        '#main-content',
        'section.content',
    ]

    for selector in selectors[:-2]:
        candidate = soup.select_one(selector)
        if candidate:
            return candidate

    # Fallback: try any div with content-like class names
    for tag in soup.find_all("div"):
        classes = tag.get("class") or []
        if not isinstance(classes, list):
            continue
        has_content = any(
            c.lower() in ("content", "article", "post", "entry", "main")
            for c in classes
        )
        if not has_content:
            continue
        # Make sure it's not a noise div (exact match)
        is_noise = any(c.lower() in _NOISE_CLASSES_SET for c in classes)
        if not is_noise:
            return tag

    # Final fallback: body
    return soup.body


def _inner_text(tag: Tag) -> str:
    """Extract text from a tag, stripping inner HTML but preserving inline formatting markers."""
    # Walk the tag tree and extract text with simple inline markers.
    # Child text is NOT stripped per-child: stripping each fragment drops the
    # spaces that separate sibling tags (e.g. <code><span>git</span> clone</code>
    # would glue into "gitclone"). Whitespace runs are collapsed instead.
    parts = []
    for child in tag.children:
        if isinstance(child, str):
            parts.append(child)
        elif isinstance(child, Tag):
            if child.name in ("strong", "b"):
                parts.append(f"**{child.get_text()}**")
            elif child.name in ("em", "i"):
                parts.append(f"*{child.get_text()}*")
            elif child.name in ("code",):
                parts.append(f"`{child.get_text()}`")
            else:
                parts.append(_inner_text(child))
    return re.sub(r"[ \t]+", " ", "".join(parts)).strip()


def _extract_blocks(content: Tag, fmt: str = "text") -> list[dict]:
    """Extract content blocks with type metadata.

    Returns a list of dicts like:
        {"type": "heading", "level": 2, "text": "..."}
        {"type": "paragraph", "text": "..."}
        {"type": "list_item", "list_type": "ul"|"ol", "text": "..."}
        ...
    """
    blocks: list[dict] = []

    for element in content.children:
        if not isinstance(element, Tag):
            continue

        # Headings (h1-h6)
        if element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = _inner_text(element).strip()
            if text:
                blocks.append({"type": "heading", "level": int(element.name[1]), "text": text})

        # Paragraphs
        elif element.name == "p":
            text = _inner_text(element).strip()
            if text:
                blocks.append({"type": "paragraph", "text": text})

        # Unordered lists - group consecutive <ul> children
        elif element.name == "ul":
            list_items = []
            for li in element.find_all("li", recursive=False):
                text = _inner_text(li).strip()
                if text:
                    list_items.append({"type": "list_item", "list_type": "ul", "text": text})
            blocks.extend(list_items)

        # Ordered lists - group consecutive <ol> children
        elif element.name == "ol":
            for idx, li in enumerate(element.find_all("li", recursive=False), start=1):
                text = _inner_text(li).strip()
                if text:
                    blocks.append({"type": "list_item", "list_type": f"ol:{idx}", "text": text})

        # Tables
        elif element.name == "table":
            for row in element.find_all("tr"):
                cells = []
                for cell in row.find_all(["td", "th"]):
                    text = _inner_text(cell).strip()
                    if text:
                        cells.append(text)
                if cells:
                    blocks.append({"type": "paragraph", "text": "| " + " | ".join(cells) + " |"})

        # Blockquotes
        elif element.name == "blockquote":
            text = _inner_text(element).strip()
            if text:
                blocks.append({"type": "paragraph", "text": "> " + text})

        # Code blocks - preserve line structure; collapse space runs only so
        # nested highlight spans don't glue words ("brew install", not "brewinstall")
        elif element.name in ("pre", "code"):
            text = re.sub(r"[ \t]+", " ", element.get_text()).strip()
            if text:
                blocks.append({"type": "code", "text": text})

        # Images - extract alt text
        elif element.name == "img":
            alt = element.get("alt", "").strip()
            if alt:
                blocks.append({"type": "paragraph", "text": f"![{alt}]"})

        # Fallback: recurse into unhandled containers
        else:
            child_blocks = _extract_blocks(element, fmt)
            blocks.extend(child_blocks)

    return blocks


def _blocks_to_text(blocks: list[dict]) -> str:
    """Join text-only blocks with normalized spacing."""
    lines = []
    for b in blocks:
        text = b["text"]
        if text.strip():
            lines.append(text)
    result = "\n\n".join(lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _blocks_to_markdown(blocks: list[dict]) -> str:
    """Convert structured blocks to markdown."""
    lines: list[str] = []

    for b in blocks:
        text = b["text"]
        if not text.strip():
            continue

        block_type = b["type"]

        if block_type == "heading":
            level = b["level"]
            prefix = "#" * level + " "
            lines.append(prefix + text)

        elif block_type == "paragraph":
            lines.append(text)

        elif block_type == "list_item":
            list_kind = b.get("list_type", "ul")
            if list_kind.startswith("ol:"):
                idx = int(list_kind.split(":")[1])
                lines.append(f"{idx}. {text}")
            else:
                lines.append(f"- {text}")

        elif block_type == "code":
            lines.append("```\n" + text + "\n```")

        else:
            lines.append(text)

    result = "\n\n".join(lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _clean_text(texts: list[str]) -> str:
    """Join text blocks with normalized spacing. (Legacy; uses _blocks_to_text now.)"""
    block_list = [{"type": "paragraph", "text": t} for t in texts if t.strip()]
    return _blocks_to_text(block_list)


def _to_markdown(texts: list[str]) -> str:
    """Convert extracted paragraphs to markdown. (Legacy; uses _blocks_to_markdown now.)"""
    block_list = [{"type": "paragraph", "text": t} for t in texts if t.strip()]
    return _blocks_to_markdown(block_list)


def extract_content(html_string: str, output_format: str = "text") -> str:
    """Extract clean text content from HTML.

    Args:
        html_string: Raw HTML string to parse.
        output_format: "text" for plain text, "markdown" for markdown format.

    Returns:
        Cleaned text string.
    """
    soup = BeautifulSoup(html_string, "lxml")

    # Step 1: Strip noise
    _strip_noise(soup)

    # Step 2: Find content area
    content = _find_content_area(soup)
    if content is None:
        content = soup

    # Step 3: Extract structured blocks
    fmt = "markdown" if output_format == "markdown" else "text"
    blocks = _extract_blocks(content, fmt)

    # Step 4: Format output
    if output_format == "markdown":
        return _blocks_to_markdown(blocks)
    return _blocks_to_text(blocks)
