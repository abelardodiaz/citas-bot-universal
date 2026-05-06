"""Factory that maps Settings -> concrete LLMProvider.

Fails fast at startup when configuration is incomplete or asks for a provider
that this milestone does not support yet.
"""

from __future__ import annotations

from citas_bot.config import Settings
from citas_bot.llm.anthropic import AnthropicProvider
from citas_bot.llm.base import LLMAuthError, LLMProvider


def get_llm_provider(settings: Settings) -> LLMProvider:
    """Return a ready-to-use provider based on the configured backend.

    Raises:
        LLMAuthError: when the backend is supported but the API key is missing.
        NotImplementedError: when LLM_PROVIDER points to a backend planned for
            a future release.
    """

    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise LLMAuthError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
            )
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )

    if settings.llm_provider == "deepseek":
        raise NotImplementedError(
            "DeepSeek provider is planned for v0.2.0+. Use LLM_PROVIDER=anthropic for now."
        )

    raise NotImplementedError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")
