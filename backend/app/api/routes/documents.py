from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_embeddings, get_vector_store
from app.core.logging import get_logger
from app.models.db import get_db
from app.models.entities import Document
from app.schemas.api import BatchUploadResult, DocumentList, DocumentOut, URLIngestRequest
from app.services.ingestion.pipeline import ingest_document
from app.services.ingestion.url_loader import fetch_url_content

logger = get_logger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=DocumentList)
async def list_documents(db: AsyncSession = Depends(get_db)) -> DocumentList:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    documents = result.scalars().all()
    return DocumentList(
        documents=[DocumentOut.model_validate(d) for d in documents],
        total=len(documents),
    )


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    embeddings=Depends(get_embeddings),
    vector_store=Depends(get_vector_store),
) -> DocumentOut:
    data = await file.read()

    doc = Document(
        filename=file.filename or "document.txt",
        content_type=file.content_type or "application/octet-stream",
        file_size=len(data),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    try:
        await ingest_document(doc, data, db, vector_store, embeddings)
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error during upload of %s", doc.filename)

    if doc.status == "failed":
        raise HTTPException(status_code=422, detail=doc.error or "Ingestion failed.")
    return DocumentOut.model_validate(doc)


@router.post("/batch-upload", response_model=BatchUploadResult, status_code=201)
async def batch_upload(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    embeddings=Depends(get_embeddings),
    vector_store=Depends(get_vector_store),
) -> BatchUploadResult:
    """Upload multiple files at once. Each file is processed concurrently."""
    if len(files) > 20:
        raise HTTPException(status_code=422, detail="Maximum 20 files per batch upload.")

    results: list[DocumentOut] = []
    succeeded = 0
    failed = 0

    async def _process_one(file: UploadFile):
        nonlocal succeeded, failed
        data = await file.read()
        doc = Document(
            filename=file.filename or "document.txt",
            content_type=file.content_type or "application/octet-stream",
            file_size=len(data),
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        try:
            await ingest_document(doc, data, db, vector_store, embeddings)
        except Exception:  # noqa: BLE001
            logger.exception("Error during batch upload of %s", doc.filename)

        if doc.status == "ready":
            succeeded += 1
        else:
            failed += 1
        results.append(DocumentOut.model_validate(doc))

    # Process files concurrently (limit to 5 at a time to avoid memory issues).
    semaphore = asyncio.Semaphore(5)

    async def _bounded(file: UploadFile):
        async with semaphore:
            await _process_one(file)

    await asyncio.gather(*[_bounded(f) for f in files])

    return BatchUploadResult(
        total=len(files),
        succeeded=succeeded,
        failed=failed,
        documents=sorted(results, key=lambda d: d.filename),
    )


@router.post("/ingest-url", response_model=DocumentOut, status_code=201)
async def ingest_url(
    body: URLIngestRequest,
    db: AsyncSession = Depends(get_db),
    embeddings=Depends(get_embeddings),
    vector_store=Depends(get_vector_store),
) -> DocumentOut:
    """Fetch a web page, extract its text, and ingest it into the knowledge base."""
    try:
        web = await fetch_url_content(body.url)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Failed to fetch URL: {exc}") from exc

    if not web.text.strip():
        raise HTTPException(status_code=422, detail="No readable content found at this URL.")

    doc = Document(
        filename=web.title[:200],
        content_type=web.content_type,
        file_size=len(web.text.encode("utf-8")),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    await ingest_document(doc, web.text.encode("utf-8"), db, vector_store, embeddings)

    if doc.status == "failed":
        raise HTTPException(status_code=422, detail=doc.error or "Ingestion failed.")
    return DocumentOut.model_validate(doc)


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    vector_store=Depends(get_vector_store),
) -> None:
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    vector_store.delete_document(doc_id)
    await db.delete(doc)
    await db.commit()
