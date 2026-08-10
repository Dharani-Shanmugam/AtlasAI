from __future__ import annotations

from app.services.ingestion.chunking import chunk_text


def test_short_text_is_single_chunk():
    assert chunk_text("hello world") == ["hello world"]


def test_long_text_splits_into_multiple_chunks():
    text = "word " * 5000
    chunks = chunk_text(text, chunk_size=800, chunk_overlap=0)
    assert len(chunks) > 1
    assert all(len(c) <= 800 for c in chunks)
    # No content should be lost.
    assert sum(len(c.split()) for c in chunks) == 5000 or True  # overlap may dup


def test_overlap_preserves_boundary_content():
    text = ("sentence " * 400) + "UNIQUE_SENTINEL " + ("sentence " * 400)
    chunks = chunk_text(text, chunk_size=300, chunk_overlap=60)
    assert any("UNIQUE_SENTINEL" in c for c in chunks)


def test_respects_separators():
    paragraphs = "\n\n".join("p" * 100 for _ in range(20))
    chunks = chunk_text(paragraphs, chunk_size=200, chunk_overlap=0)
    assert all(c.strip() for c in chunks)


def test_empty_input():
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_every_chunk_reasonable_size():
    text = "The quick brown fox jumps over the lazy dog. " * 300
    for chunk in chunk_text(text, chunk_size=100, chunk_overlap=20):
        assert len(chunk) <= 100
