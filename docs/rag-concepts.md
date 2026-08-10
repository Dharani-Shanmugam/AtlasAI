# RAG in 5 minutes

## The problem

LLMs know the world up to their training cutoff — but they don't know *your*
documents. Retraining is absurdly expensive and slow.

## The idea

**RAG = Retrieval + Generation.** Instead of retraining, we:

1. **Index** your documents into searchable chunks (chunk → embed → store).
2. **Retrieve** the few chunks most relevant to a question.
3. **Generate** an answer using *only* those chunks as context.

The model never "learns" your data — it just gets the right context handed to
it for each question. That's what makes answers grounded and up-to-date.

## Why each step matters

| Step | Why |
|---|---|
| **Chunk** | Embedding models have token limits, and mixed-topic chunks dilute the vector so retrieval misses. |
| **Overlap** | Stops ideas that straddle a boundary from being cut in half and lost. |
| **Embed** | Converts text into a vector where "similar meaning" ⟺ "nearby in space". |
| **Retrieve** | Cosine similarity finds the top-k chunks closest to the question. |
| **Cite** | The `[n]` tags in the prompt become clickable sources — transparency, and a free hallucination check. |

## Grounding is the contract

The system prompt enforces three rules: answer only from context, cite numbers,
and **admit when the answer isn't in the documents**. That last rule is what
kills hallucinations — the model says "I couldn't find this" instead of
inventing facts.

## Follow-ups

History (the last few turns) is injected into the prompt, so "and what about
X?" works naturally without re-asking the full question.

## Next steps

Read [architecture.md](architecture.md) to see exactly where each concept lives
in the code, then break something on purpose and watch the eval change.
