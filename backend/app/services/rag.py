from __future__ import annotations

import json
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.entities import ChatMessage, ChatSession
from app.schemas.api import SourceRef
from app.services.llm import LLMClient
from app.services.retrieval import build_context, build_sources

logger = get_logger(__name__)


async def stream_answer(
    *,
    question: str,
    session_id: str | None,
    db: AsyncSession,
    vector_store,
    embeddings,
    llm: LLMClient,
    top_k: int = settings.retrieval_top_k,
) -> AsyncIterator[dict]:
    """The full RAG loop, streamed as events.

    Events yielded:
      {"type": "meta", "session_id": ..., "citations": [...]}
      {"type": "token", "content": "..."}
      {"type": "error", "message": "..."}
      {"type": "done", "message_id": ...}
    """
    session = await _get_or_create_session(db, session_id)

    # ── Persist the user's question immediately ──────────────────────
    db.add(ChatMessage(session_id=session.id, role="user", content=question))
    await db.commit()

    # ── 1. Retrieve ──────────────────────────────────────────────────
    chunks: list = []
    try:
        query_vector = embeddings.embed_query(question)[0]
        chunks = vector_store.search(query_vector, top_k=top_k)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Retrieval failed")
        yield {"type": "error", "message": f"Retrieval failed: {exc}"}
        return

    citations = build_sources(chunks)
    yield {"type": "meta", "session_id": session.id, "citations": citations}

    if not chunks:
        context = ""
        history: list[dict[str, str]] = []
    else:
        context = build_context(chunks)
        history = await _load_history(db, session.id)

    messages = llm.build_messages(context, history, question)

    # ── 2. Generate (stream) ─────────────────────────────────────────
    answer_parts: list[str] = []
    error: str | None = None
    try:
        async for token in llm.stream_chat(messages):
            answer_parts.append(token)
            yield {"type": "token", "content": token}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Generation failed")
        error = str(exc)
        yield {"type": "error", "message": error}

    answer = "".join(answer_parts)
    if not answer and not error:
        answer = "(The model returned an empty response.)"
    if error and not answer:
        answer = f"[Error generating answer: {error}]"

    # ── 3. Persist the answer with its citations ─────────────────────
    message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer,
        sources_json=json.dumps([SourceRef(**c).model_dump() for c in citations])
        if citations
        else None,
    )
    db.add(message)
    if session.title == "New chat" and len(question) > 2:
        session.title = question[:60]
    await db.commit()
    await db.refresh(message)

    yield {"type": "done", "message_id": message.id}


async def _get_or_create_session(db: AsyncSession, session_id: str | None) -> ChatSession:
    if session_id:
        result = await db.get(ChatSession, session_id)
        if result:
            return result
    session = ChatSession()
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def _load_history(db: AsyncSession, session_id: str) -> list[dict[str, str]]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages]
