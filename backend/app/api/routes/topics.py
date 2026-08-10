from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_embeddings, get_llm, get_vector_store
from app.core.logging import get_logger
from app.models.db import get_db
from app.models.entities import Document, Topic
from app.schemas.api import TopicMap, TopicOut
from app.services.topics import extract_topics

logger = get_logger(__name__)

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.post("/extract/{doc_id}", response_model=TopicMap, status_code=201)
async def extract_document_topics(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    embeddings=Depends(get_embeddings),
    vector_store=Depends(get_vector_store),
    llm=Depends(get_llm),
) -> TopicMap:
    """Extract topics from a document's chunks using the LLM."""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.status != "ready":
        raise HTTPException(status_code=422, detail="Document is not ready for topic extraction.")

    # Retrieve all chunks for this document from the vector store.
    # We embed a generic query to get everything.
    all_chunks = vector_store.search(
        embeddings.embed_query("main content and topics discussed")[0],
        top_k=100,
        doc_id=doc_id,
    )
    chunk_texts = [c.text for c in all_chunks]

    if not chunk_texts:
        raise HTTPException(status_code=422, detail="No chunks found for this document.")

    # Extract topics via LLM.
    topic_data = await extract_topics(chunk_texts, llm)

    # Delete any existing topics for this doc and replace.
    existing = await db.execute(select(Topic).where(Topic.doc_id == doc_id))
    for old in existing.scalars().all():
        await db.delete(old)

    # Persist the new topics.
    topics: list[Topic] = []
    for td in topic_data:
        topic = Topic(
            doc_id=doc_id,
            name=td.name,
            summary=td.summary,
            keywords_json=json.dumps(td.keywords),
            chunk_indices_json=json.dumps(td.chunk_indices),
        )
        db.add(topic)
        topics.append(topic)

    await db.commit()
    for t in topics:
        await db.refresh(t)

    return TopicMap(
        topics=[_to_out(t) for t in topics],
        total=len(topics),
    )


@router.get("", response_model=TopicMap)
async def list_topics(
    doc_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> TopicMap:
    """List all topics, optionally filtered by document ID."""
    query = select(Topic).order_by(Topic.created_at.desc())
    if doc_id:
        query = query.where(Topic.doc_id == doc_id)
    result = await db.execute(query)
    topics = result.scalars().all()
    return TopicMap(
        topics=[_to_out(t) for t in topics],
        total=len(topics),
    )


@router.delete("/{topic_id}", status_code=204)
async def delete_topic(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")
    await db.delete(topic)
    await db.commit()


def _to_out(t: Topic) -> TopicOut:
    keywords: list[str] = []
    chunk_indices: list[int] = []
    if t.keywords_json:
        try:
            keywords = json.loads(t.keywords_json)
        except (json.JSONDecodeError, TypeError):
            pass
    if t.chunk_indices_json:
        try:
            chunk_indices = json.loads(t.chunk_indices_json)
        except (json.JSONDecodeError, TypeError):
            pass
    return TopicOut(
        id=t.id,
        doc_id=t.doc_id,
        name=t.name,
        summary=t.summary,
        keywords=keywords,
        chunk_indices=chunk_indices,
        created_at=t.created_at,
    )
