"""Reminder scanner tests with frozen time."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from freezegun import freeze_time
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from citas_bot.config import Settings
from citas_bot.data.repositories import CustomerRepository
from citas_bot.domain import Appointment, AppointmentStatus, Base
from citas_bot.scheduling import scan_and_send


def _settings() -> Settings:
    return Settings(
        meta_verify_token="t",
        meta_app_secret="s",
        anthropic_api_key="x",
        business_info_json='{"name":"Demo","hours":"9-18","address":"x","phone":"","description":""}',
        business_timezone="America/Mexico_City",
        reminder_scan_interval_seconds=300,
        reminder_window_minutes=5,
    )


@pytest_asyncio.fixture
async def session_and_factory() -> AsyncIterator[
    tuple[AsyncSession, async_sessionmaker[AsyncSession]]
]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s, maker
    await engine.dispose()


@pytest.mark.asyncio
async def test_no_appointments_means_zero_sent(
    session_and_factory: tuple[AsyncSession, async_sessionmaker[AsyncSession]],
) -> None:
    _, maker = session_and_factory
    sender = AsyncMock()
    sent = await scan_and_send(_settings(), sender, maker)
    assert sent == 0
    sender.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_24h_reminder_fires_inside_window(
    session_and_factory: tuple[AsyncSession, async_sessionmaker[AsyncSession]],
) -> None:
    session, maker = session_and_factory
    customer = await CustomerRepository(session).get_or_create(
        "+5215559990001", name="Ana"
    )
    now = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    appt = Appointment(
        customer_id=customer.id,
        scheduled_at=now + timedelta(hours=24),
        status=AppointmentStatus.SCHEDULED,
    )
    session.add(appt)
    await session.commit()

    sender = AsyncMock()
    with freeze_time(now):
        sent = await scan_and_send(_settings(), sender, maker, now=now)

    assert sent == 1
    sender.send.assert_awaited_once()
    await session.refresh(appt)
    assert appt.reminder_24h_sent is True
    assert appt.reminder_2h_sent is False


@pytest.mark.asyncio
async def test_2h_reminder_fires(
    session_and_factory: tuple[AsyncSession, async_sessionmaker[AsyncSession]],
) -> None:
    session, maker = session_and_factory
    customer = await CustomerRepository(session).get_or_create(
        "+5215559990002", name="Beto"
    )
    now = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    appt = Appointment(
        customer_id=customer.id,
        scheduled_at=now + timedelta(hours=2),
        status=AppointmentStatus.SCHEDULED,
        reminder_24h_sent=True,  # already sent 22h ago
    )
    session.add(appt)
    await session.commit()

    sender = AsyncMock()
    sent = await scan_and_send(_settings(), sender, maker, now=now)
    assert sent == 1
    await session.refresh(appt)
    assert appt.reminder_2h_sent is True


@pytest.mark.asyncio
async def test_no_double_send_on_repeat_run(
    session_and_factory: tuple[AsyncSession, async_sessionmaker[AsyncSession]],
) -> None:
    session, maker = session_and_factory
    customer = await CustomerRepository(session).get_or_create(
        "+5215559990003", name="X"
    )
    now = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    appt = Appointment(
        customer_id=customer.id,
        scheduled_at=now + timedelta(hours=24),
        status=AppointmentStatus.SCHEDULED,
    )
    session.add(appt)
    await session.commit()

    sender = AsyncMock()
    sent_first = await scan_and_send(_settings(), sender, maker, now=now)
    sent_second = await scan_and_send(_settings(), sender, maker, now=now)
    assert sent_first == 1
    assert sent_second == 0


@pytest.mark.asyncio
async def test_outside_window_no_send(
    session_and_factory: tuple[AsyncSession, async_sessionmaker[AsyncSession]],
) -> None:
    session, maker = session_and_factory
    customer = await CustomerRepository(session).get_or_create(
        "+5215559990004", name="X"
    )
    now = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    appt = Appointment(
        customer_id=customer.id,
        scheduled_at=now + timedelta(hours=12),  # neither 24h nor 2h
        status=AppointmentStatus.SCHEDULED,
    )
    session.add(appt)
    await session.commit()

    sender = AsyncMock()
    sent = await scan_and_send(_settings(), sender, maker, now=now)
    assert sent == 0
