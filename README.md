<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Next.js-15-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Groq-LLM-FF6B35?style=for-the-badge&logo=groq&logoColor=white" alt="Groq">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License">
</p>

<h1 align="center">AtlasAI</h1>

<p align="center">
  <strong>Upload documents → Ask questions → Get grounded, cited, streaming answers</strong>
</p>

<p align="center">
  A production-grade RAG (Retrieval-Augmented Generation) knowledge assistant.<br>
  Simple enough to learn from. Polished enough to actually use.
</p>

---

## What is AtlasAI?

AtlasAI turns your documents into a searchable knowledge base. Upload a PDF, Markdown file, or paste a URL — it gets chunked, embedded, and indexed. Then ask any question and get a streaming answer with clickable citations back to the exact source.

**No hallucinations. No guesswork. Every answer is grounded in your files.**

## How It Works

```
                    ┌──────────────────────────────────────────────────┐
                    │                  ATLASAI PIPELINE                │
                    └──────────────────────────────────────────────────┘

    INGESTION                              RETRIEVAL
    ────────                               ─────────
    Upload                                 Embed Query
       ↓                                      ↓
    Extract Text                           Vector Search
       ↓                                      ↓
    Smart Chunking                         Top-K Chunks
       ↓                                      ↓
    Local Embedding                        Context [1] [2] ...
       ↓                                      ↓
    ChromaDB Store ──────────────────►   Groq LLM (streaming)
                                            ↓
                                         Answer + Citations
                                            ↓
                                         Streaming UI
```

## Features

| Feature | Description |
|---|---|
| **Multi-format Upload** | PDF, Markdown, plain text, or paste any URL |
| **Batch Upload** | Drag multiple files at once, processed concurrently |
| **Smart Chunking** | Recursive splitting on natural boundaries with overlap |
| **Local Embeddings** | Free, private — runs on CPU via fastembed (ONNX) |
| **Streaming Chat** | Answers stream token-by-token with a live cursor |
| **Cited Sources** | Every claim links back to the exact chunk it came from |
| **Topic Extraction** | LLM auto-generates a topic map from your documents |
| **Chat History** | Sessions persist across page reloads |
| **URL Scraping** | Paste any URL — fetches and indexes the page content |

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+ · FastAPI · SQLAlchemy · ChromaDB · fastembed |
| **LLM** | Groq (OpenAI-compatible API) · Llama 3.3 70B |
| **Frontend** | Next.js 15 · React 19 · Tailwind CSS · framer-motion |
| **Infra** | Docker Compose · GitHub Actions CI |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- A free [Groq API key](https://console.groq.com/keys) (used only for answers — indexing is fully local)

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/Dharani-Shanmugam/AtlasAI.git
cd AtlasAI

# Configure your Groq API key
cp backend/.env.example backend/.env
# Edit backend/.env and set GROQ_API_KEY=your-key-here

# Start everything
docker compose up --build
```

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

### Option 2: Local Development

```bash
# ── Backend (Terminal 1) ──
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ── Frontend (Terminal 2) ──
cd frontend
npm install
npm run dev
```

> First upload downloads the embedding model (~130 MB). It's cached after that.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Your Groq API key (required) |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | LLM endpoint |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Model to use |
| `LLM_TEMPERATURE` | `0.0` | Generation temperature |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Local embedding model |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/atlas.db` | Database connection |
| `RETRIEVAL_TOP_K` | `5` | Number of chunks to retrieve |
| `CHUNK_SIZE` | `800` | Characters per chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between chunks |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed origins |

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check + stats |
| `/api/documents` | GET | List all documents |
| `/api/documents/upload` | POST | Upload a single file |
| `/api/documents/batch-upload` | POST | Upload multiple files |
| `/api/documents/ingest-url` | POST | Scrape and ingest a URL |
| `/api/documents/{id}` | DELETE | Remove a document |
| `/api/chat` | POST | Stream a chat response (SSE) |
| `/api/sessions` | GET | List chat sessions |
| `/api/topics` | GET | List extracted topics |
| `/api/topics/extract/{doc_id}` | POST | Extract topics from a document |

## Project Structure

```
AtlasAI/
├── backend/
│   ├── app/
│   │   ├── core/           Config, logging
│   │   ├── api/            Routes + dependency injection
│   │   ├── models/         SQLAlchemy models (Document, Session, Message, Topic)
│   │   ├── schemas/        Pydantic request/response contracts
│   │   └── services/
│   │       ├── ingestion/  Loaders, chunking, pipeline, URL scraper
│   │       ├── embeddings  Local embedding provider (fastembed)
│   │       ├── vector_store ChromaDB interface
│   │       ├── retrieval   Context builder
│   │       ├── llm         Groq/OpenAI-compatible client
│   │       ├── rag         Orchestrator (retrieve → generate → persist)
│   │       └── topics      LLM topic extraction
│   └── tests/              20 tests (all green)
├── frontend/
│   ├── app/                Pages: /chat, /documents, landing
│   ├── components/         Animated UI components
│   └── lib/                Typed API client + SSE parser
├── docs/                   Architecture + RAG concepts
├── docker-compose.yml      One-command deployment
└── .github/workflows/      CI (lint + test + build)
```

## Running Tests

```bash
cd backend
python -m pytest -q          # 20 tests
ruff check app tests         # lint
```

## Learning Path

1. **[RAG Concepts](docs/rag-concepts.md)** — What retrieval-augmented generation is and why it exists
2. **[Architecture](docs/architecture.md)** — How each service works and why it's designed that way
3. **Break it** — Change `chunk_size`, swap the embedding model, point `GROQ_BASE_URL` at a local Ollama server

## License

Built with by Dharani Shanmugam
