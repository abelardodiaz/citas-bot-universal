"""Outbound message sender abstraction."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from citas_bot.intents.base import Reply
from citas_bot.observability import get_logger

log = get_logger(__name__)


@runtime_checkable
class MessageSender(Protocol):
    """Send a Reply to a customer's WhatsApp number."""

    async def send(self, to: str, reply: Reply) -> None: ...


class LogOnlySender:
    """No-op sender that just logs what would be sent.

    Used in M05 (and tests). Replaced by a real Meta Send API client in M07.
    """

    async def send(self, to: str, reply: Reply) -> None:
        log.info("would_send", to=to, type=reply.type, text=reply.text)
