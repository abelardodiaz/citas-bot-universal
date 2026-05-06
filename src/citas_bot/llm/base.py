"""Provider-agnostic LLM types: messages, response, protocol, errors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Message:
    """A single message in a chat conversation."""

    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """Result of a single chat completion call.

    ``raw`` exposes the provider-specific payload for debugging or analytics.
    Application code should rely on ``text``, ``model``, and the token counters.
    """

    text: str
    model: str
    tokens_in: int
    tokens_out: int
    raw: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """Contract every LLM implementation must satisfy.

    Implementations are async and return a fully assembled ``ChatResponse``.
    Streaming will be added as a separate ``stream`` method in v0.2.0+.
    """

    async def chat(
        self,
        messages: list[Message],
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> ChatResponse: ...


class LLMError(Exception):
    """Base class for all LLM-related failures."""


class LLMAuthError(LLMError):
    """Raised when the API rejects the credentials (401/403)."""


class LLMRateLimitError(LLMError):
    """Raised when the provider returns a rate-limit response (429)."""


class LLMTimeoutError(LLMError):
    """Raised when the request exceeds the configured timeout."""
