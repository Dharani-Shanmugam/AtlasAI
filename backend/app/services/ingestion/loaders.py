from __future__ import annotations

import io
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)

SUPPORTED_TYPES = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".pdf": "application/pdf",
}

# Maximum content size to fetch from URLs (10 MB).
MAX_URL_CONTENT_BYTES = 10 * 1024 * 1024


class UnsupportedFileTypeError(ValueError):
    pass


@dataclass
class ExtractedText:
    text: str
    content_type: str
    page_count: int | None = None


def extract_text(filename: str, data: bytes) -> ExtractedText:
    import os

    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_TYPES:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext or 'unknown'}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_TYPES))}"
        )

    content_type = SUPPORTED_TYPES[ext]
    if ext == ".pdf":
        return _extract_pdf(data, content_type)
    return _extract_plain(data, content_type)


def _extract_plain(data: bytes, content_type: str) -> ExtractedText:
    for encoding in ("utf-8", "latin-1"):
        try:
            return ExtractedText(text=data.decode(encoding), content_type=content_type)
        except UnicodeDecodeError:
            continue
    return ExtractedText(text=data.decode("utf-8", errors="replace"), content_type=content_type)


def _extract_pdf(data: bytes, content_type: str) -> ExtractedText:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:  # some PDFs have broken content streams
            logger.warning("Skipping unreadable PDF page")
            text = ""
        if text.strip():
            pages.append(text)
    return ExtractedText(text="\n\n".join(pages), content_type=content_type, page_count=len(pages))
