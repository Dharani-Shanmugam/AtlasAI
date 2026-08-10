from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_embeddings, get_llm, get_vector_store
from app.core.logging import get_logger
from app.models.db import get_db
from app.models.entities import ChatMessage, ChatSession
from app.schemas.api import ChatRequest, MessageOut, SessionOut, SourceRef
from app.services.rag import stream_answer

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


def _sse(event: dict) -> str:
    """Serialize an event into a Server-Sent-Events frame."""
    return f"data: {json.dumps(event)}\n\n"


@router.post("/chat")
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    embeddings=Depends(get_embeddings),
    vector_store=Depends(get_vector_store),
    llm=Depends(get_llm),
) -> StreamingResponse:
    async def event_source():
        try:
            async for event in stream_answer(
                question=body.question,
                session_id=body.session_id,
                db=db,
                vector_store=vector_store,
                embeddings=embeddings,
                llm=llm,
            ):
                yield _sse(event)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Stream failed")
            yield _sse({"type": "error", "message": f"Server error: {exc}"})

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)) -> list[SessionOut]:
    result = await db.execute(select(ChatSession).order_by(ChatSession.created_at.desc()))
    return [SessionOut.model_validate(s) for s in result.scalars().all()]


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def session_messages(session_id: str, db: AsyncSession = Depends(get_db)) -> list[MessageOut]:
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages: list[MessageOut] = []
    for m in result.scalars().all():
        sources: list[SourceRef] = []
        if m.sources_json:
            try:
                sources = [SourceRef(**s) for s in json.loads(m.sources_json)]
            except (json.JSONDecodeError, ValidationError):
                logger.warning("Unparseable sources on message %s", m.id)
        messages.append(
            MessageOut(
                id=m.id, role=m.role, content=m.content, sources=sources, created_at=m.created_at
            )
        )
    return messages


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)) -> None:
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    await db.delete(session)
    await db.commit()
