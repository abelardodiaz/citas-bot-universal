"""Coverage for the engine + session factory module."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from citas_bot.config import Settings
from citas_bot.data.db import (
    get_engine,
    get_session,
    get_session_maker,
    reset_engine,
)
from citas_bot.domain import Base


def _settings() -> Settings:
    return Settings(database_url="sqlite+aiosqlite:///:memory:")


def test_get_engine_returns_async_engine() -> None:
    reset_engine()
    engine = get_engine(_settings())
    assert isinstance(engine, AsyncEngine)


def test_get_engine_is_singleton_across_calls() -> None:
    reset_engine()
    a = get_engine(_settings())
    b = get_engine(_settings())
    assert a is b


def test_get_session_maker_is_singleton() -> None:
    reset_engine()
    a = get_session_maker(_settings())
    b = get_session_maker(_settings())
    assert isinstance(a, async_sessionmaker)
    assert a is b


@pytest.mark.asyncio
async def test_get_session_yields_async_session() -> None:
    reset_engine()
    engine = get_engine(_settings())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    gen = get_session()
    session = await anext(gen)
    assert isinstance(session, AsyncSession)
    # Closing the generator triggers commit + cleanup.
    await gen.aclose()
