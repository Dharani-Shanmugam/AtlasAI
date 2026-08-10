from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import get_logger
from app.services.embeddings import FastEmbedProvider
from app.services.llm import LLMClient, LLMError
from app.services.vector_store import ChromaStore

logger = get_logger(__name__)


@lru_cache
def get_embeddings() -> FastEmbedProvider:
    return FastEmbedProvider(model_name=settings.embedding_model)


@lru_cache
def get_vector_store() -> ChromaStore:
    return ChromaStore()


def get_top_k() -> int:
    return settings.retrieval_top_k


def get_llm() -> LLMClient:
    try:
        return LLMClient()
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
