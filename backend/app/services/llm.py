from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a helpful research assistant with access to the user's uploaded documents.

Your job is to answer questions using the provided context. Follow these rules:

1. Use the context to answer. The context contains numbered sections [1], [2], etc.
   Reference them with citations like [1] when you use information from them.
2. If the context contains relevant information, use it to give a clear, complete answer.
   You CAN synthesize and combine information from multiple chunks to form a complete answer.
3. If the context is completely unrelated to the question, say:
   "Based on the uploaded documents, I don't have information about this topic."
4. If the context has partial information, answer what you can and note what's missing.
5. Answer in the same language as the question.
6. Be helpful, direct, and thorough. Use short paragraphs or bullets when helpful.
"""


class LLMError(RuntimeError):
    pass


class LLMClient:
    """Thin wrapper around an OpenAI-compatible chat-completions endpoint.

    Groq exposes a drop-in OpenAI API, so ``AsyncOpenAI(base_url=groq)`` works.
    Swap in any OpenAI-compatible provider (Ollama, vLLM, Together...) by
    changing ``GROQ_BASE_URL`` and ``GROQ_MODEL``.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        self.api_key = api_key or settings.groq_api_key
        self.base_url = base_url or settings.groq_base_url
        self.model = model or settings.groq_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature

        if not self.api_key:
            raise LLMError(
                "GROQ_API_KEY is not set. Create a free key at "
                "https://console.groq.com/keys and add it to backend/.env"
            )
        self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Stream assistant tokens from the model, one text piece at a time."""
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                stream=True,
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"LLM request failed: {exc}") from exc
    @classmethod
    def build_messages(
        cls,
        context: str,
        history: list[dict[str, str]],
        question: str,
    ) -> list[dict[str, str]]:
        """Assemble the full message list: system + recent history + question."""
        if not context.strip():
            system = (
                _SYSTEM_PROMPT
                + "\n\nNo document context is available for this question. "
                "Answer based on your general knowledge and note that the information "
                "is not from any uploaded documents."
            )
        else:
            system = _SYSTEM_PROMPT + f"\n\n--- Document Context ---\n{context}"

        messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        messages.extend(history[-6:])  # last few turns for follow-up questions
        messages.append({"role": "user", "content": question})
        return messages
