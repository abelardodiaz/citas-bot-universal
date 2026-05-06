"""LLM abstraction layer.

Public surface:

- ``Message``, ``ChatResponse``: data carriers
- ``LLMProvider``: the protocol every concrete provider must satisfy
- ``LLMError`` and subclasses: typed exceptions for retry / error handling
- ``get_llm_provider``: factory that returns a ready-to-use provider
"""

from citas_bot.llm.base import (
    ChatResponse,
    LLMAuthError,
    LLMError,
    LLMProvider,
    LLMRateLimitError,
    LLMTimeoutError,
    Message,
)
from citas_bot.llm.factory import get_llm_provider

__all__ = [
    "ChatResponse",
    "LLMAuthError",
    "LLMError",
    "LLMProvider",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "Message",
    "get_llm_provider",
]
