"""Intent shape, handler signature, and value objects."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from citas_bot.config import BusinessInfo
    from citas_bot.domain import Conversation, Customer
    from citas_bot.llm import LLMProvider


ReplyType = Literal["text", "buttons", "list"]


@dataclass(frozen=True, slots=True)
class Reply:
    """Outbound message sent back to the user.

    Only ``text`` is used in M05; other types are scaffolding for M06+.
    """

    text: str
    type: ReplyType = "text"
    options: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class IntentResult:
    """What an intent handler returns to the router."""

    reply: Reply
    new_intent: str | None = None  # None = clear current_intent
    new_slots: dict[str, Any] | None = None  # None = leave unchanged
    clear_state: bool = False  # if True, both intent and slots are reset


@dataclass(frozen=True, slots=True)
class Classification:
    """Result of intent classification (keyword or LLM)."""

    intent_name: str
    confidence: float
    reasoning: str | None = None


@dataclass(frozen=True, slots=True)
class IntentContext:
    """Read-only context handed to handlers."""

    customer: Customer
    conversation: Conversation
    text: str
    business_info: BusinessInfo
    llm: LLMProvider


IntentHandler = Callable[[IntentContext], Awaitable[IntentResult]]


@dataclass(frozen=True, slots=True)
class Intent:
    """Static metadata + handler reference for one intent."""

    name: str
    description: str
    examples: list[str]
    handler: IntentHandler
    keywords: list[str] = field(default_factory=list)
