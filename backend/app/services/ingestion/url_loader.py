from __future__ import annotations

"""Fetch a web page and extract its readable text content."""

import re
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class WebContent:
    url: str
    title: str
    text: str
    content_type: str = "text/html"


async def fetch_url_content(url: str) -> WebContent:
    """Fetch a URL and extract clean, readable text from the HTML."""
    import httpx
    from bs4 import BeautifulSoup

    async with httpx.AsyncClient(
        timeout=30,
        follow_redirects=True,
        headers={"User-Agent": "AtlasAI/0.1"},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    content_type = response.headers.get("content-type", "")

    # If it's plain text / markdown, return directly.
    if "text/plain" in content_type or url.endswith(".txt") or url.endswith(".md"):
        return WebContent(
            url=url,
            title=url.split("/")[-1] or url,
            text=response.text,
            content_type="text/plain",
        )

    soup = BeautifulSoup(response.text, "lxml")

    # Remove non-content elements.
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else url

    # Try to find the main content area.
    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main is None:
        main = soup

    text = _clean_html(str(main))

    return WebContent(url=url, title=title, text=text, content_type="text/html")


def _clean_html(html: str) -> str:
    """Convert HTML to clean, readable plain text."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")

    # Convert certain tags to markdown-like formatting.
    for bold in soup.find_all(["strong", "b"]):
        bold.replace_with(f"**{bold.get_text()}**")
    for italic in soup.find_all(["em", "i"]):
        italic.replace_with(f"*{italic.get_text()}*")
    for code in soup.find_all("code"):
        code.replace_with(f"`{code.get_text()}`")
    for link in soup.find_all("a", href=True):
        text = link.get_text()
        href = link["href"]
        if text and href and not href.startswith("#"):
            link.replace_with(f"[{text}]({href})")

    # Convert headings to markdown.
    for level in range(1, 7):
        for heading in soup.find_all(f"h{level}"):
            prefix = "#" * level
            heading.replace_with(f"\n{prefix} {heading.get_text()}\n")

    # Add line breaks for block elements.
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.insert_before("\n")
        p.insert_after("\n")
    for li in soup.find_all("li"):
        li.insert_before("- ")

    text = soup.get_text()

    # Collapse whitespace but preserve structure.
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
