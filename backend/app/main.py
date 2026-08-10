from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.deps import get_embeddings  # noqa: F401  (lazily initialized)
from app.api.routes import chat, documents, health, topics
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.models.db import init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.debug)
    logger.info("Starting %s (%s)", settings.app_name, settings.app_env)

    # Make sure the DB and data directories exist.
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    await init_db()

    # NOTE: embeddings load lazily on first use (the local model downloads
    # once), so startup stays instant.
    logger.info(
        "LLM: %s | embeddings: %s",
        settings.groq_model if settings.is_llm_configured else "not configured",
        settings.embedding_model,
    )
    yield


app = FastAPI(
    title="AtlasAI API",
    version="0.1.0",
    description="Upload documents, then ask grounded questions with citations.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(topics.router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")
