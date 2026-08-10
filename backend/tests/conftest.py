from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Set test environment BEFORE any app module imports (settings are cached).
# A fresh temp dir per run keeps the SQLite DB and Chroma data isolated.
_TMP = Path(tempfile.mkdtemp(prefix="atlas-test-"))
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_TMP / 'test.db'}")
os.environ.setdefault("DATA_DIR", str(_TMP))
os.environ.setdefault("GROQ_API_KEY", "test-key")  # required to build LLMClient
os.environ.setdefault("GROQ_MODEL", "test-model")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services.embeddings import FakeEmbeddingsProvider  # noqa: E402
from app.services.vector_store import InMemoryStore  # noqa: E402


class FakeLLM:
    """Deterministic streaming model used in tests."""

    def __init__(self, tokens: list[str] | None = None) -> None:
        self.tokens = tokens or ["This is a ", "grounded answer ", "citing [1]."]
        self.last_messages: list[dict[str, str]] | None = None

    @classmethod
    def build_messages(cls, context, history, question):
        from app.services.llm import LLMClient

        return LLMClient.build_messages(context, history, question)

    async def stream_chat(self, messages):
        self.last_messages = messages
        for token in self.tokens:
            yield token


@pytest.fixture
def embeddings():
    return FakeEmbeddingsProvider()


@pytest.fixture
def vector_store():
    return InMemoryStore()


@pytest.fixture
def llm():
    return FakeLLM()


@pytest.fixture
def client(embeddings, vector_store, llm):
    app.dependency_overrides.clear()
    from app.api import deps

    app.dependency_overrides[deps.get_embeddings] = lambda: embeddings
    app.dependency_overrides[deps.get_vector_store] = lambda: vector_store
    app.dependency_overrides[deps.get_llm] = lambda: llm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
