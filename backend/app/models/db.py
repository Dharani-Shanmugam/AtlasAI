from __future__ import annotations

import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _ensure_parent(url: str) -> None:
    """Make sure the sqlite file's parent directory exists before connecting."""
    if url.startswith("sqlite"):
        path = url.rsplit("///", 1)[-1]
        if path and path != ":memory:":
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)


_ensure_parent(settings.database_url)

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create tables if they don't exist. Cheap enough to run at startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields a database session per request."""
    async with SessionFactory() as session:
        yield session
