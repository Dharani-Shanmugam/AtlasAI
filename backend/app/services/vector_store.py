from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings
from app.services.embeddings import EmbeddingsProvider

logger = logging.getLogger(__name__)

_COLLECTION = "atlas_documents"


@dataclass
class Chunk:
    """One piece of a document, ready to be embedded and indexed."""

    text: str
    index: int


@dataclass
class RetrievedChunk:
    """A chunk returned by retrieval, with the metadata needed for citations."""

    text: str
    doc_id: str
    filename: str
    chunk_index: int
    score: float


class VectorStore(Protocol):
    def upsert_document(
        self,
        doc_id: str,
        filename: str,
        chunks: list[Chunk],
        embeddings: EmbeddingsProvider,
    ) -> int: ...
    def delete_document(self, doc_id: str) -> None: ...
    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        doc_id: str | None = None,
    ) -> list[RetrievedChunk]: ...
    def count_chunks(self, doc_id: str) -> int: ...


class ChromaStore:
    """Vector store backed by ChromaDB with a persistent local directory.

    Zero configuration: the DB lives on disk at ``data/chroma`` and survives
    restarts. Embeddings are computed by us and passed in explicitly so the
    provider is fully swappable (local or hosted).
    """

    def __init__(self, persist_dir=None) -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=str(persist_dir or settings.vector_store_dir))
        self._collection = self._client.get_or_create_collection(
            _COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Vector store ready at %s", persist_dir or settings.vector_store_dir)

    def upsert_document(
        self,
        doc_id: str,
        filename: str,
        chunks: list[Chunk],
        embeddings: EmbeddingsProvider,
    ) -> int:
        if not chunks:
            return 0
        vectors = embeddings.embed_documents([c.text for c in chunks])
        self._collection.upsert(
            ids=[f"{doc_id}:{c.index}" for c in chunks],
            embeddings=vectors,
            documents=[c.text for c in chunks],
            metadatas=[
                {"doc_id": doc_id, "filename": filename, "chunk_index": c.index} for c in chunks
            ],
        )
        return len(chunks)

    def delete_document(self, doc_id: str) -> None:
        self._collection.delete(where={"doc_id": doc_id})

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        doc_id: str | None = None,
    ) -> list[RetrievedChunk]:
        where = {"doc_id": doc_id} if doc_id else None
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=max(top_k, 1),
            where=where,
        )
        ids: list[str] = result["ids"][0] if result["ids"] else []
        docs: list[str] = result["documents"][0] if result["documents"] else []
        metas: list[dict] = result["metadatas"][0] if result["metadatas"] else []
        distances: list[float] = result["distances"][0] if result["distances"] else []

        chunks: list[RetrievedChunk] = []
        for i, doc_id_str in enumerate(ids):
            meta = metas[i] or {}
            score = 1.0 - distances[i]  # cosine distance → similarity
            chunks.append(
                RetrievedChunk(
                    text=docs[i],
                    doc_id=str(meta.get("doc_id", doc_id_str)),
                    filename=str(meta.get("filename", "unknown")),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    score=score,
                )
            )
        return chunks

    def count_chunks(self, doc_id: str) -> int:
        try:
            return self._collection.count(where={"doc_id": doc_id})
        except Exception:  # pragma: no cover
            return 0


class InMemoryStore:
    """Naive brute-force store used by tests — deterministic and dependency-free.

    It also serves as a reference implementation of the ``VectorStore`` contract.
    """

    def __init__(self) -> None:
        self._vectors: dict[str, list[float]] = {}
        self._meta: dict[str, dict] = {}

    def upsert_document(
        self,
        doc_id: str,
        filename: str,
        chunks: list[Chunk],
        embeddings: EmbeddingsProvider,
    ) -> int:
        vectors = embeddings.embed_documents([c.text for c in chunks])
        for c, vec in zip(chunks, vectors, strict=True):
            key = f"{doc_id}:{c.index}"
            self._vectors[key] = vec
            self._meta[key] = {
                "doc_id": doc_id,
                "filename": filename,
                "chunk_index": c.index,
                "text": c.text,
            }
        return len(chunks)

    def delete_document(self, doc_id: str) -> None:
        for key in [k for k in self._meta if self._meta[k]["doc_id"] == doc_id]:
            self._vectors.pop(key, None)
            self._meta.pop(key, None)

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        doc_id: str | None = None,
    ) -> list[RetrievedChunk]:
        def cosine(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b, strict=False))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(x * x for x in b) ** 0.5
            return dot / (na * nb) if na and nb else 0.0

        scored: list[RetrievedChunk] = []
        for key, vec in self._vectors.items():
            meta = self._meta[key]
            if doc_id and meta["doc_id"] != doc_id:
                continue
            scored.append(
                RetrievedChunk(
                    text=meta.get("text", ""),
                    doc_id=meta["doc_id"],
                    filename=meta["filename"],
                    chunk_index=meta["chunk_index"],
                    score=cosine(query_embedding, vec),
                )
            )
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]

    def count_chunks(self, doc_id: str) -> int:
        return sum(1 for m in self._meta.values() if m["doc_id"] == doc_id)
