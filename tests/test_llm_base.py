"""Sanity tests for base types: dataclass immutability and error hierarchy."""

import pytest

from citas_bot.llm import (
    ChatResponse,
    LLMAuthError,
    LLMError,
    LLMProvider,
    LLMRateLimitError,
    LLMTimeoutError,
    Message,
)


def test_message_is_frozen() -> None:
    msg = Message(role="user", content="hi")
    with pytest.raises((AttributeError, Exception)):
        msg.role = "system"  # type: ignore[misc]


def test_chat_response_holds_token_counts() -> None:
    resp = ChatResponse(
        text="ok",
        model="claude-sonnet-4-6",
        tokens_in=10,
        tokens_out=2,
    )
    assert resp.text == "ok"
    assert resp.tokens_in + resp.tokens_out == 12
    assert resp.raw == {}


def test_error_hierarchy() -> None:
    assert issubclass(LLMAuthError, LLMError)
    assert issubclass(LLMRateLimitError, LLMError)
    assert issubclass(LLMTimeoutError, LLMError)


def test_protocol_runtime_checkable() -> None:
    class Dummy:
        async def chat(
            self, messages: list[Message], max_tokens: int | None = None, temperature: float = 0.7
        ) -> ChatResponse:
            return ChatResponse(text="x", model="m", tokens_in=0, tokens_out=0)

    assert isinstance(Dummy(), LLMProvider)
