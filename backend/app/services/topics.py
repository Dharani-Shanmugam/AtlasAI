from __future__ import annotations

import json
from dataclasses import dataclass

from app.core.logging import get_logger
from app.services.llm import LLMClient

logger = get_logger(__name__)

_TOPIC_EXTRACTION_PROMPT = """Analyze the following document chunks and extract the main topics.

For each topic, provide:
- A short, descriptive name (2-5 words)
- A 1-2 sentence summary of what this topic covers
- 3-5 keywords that represent this topic
- Which chunk numbers (1-indexed) are relevant to this topic

Return ONLY a JSON array (no markdown, no explanation) in this exact format:
[
  {
    "name": "Topic Name",
    "summary": "Brief description of what this topic covers.",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "chunk_indices": [1, 2, 3]
  }
]

Group related chunks together. Aim for 2-8 topics depending on the content.
If the content is very short or homogeneous, 1-2 topics is fine.

Document chunks:
"""


@dataclass
class TopicData:
    name: str
    summary: str
    keywords: list[str]
    chunk_indices: list[int]


async def extract_topics(chunks: list[str], llm: LLMClient) -> list[TopicData]:
    """Use the LLM to extract topics from document chunks.

    Chunks are numbered 1-indexed in the prompt so the LLM can reference them.
    """
    if not chunks:
        return []

    # Build the numbered chunks for the prompt.
    numbered = "\n".join(f"[{i+1}] {chunk[:1000]}" for i, chunk in enumerate(chunks))
    prompt = _TOPIC_EXTRACTION_PROMPT + numbered

    messages = [
        {"role": "system", "content": "You are a topic extraction assistant. Output valid JSON only."},
        {"role": "user", "content": prompt},
    ]

    full_response = ""
    async for token in llm.stream_chat(messages):
        full_response += token

    # Parse the response.
    topics: list[TopicData] = []
    try:
        # Strip markdown code fences if present.
        clean = full_response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
        if clean.endswith("```"):
            clean = clean.rsplit("```", 1)[0]
        clean = clean.strip()

        data = json.loads(clean)
        if not isinstance(data, list):
            logger.warning("Topic extraction returned non-array: %s", type(data))
            return []

        for item in data:
            if not isinstance(item, dict) or "name" not in item:
                continue
            topics.append(
                TopicData(
                    name=str(item.get("name", "Unnamed")),
                    summary=str(item.get("summary", "")),
                    keywords=list(item.get("keywords", [])),
                    chunk_indices=list(item.get("chunk_indices", [])),
                )
            )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.warning("Failed to parse topic extraction response: %s", exc)
        logger.debug("Raw response: %s", full_response[:500])

    return topics
