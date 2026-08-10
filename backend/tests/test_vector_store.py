from __future__ import annotations

from app.services.embeddings import FakeEmbeddingsProvider
from app.services.vector_store import Chunk, InMemoryStore


def _doc_entries(doc_id: str, filename: str) -> list[Chunk]:
    return [Chunk(text=f"content about {word}", index=i) for i, word in enumerate(["cows", "cats"])]


def test_upsert_and_search():
    store = InMemoryStore()
    embeddings = FakeEmbeddingsProvider()
    n = store.upsert_document("d1", "animals.txt", _doc_entries("d1", "animals.txt"), embeddings)
    assert n == 2
    assert store.count_chunks("d1") == 2


def test_search_returns_most_similar_first():
    store = InMemoryStore()
    embeddings = FakeEmbeddingsProvider()
    store.upsert_document("d1", "f.txt", _doc_entries("d1", "f.txt"), embeddings)

    results = store.search(embeddings.embed_query("cows")[0], top_k=5)
    assert len(results) == 2
    assert results[0].chunk_index == 0  # "cows" chunk is most similar to "cows"


def test_delete_removes_chunks():
    store = InMemoryStore()
    embeddings = FakeEmbeddingsProvider()
    store.upsert_document("d1", "f.txt", _doc_entries("d1", "f.txt"), embeddings)
    store.delete_document("d1")
    assert store.count_chunks("d1") == 0
    assert store.search(embeddings.embed_query("cows")[0], top_k=5) == []
