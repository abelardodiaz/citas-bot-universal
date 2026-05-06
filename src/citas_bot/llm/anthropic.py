"""Anthropic Claude provider implementation."""

from __future__ import annotations

import anthropic
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from citas_bot.llm.base import (
    ChatResponse,
    LLMAuthError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    Message,
)
from citas_bot.observability import get_logger

log = get_logger(__name__)


class AnthropicProvider:
    """LLMProvider backed by the official `anthropic` SDK."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        if not api_key:
            raise LLMAuthError("Empty ANTHROPIC_API_KEY")
        self._client = anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout_seconds)
        self._model = model
        self._max_retries = max_retries

    async def chat(
        self,
        messages: list[Message],
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> ChatResponse:
        retryer = AsyncRetrying(
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type((LLMRateLimitError, LLMTimeoutError)),
            reraise=True,
        )
        async for attempt in retryer:
            with attempt:
                return await self._chat_once(messages, max_tokens, temperature)
        raise LLMError("retry loop exhausted unexpectedly")  # pragma: no cover

    async def _chat_once(
        self,
        messages: list[Message],
        max_tokens: int | None,
        temperature: float,
    ) -> ChatResponse:
        system, payload = _split_system(messages)
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens or 1024,
                temperature=temperature,
                system=system,
                messages=[{"role": m.role, "content": m.content} for m in payload],
            )
        except anthropic.AuthenticationError as exc:
            raise LLMAuthError(str(exc)) from exc
        except anthropic.RateLimitError as exc:
            raise LLMRateLimitError(str(exc)) from exc
        except anthropic.APITimeoutError as exc:
            raise LLMTimeoutError(str(exc)) from exc
        except anthropic.APIError as exc:
            raise LLMError(str(exc)) from exc

        text_blocks = [block.text for block in response.content if block.type == "text"]
        text = "".join(text_blocks)
        usage = response.usage
        tokens_in = getattr(usage, "input_tokens", 0)
        tokens_out = getattr(usage, "output_tokens", 0)

        log.info(
            "llm_chat",
            provider="anthropic",
            model=self._model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )
        return ChatResponse(
            text=text,
            model=self._model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            raw=response.model_dump() if hasattr(response, "model_dump") else {},
        )


def _split_system(messages: list[Message]) -> tuple[str, list[Message]]:
    """Anthropic API takes system prompt as a top-level field, not in messages."""

    system_parts = [m.content for m in messages if m.role == "system"]
    rest = [m for m in messages if m.role != "system"]
    return "\n\n".join(system_parts), rest
