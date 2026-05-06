"""Tests for cancel, reschedule, list_mine, and handoff intents."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from citas_bot.config import BusinessInfo
from citas_bot.data.repositories import (
    AppointmentRepository,
    ConversationRepository,
    CustomerRepository,
)
from citas_bot.domain import (
    Appointment,
    AppointmentStatus,
    Base,
    Conversation,
    Customer,
)
from citas_bot.domain.base import utc_now
from citas_bot.intents import IntentRouter
from citas_bot.intents.registry import build_default_registry
from citas_bot.llm import ChatResponse, LLMProvider


def _llm_mock() -> LLMProvider:
    mock = AsyncMock(spec=LLMProvider)
    mock.chat = AsyncMock(
        return_value=ChatResponse(
            text='{"intent_name":"info","confidence":0.5}',
            model="m",
            tokens_in=1,
            tokens_out=1,
            raw={},
        )
    )
    return mock


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


@pytest.fixture
def business_info() -> BusinessInfo:
    return BusinessInfo(name="Demo", hours="9-18", address="x", phone="", description="")


@pytest_asyncio.fixture
async def setup(
    session: AsyncSession, business_info: BusinessInfo
) -> tuple[Customer, Conversation, ConversationRepository, IntentRouter, AsyncSession]:
    customers = CustomerRepository(session)
    convs = ConversationRepository(session)
    customer = await customers.get_or_create("+5215559998877", name="C")
    conversation = await convs.get_or_create(customer.id)
    router = IntentRouter(
        registry=build_default_registry(),
        llm=_llm_mock(),
        business_info=business_info,
        conversation_repo=convs,
    )
    return customer, conversation, convs, router, session


@pytest.mark.asyncio
async def test_list_mine_empty(
    setup: tuple[Customer, Conversation, ConversationRepository, IntentRouter, AsyncSession],
) -> None:
    customer, conversation, _, router, session = setup
    reply = await router.route(customer, conversation, "mis citas", session=session)
    assert reply is not None
    assert "no tienes" in reply.text.lower()


@pytest.mark.asyncio
async def test_list_mine_with_appointments(
    setup: tuple[Customer, Conversation, ConversationRepository, IntentRouter, AsyncSession],
) -> None:
    customer, conversation, _, router, session = setup
    repo = AppointmentRepository(session)
    await repo.add(
        Appointment(
            customer_id=customer.id,
            scheduled_at=utc_now() + timedelta(days=2),
            status=AppointmentStatus.SCHEDULED,
        )
    )
    reply = await router.route(customer, conversation, "mis citas", session=session)
    assert reply is not None
    assert "1." in reply.text


@pytest.mark.asyncio
async def test_handoff_marks_conversation(
    setup: tuple[Customer, Conversation, ConversationRepository, IntentRouter, AsyncSession],
) -> None:
    customer, conversation, convs, router, session = setup
    reply = await router.route(
        customer, conversation, "quiero hablar con un humano", session=session
    )
    assert reply is not None
    assert "equipo" in reply.text.lower() or "alguien" in reply.text.lower()
    refreshed = await convs.get_active(customer.id)
    assert refreshed is not None
    assert refreshed.handoff_active is True


@pytest.mark.asyncio
async def test_cancel_no_appointments(
    setup: tuple[Customer, Conversation, ConversationRepository, IntentRouter, AsyncSession],
) -> None:
    customer, conversation, _, router, session = setup
    reply = await router.route(customer, conversation, "cancelar mi cita", session=session)
    assert reply is not None
    assert "no tienes" in reply.text.lower()


@pytest.mark.asyncio
async def test_cancel_full_flow(
    setup: tuple[Customer, Conversation, ConversationRepository, IntentRouter, AsyncSession],
) -> None:
    customer, conversation, convs, router, session = setup
    repo = AppointmentRepository(session)
    appt = await repo.add(
        Appointment(
            customer_id=customer.id,
            scheduled_at=utc_now() + timedelta(days=3),
            status=AppointmentStatus.SCHEDULED,
        )
    )

    reply = await router.route(customer, conversation, "cancelar mi cita", session=session)
    assert reply is not None
    assert "1." in reply.text

    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    reply = await router.route(customer, conversation, "1", session=session)
    assert reply is not None
    assert "confirmas" in reply.text.lower()

    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    reply = await router.route(customer, conversation, "si", session=session)
    assert reply is not None
    assert "cancele" in reply.text.lower()

    refreshed = await repo.get(appt.id)
    assert refreshed is not None
    assert refreshed.status == AppointmentStatus.CANCELLED
