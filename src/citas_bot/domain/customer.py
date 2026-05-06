"""Customer entity: a WhatsApp user known to the bot."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from citas_bot.domain.base import Base, IdMixin, TimestampMixin


class Customer(IdMixin, TimestampMixin, Base):
    """A person who interacts with the bot via WhatsApp.

    The unique business key is ``whatsapp_number`` (E.164 string).
    """

    __tablename__ = "customers"

    whatsapp_number: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), default="es-MX", nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
