"""Factory validation: fail-fast on missing keys and unsupported providers."""

import pytest

from citas_bot.config import Settings
from citas_bot.llm import LLMAuthError, get_llm_provider


def test_factory_returns_anthropic_when_configured() -> None:
    settings = Settings(anthropic_api_key="sk-test", llm_provider="anthropic")
    provider = get_llm_provider(settings)
    assert provider is not None


def test_factory_raises_when_anthropic_key_missing() -> None:
    settings = Settings(anthropic_api_key="", llm_provider="anthropic")
    with pytest.raises(LLMAuthError):
        get_llm_provider(settings)


def test_factory_raises_not_implemented_for_deepseek() -> None:
    settings = Settings(llm_provider="deepseek", deepseek_api_key="sk-test")
    with pytest.raises(NotImplementedError, match="DeepSeek"):
        get_llm_provider(settings)
