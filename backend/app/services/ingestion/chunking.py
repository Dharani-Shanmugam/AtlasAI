from __future__ import annotations

"""Chunking splits a long document into small, self-contained pieces.

Why chunk? Embedding models have a token limit and, more importantly,
retrieval quality drops when a chunk contains too much unrelated content —
the vector for the whole chunk gets "averaged out" so no query matches well.
Small overlapping chunks keep each piece focused on a single idea.

Algorithm (two phases, nothing is ever lost or truncated):

1. *Natural split* — break the text recursively on the largest separator
   first (paragraph ``\\n\\n``), then line ``\\n``, sentence ``'. '``, and
   finally hard character cuts. Each resulting piece is ≤ ``chunk_size``.
2. *Greedy pack* — merge pieces into chunks. When a chunk would overflow,
   close it and start the next one *prefixed with the previous chunk's tail*
   (the overlap), so ideas straddling a boundary are preserved. Overlap is
   duplicated content, so trimming it when necessary costs nothing.
"""


def chunk_text(
    text: str,
    *,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> list[str]:
    """Split ``text`` into overlapping chunks of at most ``chunk_size`` chars."""
    if not text:
        return []

    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []

    pieces: list[str] = []
    _natural_split(text, ["\n\n", "\n", ". ", " "], chunk_size, pieces)
    return _pack(pieces, chunk_size, max(0, chunk_overlap))


def _natural_split(
    text: str,
    separators: list[str],
    chunk_size: int,
    out: list[str],
) -> None:
    """Recursively cut on the best separator, yielding pieces ≤ ``chunk_size``."""
    if len(text) <= chunk_size:
        out.append(text)
        return

    separator = separators[0] if separators else None
    rest = separators[1:]

    if separator is None:
        # Last resort: hard character cut.
        for i in range(0, len(text), chunk_size):
            out.append(text[i : i + chunk_size])
        return

    for part in text.split(separator):
        if not part:
            continue
        if len(part) <= chunk_size:
            out.append(part)
        else:
            _natural_split(part, rest, chunk_size, out)


def _pack(pieces: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Greedily merge natural pieces into chunks, carrying overlap forward."""
    chunks: list[str] = []
    current = ""
    separator = "\n\n"

    for piece in pieces:
        candidate = piece if not current else current + separator + piece
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)

        tail = current[-overlap:] if current and overlap else ""
        # Prepend the overlap, but never force a single piece past the limit.
        current = (
            (tail + separator + piece) if (tail and len(tail) + len(piece) <= chunk_size) else piece
        )

    if current:
        chunks.append(current)
    return [c for c in chunks if c.strip()]
