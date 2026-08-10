from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── URL ingestion ──────────────────────────────────────────────
class URLIngestRequest(BaseModel):
    url: str = Field(min_length=5, max_length=2000)


# ── Documents ──────────────────────────────────────────────────
class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    content_type: str
    file_size: int
    status: str
    error: str | None = None
    chunk_count: int
    created_at: datetime


class DocumentList(BaseModel):
    documents: list[DocumentOut]
    total: int


# ── Batch upload ───────────────────────────────────────────────
class BatchUploadResult(BaseModel):
    total: int
    succeeded: int
    failed: int
    documents: list[DocumentOut]


# ── Topics ─────────────────────────────────────────────────────
class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    doc_id: str
    name: str
    summary: str
    keywords: list[str] = Field(default_factory=list)
    chunk_indices: list[int] = Field(default_factory=list)
    created_at: datetime


class TopicMap(BaseModel):
    topics: list[TopicOut]
    total: int


# ── Chat ───────────────────────────────────────────────────────
class SourceRef(BaseModel):
    """One retrieved chunk cited by the answer."""

    number: int
    text: str
    filename: str
    doc_id: str
    chunk_index: int


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    sources: list[SourceRef] = Field(default_factory=list)
    created_at: datetime


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None