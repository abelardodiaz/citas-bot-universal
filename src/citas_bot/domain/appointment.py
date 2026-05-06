"""Appointment entity: a scheduled service slot for a customer."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from citas_bot.domain.base import Base, IdMixin, TimestampMixin


class AppointmentStatus(StrEnum):
    """Lifecycle states of an Appointment."""

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class Appointment(IdMixin, TimestampMixin, Base):
    """A booking made by a customer for a future date+time.

    ``scheduled_at`` is stored in UTC; the application converts to the
    business timezone at presentation boundaries.
    """

    __tablename__ = "appointments"

    customer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        String(20), default=AppointmentStatus.SCHEDULED, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
