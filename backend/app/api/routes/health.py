from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.db import get_db
from app.models.entities import Document

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "llm_configured": settings.is_llm_configured,
        "llm_model": settings.groq_model,
        "embedding_model": settings.embedding_model,
        "documents": await db.scalar(select(func.count(Document.id))),
    }
