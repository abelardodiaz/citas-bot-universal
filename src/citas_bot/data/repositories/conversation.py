"""ConversationRepository: queries scoped to the Conversation aggregate."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from citas_bot.domain import Conversation
from citas_bot.domain.base import utc_now


class ConversationRepository:
    """Read/write operations for Conversation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(self, customer_id: str) -> Conversation | None:
        """Return the most recent conversation for the customer, if any."""

        stmt = (
            select(Conversation)
            .where(Conversation.customer_id == customer_id)
            .order_by(Conversation.last_message_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, customer_id: str) -> Conversation:
        existing = await self.get_active(customer_id)
        if existing is not None:
            return existing
        conv = Conversation(customer_id=customer_id, slots_filled={})
        self._session.add(conv)
        await self._session.flush()
        return conv

    async def update_state(
        self,
        conversation: Conversation,
        intent: str | None = None,
        slots: dict[str, Any] | None = None,
    ) -> Conversation:
        if intent is not None:
            conversation.current_intent = intent
        if slots is not None:
            conversation.slots_filled = slots
        conversation.last_message_at = utc_now()
        await self._session.flush()
        return conversation

    async def clear(self, conversation: Conversation) -> Conversation:
        conversation.current_intent = None
        conversation.slots_filled = {}
        conversation.last_message_at = utc_now()
        await self._session.flush()
        return conversation
