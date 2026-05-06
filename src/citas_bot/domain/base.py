"""Declarative base + helpers shared by every model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Timezone-aware UTC timestamp factory."""

    return datetime.now(UTC)


def new_uuid() -> str:
    """Generate a UUID v4 as 36-char string."""

    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Project-wide SQLAlchemy declarative base."""


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` columns to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class IdMixin:
    """Adds a UUID primary key as 36-char string."""

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
