from __future__ import annotations

from app.services.retrieval import build_context, build_sources
from app.services.vector_store import RetrievedChunk


def _chunk(text: str, i: int) -> RetrievedChunk:
    return RetrievedChunk(text=text, doc_id="d1", filename="a.txt", chunk_index=i, score=0.9)


def test_build_context_numbered():
    chunks = [_chunk("first content", 0), _chunk("second content", 1)]
    context = build_context(chunks)
    assert "[1]" in context and "[2]" in context
    assert "a.txt" in context


def test_build_sources_matches_context_numbers():
    chunks = [_chunk("alpha", 0), _chunk("beta", 1)]
    sources = build_sources(chunks)
    assert [s["number"] for s in sources] == [1, 2]
    assert sources[0]["filename"] == "a.txt"
    assert sources[0]["doc_id"] == "d1"
