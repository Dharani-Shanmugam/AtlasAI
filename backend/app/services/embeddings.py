from __future__ import annotations

import logging
from contextlib import suppress
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)

# For "bge" models the embedding quality for retrieval improves if queries
# carry this instruction prefix. Documents are embedded as-is.
_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class EmbeddingsProvider(Protocol):
    """Anything that turns text into dense vectors."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[list[float]]: ...
    @property
    def dimension(self) -> int: ...


class FastEmbedProvider:
    def __init__(self, model_name: str = settings.embedding_model) -> None:
        self.model_name = model_name
        self._model = None
        self._dimension = 384

    def _ensure_model(self):
        if self._model is None:
            from fastembed import TextEmbedding

            logger.info("Loading embedding model %s (first call downloads it)...", self.model_name)
            self._model = TextEmbedding(model_name=self.model_name)
            with suppress(Exception):
                self._dimension = (
                    self._model.model.get_sentence_embedding_dimension()  # type: ignore[attr-defined]
                )
        return self._model

    @staticmethod
    def _to_floats(vecs) -> list[list[float]]:
        return [[float(x) for x in v] for v in vecs]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        model = self._ensure_model()
        return self._to_floats(model.embed(texts, batch_size=32))

    def embed_query(self, text: str) -> list[list[float]]:
        model = self._ensure_model()
        query = text if "bge" not in self.model_name.lower() else _BGE_QUERY_PREFIX + text
        return self._to_floats(model.embed([query]))

    @property
    def dimension(self) -> int:
        return self._dimension


class FakeEmbeddingsProvider:
    """Deterministic embeddings for tests — no model download, no network."""

    def __init__(self, dimension: int = 8) -> None:
        self._dimension = dimension

    @staticmethod
    def _hash(text: str, seed: int, dimension: int) -> list[float]:
        out: list[float] = []
        for _ in range(dimension):
            value = 0.0
            for ch in text:
                value = (value * 31 + ord(ch)) % 9973
            value = (value + seed * 7919) % 100000 / 100000.0
            out.append(value)
        return out

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._hash(t, 1, self._dimension) for t in texts]

    def embed_query(self, text: str) -> list[list[float]]:
        return [self._hash(text, 1, self._dimension)]

    @property
    def dimension(self) -> int:
        return self._dimension
