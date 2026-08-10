from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.entities import Document
from app.services.ingestion.chunking import chunk_text
from app.services.ingestion.loaders import extract_text
from app.services.vector_store import Chunk

logger = get_logger(__name__)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


class IngestionError(RuntimeError):
    pass


async def ingest_document(
    doc: Document,
    data: bytes,
    db: AsyncSession,
    vector_store,
    embeddings,
) -> Document:

    try:
        if len(data) > MAX_UPLOAD_BYTES:
            raise IngestionError("File exceeds the 25 MB upload limit.")

        extracted = extract_text(doc.filename, data)
        if not extracted.text.strip():
            raise IngestionError("No readable text found in this file.")

        chunks = chunk_text(
            extracted.text,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        if not chunks:
            raise IngestionError("The document produced no usable chunks.")

        chunk_objs = [Chunk(text=c, index=i) for i, c in enumerate(chunks)]

        count = await asyncio.to_thread(
            vector_store.upsert_document,
            doc.id,
            doc.filename,
            chunk_objs,
            embeddings,
        )

        doc.content_type = extracted.content_type
        doc.file_size = len(data)
        doc.chunk_count = count
        doc.status = "ready"
        doc.error = None
        logger.info("Indexed %s: %d chunks", doc.filename, count)
    except Exception as exc:  # noqa: BLE001
        doc.status = "failed"
        doc.error = str(exc)
        logger.warning("Ingestion failed for %s: %s", doc.filename, exc)
    finally:
        await db.commit()
        await db.refresh(doc)
    return doc
