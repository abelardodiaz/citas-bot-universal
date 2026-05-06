"""AnthropicProvider tests with the SDK stubbed out."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import anthropic
import pytest

from citas_bot.llm import LLMAuthError, LLMRateLimitError, LLMTimeoutError, Message
from citas_bot.llm.anthropic import AnthropicProvider, _split_system


def _make_response(text: str = "hola") -> Any:
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    response.usage = MagicMock(input_tokens=10, output_tokens=4)
    response.model_dump = MagicMock(return_value={"text": text})
    return response


def test_constructor_rejects_empty_key() -> None:
    with pytest.raises(LLMAuthError):
        AnthropicProvider(api_key="")


def test_split_system_separates_system_messages() -> None:
    messages = [
        Message(role="system", content="You are X"),
        Message(role="user", content="Hi"),
        Message(role="assistant", content="Hello"),
    ]
    system, rest = _split_system(messages)
    assert system == "You are X"
    assert [m.role for m in rest] == ["user", "assistant"]


@pytest.mark.asyncio
async def test_chat_returns_response_with_token_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = AnthropicProvider(api_key="sk-test", model="claude-sonnet-4-6")
    create_mock = AsyncMock(return_value=_make_response("hello"))
    monkeypatch.setattr(provider._client.messages, "create", create_mock)

    result = await provider.chat([Message(role="user", content="hi")])

    assert result.text == "hello"
    assert result.tokens_in == 10
    assert result.tokens_out == 4
    assert result.model == "claude-sonnet-4-6"
    create_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_chat_maps_authentication_error(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = AnthropicProvider(api_key="sk-test", max_retries=1)
    err = anthropic.AuthenticationError(
        message="bad key", response=MagicMock(status_code=401), body=None
    )
    monkeypatch.setattr(provider._client.messages, "create", AsyncMock(side_effect=err))

    with pytest.raises(LLMAuthError):
        await provider.chat([Message(role="user", content="hi")])


@pytest.mark.asyncio
async def test_chat_retries_on_rate_limit_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = AnthropicProvider(api_key="sk-test", max_retries=3)
    rate_err = anthropic.RateLimitError(
        message="too fast", response=MagicMock(status_code=429), body=None
    )
    create_mock = AsyncMock(side_effect=[rate_err, _make_response("ok")])
    monkeypatch.setattr(provider._client.messages, "create", create_mock)

    result = await provider.chat([Message(role="user", content="hi")])

    assert result.text == "ok"
    assert create_mock.await_count == 2


@pytest.mark.asyncio
async def test_chat_raises_after_retries_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = AnthropicProvider(api_key="sk-test", max_retries=2)
    err = anthropic.APITimeoutError(request=MagicMock())
    monkeypatch.setattr(provider._client.messages, "create", AsyncMock(side_effect=err))

    with pytest.raises(LLMTimeoutError):
        await provider.chat([Message(role="user", content="hi")])
