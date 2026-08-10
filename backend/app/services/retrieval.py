from __future__ import annotations

from dataclasses import dataclass

from app.services.vector_store import RetrievedChunk


@dataclass
class RetrievalResult:
    query: str
    chunks: list[RetrievedChunk]

    @property
    def has_results(self) -> bool:
        return bool(self.chunks)


def build_context(chunks: list[RetrievedChunk], max_chars: int = 16_000) -> str:
    """Turn retrieved chunks into the numbered context block used in the prompt.

    Each chunk gets a ``[n]`` tag. The LLM is instructed to answer only from
    this context and to cite numbers, which we map back to sources for the UI.
    """
    parts: list[str] = []
    total = 0
    for i, chunk in enumerate(chunks, start=1):
        part = f"[{i}] (from {chunk.filename}) {chunk.text}"
        if total + len(part) > max_chars:
            break
        parts.append(part)
        total += len(part)
    return "\n\n".join(parts)


def build_sources(chunks: list[RetrievedChunk]) -> list[dict]:
    """Convert retrieved chunks into citation payloads sent to the frontend."""
    return [
        {
            "number": i,
            "text": c.text,
            "filename": c.filename,
            "doc_id": c.doc_id,
            "chunk_index": c.chunk_index,
        }
        for i, c in enumerate(chunks, start=1)
    ]
