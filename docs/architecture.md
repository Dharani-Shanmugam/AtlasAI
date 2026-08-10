# AtlasAI architecture

A short walkthrough of every moving part and *why* it exists.

## The pipeline

```
 upload ──► extract text ──► chunk ──► embed ──► vector store
                                                        ▲
 question ──► embed query ──► retrieve top-k ───────────┘
                                                        │
                          context + history ──► LLM ────┘
                                                        │
                          streamed answer + citations ──► UI
```

## Backend services

### `app/services/ingestion/`
- **`loaders.py`** — turns raw bytes into plain text. PDFs go through `pypdf`;
  markdown/text are decoded directly. Kept behind one function so adding a new
  format (DOCX, HTML…) is a 10-line change.
- **`chunking.py`** — recursive splitting: paragraphs → lines → sentences →
  hard cuts, then greedy packing with overlap. Splitting on natural boundaries
  keeps the semantics of each chunk intact, which is what makes retrieval work.
- **`pipeline.py`** — orchestrates load → chunk → embed → index, and records
  status (`pending → ready | failed`) on the `Document` row. CPU-heavy work
  (embedding) is pushed to a worker thread so the API stays responsive.

### `app/services/embeddings.py`
Turns text into dense vectors. `FastEmbedProvider` runs locally via ONNX
(BAAI/bge-small-en-v1.5, 384 dims) — free, private, no key. bge models get the
recommended "Represent this sentence…" query prefix, which measurably improves
retrieval. The model downloads once on first use, then loads from cache.

### `app/services/vector_store.py`
`ChromaStore` persists chunks + vectors to `data/chroma`. Each chunk stores
metadata (`doc_id`, `filename`, `chunk_index`) so results carry enough context
for citations. `InMemoryStore` implements the same `VectorStore` contract and is
used by tests — it doubles as a reference implementation.

### `app/services/retrieval.py`
The query vector is compared against all chunk vectors (cosine similarity) and
the top-k nearest are returned. `build_context` numbers them `[1]…[n]` and
`build_sources` maps those numbers back to file/chunk for the UI.

### `app/services/llm.py`
`LLMClient` wraps an **OpenAI-compatible** chat-completions endpoint — that's
exactly what Groq exposes. Swap providers by changing `GROQ_BASE_URL` /
`GROQ_MODEL` (Ollama, Together, vLLM all work). The system prompt enforces
grounding: answer only from context, cite with `[n]`, admit when the answer
isn't in the documents.

### `app/services/rag.py`
The RAG orchestrator:
1. persists the user question,
2. embeds it and retrieves top-k chunks,
3. builds messages (system + last few turns of history + question),
4. streams tokens and persists the final answer with its citations.

## API surface

| Endpoint | Purpose |
|---|---|
| `POST /api/documents/upload` | Upload + index a file (returns doc + chunk count) |
| `GET /api/documents` | List documents |
| `DELETE /api/documents/{id}` | Remove from DB **and** vector store |
| `POST /api/chat` | SSE stream: `meta` → `token`* → `done` |
| `GET /api/sessions` / `…/messages` | History |

## Frontend (Next.js App Router)

- `/chat` — streaming messages, live cursor, expandable citations, session
  sidebar (all animated with framer-motion).
- `/documents` — drag-and-drop upload zone, document cards with status and
  chunk counts.
- `lib/api.ts` — typed client + SSE parser; `lib/types.ts` — shared contracts.

## Data model

`documents` (uploaded files + ingest status) · `chat_sessions` · `chat_messages`
(role, content, `sources_json` with the citations that grounded the answer).
SQLite by default; swap `DATABASE_URL` for Postgres and it just works.

## Common questions

**Why Chroma and not a cloud vector DB?** Zero setup for learning, and the
`VectorStore` interface means swapping to Qdrant/pgvector is contained.

**Why local embeddings?** Groq has no embedding endpoint, so we keep indexing
free and private — and it demonstrates a mixed provider setup, which is common
in production.
