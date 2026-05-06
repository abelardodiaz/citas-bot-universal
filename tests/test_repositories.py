"""End-to-end tests for the repository layer using an in-memory SQLite DB."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from citas_bot.data.repositories import (
    AppointmentRepository,
    ConversationRepository,
    CustomerRepository,
)
from citas_bot.domain import Appointment, AppointmentStatus, Base
from citas_bot.domain.base import utc_now


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_customer_get_or_create_idempotent(session: AsyncSession) -> None:
    repo = CustomerRepository(session)
    a = await repo.get_or_create("+5215551234567", name="Ana")
    b = await repo.get_or_create("+5215551234567", name="Ana")
    assert a.id == b.id


@pytest.mark.asyncio
async def test_appointment_list_for_customer_filters_status(session: AsyncSession) -> None:
    customers = CustomerRepository(session)
    appts = AppointmentRepository(session)
    customer = await customers.get_or_create("+5215551111111", name="Test")
    now = utc_now()
    await appts.add(
        Appointment(
            customer_id=customer.id,
            scheduled_at=now + timedelta(days=1),
            status=AppointmentStatus.SCHEDULED,
        )
    )
    await appts.add(
        Appointment(
            customer_id=customer.id,
            scheduled_at=now + timedelta(days=2),
            status=AppointmentStatus.CANCELLED,
        )
    )

    scheduled = await appts.list_for_customer(
        customer.id, statuses=[AppointmentStatus.SCHEDULED]
    )
    assert len(scheduled) == 1
    assert scheduled[0].status == AppointmentStatus.SCHEDULED


@pytest.mark.asyncio
async def test_appointment_update_status(session: AsyncSession) -> None:
    customers = CustomerRepository(session)
    appts = AppointmentRepository(session)
    customer = await customers.get_or_create("+5215552222222", name="Test")
    appt = await appts.add(
        Appointment(
            customer_id=customer.id,
            scheduled_at=utc_now() + timedelta(days=3),
            status=AppointmentStatus.SCHEDULED,
        )
    )
    updated = await appts.update_status(appt.id, AppointmentStatus.CONFIRMED)
    assert updated is not None
    assert updated.status == AppointmentStatus.CONFIRMED


@pytest.mark.asyncio
async def test_conversation_get_or_create_returns_active(session: AsyncSession) -> None:
    customers = CustomerRepository(session)
    convs = ConversationRepository(session)
    customer = await customers.get_or_create("+5215553333333", name="Test")
    a = await convs.get_or_create(customer.id)
    b = await convs.get_or_create(customer.id)
    assert a.id == b.id


@pytest.mark.asyncio
async def test_conversation_update_state_writes_intent_and_slots(
    session: AsyncSession,
) -> None:
    customers = CustomerRepository(session)
    convs = ConversationRepository(session)
    customer = await customers.get_or_create("+5215554444444", name="Test")
    conv = await convs.get_or_create(customer.id)
    updated = await convs.update_state(
        conv,
        intent="book_appointment",
        slots={"date": "2026-05-20", "time": "10:00"},
    )
    assert updated.current_intent == "book_appointment"
    assert updated.slots_filled["date"] == "2026-05-20"
