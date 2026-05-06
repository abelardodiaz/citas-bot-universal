"""Conversation entity: tracks intent + slot state for a customer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from citas_bot.domain.base import Base, IdMixin, TimestampMixin, utc_now


class Conversation(IdMixin, TimestampMixin, Base):
    """One conversational session with a customer.

    ``current_intent`` is the LLM-classified intent (or None when idle).
    ``slots_filled`` is a JSON-serialised dict of slot name -> value collected
    during the multi-step flow (e.g. {"date": "2026-05-12", "time": "10:00"}).
    """

    __tablename__ = "conversations"

    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    slots_filled: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
