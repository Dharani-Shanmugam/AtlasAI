# AtlasAI

Upload documents → ask questions → get **grounded, cited, streaming answers**.

A production-grade RAG (Retrieval-Augmented Generation) knowledge assistant,
built to be simple enough to fully understand and polished enough to actually
use — the canonical project for learning how real AI systems are engineered.

## How it works

```
upload ──► extract text ──► chunk ──► embed (local) ──► vector store (Chroma)
                                                              ▲
question ──► embed query ──► retrieve top-k ──────────────────┘
                                                              │
                          context + history ──► Groq LLM ─────┘
                                                              │
                             streamed answer + citations ──► UI
```

- **Chunking** — recursive splitting on natural boundaries + overlap, so no
  idea is lost at a cut.
- **Embeddings** — fully local (fastembed/ONNX, `bge-small`), free and private.
- **Retrieval** — cosine top-k over a persistent ChromaDB.
- **Generation** — Groq's blazing-fast OpenAI-compatible API, streamed over SSE.
- **Grounding** — the prompt only answers from retrieved context and cites
  `[1]…[n]`, mapped back to clickable sources in the UI.

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11+ · FastAPI · SQLAlchemy · ChromaDB · fastembed · Groq |
| Frontend | Next.js 15 · React 19 · Tailwind · framer-motion |
| Ops | Docker Compose · GitHub Actions (lint + tests + build) |

## Quick start

**Prereqs:** Docker, or Python 3.11+ / Node 20+. You need a free
[Groq API key](https://console.groq.com/keys) (used only for answers — indexing
is local).

```bash
git clone <this-repo> atlas && cd atlas

# configure keys (copy from backend/.env.example)
cp backend/.env.example backend/.env
# → set GROQ_API_KEY=...

# run everything
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

**Without Docker:**

```bash
# terminal 1 — backend
cd backend
python -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# terminal 2 — frontend
cd frontend
npm install
npm run dev
```

First upload downloads the embedding model once (~130 MB), then it's cached.

## Features

- **Upload docs** — PDF, Markdown, TXT, or paste a URL to scrape
- **Multi-file batch upload** — drag multiple files at once
- **Smart chunking** — recursive splitting with overlap, no content lost
- **Local embeddings** — free, private, no API key needed for indexing
- **Streaming chat** — answers stream in token-by-token with a live cursor
- **Cited sources** — every claim links back to the exact chunk it came from
- **Topic extraction** — auto-generate a topic map from your documents
- **Chat history** — sessions persist across page reloads

## Project layout

```
atlas/
├── backend/
│   ├── app/
│   │   ├── core/        config, logging
│   │   ├── api/         routes + dependencies
│   │   ├── models/      SQLAlchemy models
│   │   ├── schemas/     request/response contracts
│   │   └── services/    ingestion · embeddings · vector store · RAG · topics
│   └── tests/           20 tests (chunking, loaders, retrieval, API)
├── frontend/
│   ├── app/             /chat · /documents · landing
│   ├── components/      animated UI (messages, citations, upload)
│   └── lib/             typed API client + SSE parser
├── docs/                architecture + RAG concepts
└── .github/workflows/   CI
```

## Tests & checks

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest        # 20 tests
.\.venv\Scripts\ruff.exe check app tests    # lint
```
