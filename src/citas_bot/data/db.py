"""Async SQLAlchemy engine + session factory + FastAPI dependency."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from citas_bot.config import Settings, get_settings
from citas_bot.domain.base import Base

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return a process-wide AsyncEngine (created on first call)."""

    global _engine
    if _engine is None:
        s = settings or get_settings()
        _engine = create_async_engine(
            s.database_url,
            echo=s.database_echo,
            future=True,
        )
    return _engine


def get_session_maker(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """Return the process-wide AsyncSession factory."""

    global _session_maker
    if _session_maker is None:
        engine = get_engine(settings)
        _session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_maker


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields an AsyncSession scoped to one request.

    Commits on success and rolls back on exception.
    """

    maker = get_session_maker()
    async with maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def reset_engine() -> None:
    """Test helper: drop the cached engine + session maker."""

    global _engine, _session_maker
    _engine = None
    _session_maker = None


__all__ = [
    "Base",
    "get_engine",
    "get_session",
    "get_session_maker",
    "reset_engine",
]
