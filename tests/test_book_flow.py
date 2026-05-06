"""End-to-end tests for the 'book' intent state machine."""

from __future__ import annotations

from collections.abc import AsyncIterator
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
from citas_bot.domain import Base, Conversation, Customer
from citas_bot.intents import IntentRouter
from citas_bot.intents.registry import build_default_registry
from citas_bot.llm import ChatResponse, LLMProvider


def _llm_mock() -> LLMProvider:
    mock = AsyncMock(spec=LLMProvider)
    mock.chat = AsyncMock(
        return_value=ChatResponse(
            text='{"intent_name":"book","confidence":0.95}',
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
    return BusinessInfo(
        name="Demo",
        hours="9-18",
        address="x",
        phone="",
        description="",
    )


@pytest_asyncio.fixture
async def setup(
    session: AsyncSession, business_info: BusinessInfo
) -> tuple[Customer, Conversation, ConversationRepository, IntentRouter, AsyncSession]:
    customers = CustomerRepository(session)
    convs = ConversationRepository(session)
    customer = await customers.get_or_create("+5215551112233", name="Ana")
    conversation = await convs.get_or_create(customer.id)

    router = IntentRouter(
        registry=build_default_registry(),
        llm=_llm_mock(),
        business_info=business_info,
        conversation_repo=convs,
    )
    return customer, conversation, convs, router, session


@pytest.mark.asyncio
async def test_happy_path_book_appointment(
    setup: tuple[Customer, Conversation, ConversationRepository, IntentRouter, AsyncSession],
) -> None:
    customer, conversation, convs, router, session = setup

    # Turn 1: trigger book via keyword
    reply = await router.route(customer, conversation, "quiero agendar", session=session)
    assert reply is not None
    assert "dia" in reply.text.lower()

    # Turn 2: provide date
    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    reply = await router.route(customer, conversation, "15 de junio", session=session)
    assert reply is not None
    assert "hora" in reply.text.lower()

    # Turn 3: provide time
    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    reply = await router.route(customer, conversation, "10:00", session=session)
    assert reply is not None
    assert "nombre" in reply.text.lower()

    # Turn 4: provide name
    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    reply = await router.route(customer, conversation, "Ana Lopez", session=session)
    assert reply is not None
    assert "confirmar" in reply.text.lower() or "correcto" in reply.text.lower()

    # Turn 5: confirm
    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    reply = await router.route(customer, conversation, "si", session=session)
    assert reply is not None
    assert "confirmo" in reply.text.lower() or "listo" in reply.text.lower()

    appointments = await AppointmentRepository(session).list_for_customer(customer.id)
    assert len(appointments) == 1
    assert appointments[0].notes == "name=Ana Lopez"


@pytest.mark.asyncio
async def test_cancel_mid_flow(
    setup: tuple[Customer, Conversation, ConversationRepository, IntentRouter, AsyncSession],
) -> None:
    customer, conversation, convs, router, session = setup

    await router.route(customer, conversation, "agendar", session=session)
    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    reply = await router.route(customer, conversation, "cancelar", session=session)
    assert reply is not None
    assert "cancelada" in reply.text.lower()

    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    assert conversation.current_intent is None
    assert conversation.slots_filled == {}


@pytest.mark.asyncio
async def test_invalid_time_retries_then_exhausts(
    setup: tuple[Customer, Conversation, ConversationRepository, IntentRouter, AsyncSession],
) -> None:
    customer, conversation, convs, router, session = setup

    await router.route(customer, conversation, "agendar", session=session)
    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    await router.route(customer, conversation, "15 de junio", session=session)

    # Three invalid times -> exhausted
    for _ in range(3):
        conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
        assert conversation is not None
        reply = await router.route(customer, conversation, "qwerty", session=session)
        assert reply is not None

    assert "intenta" in reply.text.lower() or "no logre" in reply.text.lower()
    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    assert conversation.slots_filled == {}


@pytest.mark.asyncio
async def test_confirm_no_does_not_persist(
    setup: tuple[Customer, Conversation, ConversationRepository, IntentRouter, AsyncSession],
) -> None:
    customer, conversation, convs, router, session = setup

    await router.route(customer, conversation, "agendar", session=session)
    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    await router.route(customer, conversation, "15 de junio", session=session)
    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    await router.route(customer, conversation, "11:00", session=session)
    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    await router.route(customer, conversation, "Beto", session=session)
    conversation = await convs.get_active(customer.id)  # type: ignore[assignment]
    assert conversation is not None
    reply = await router.route(customer, conversation, "no", session=session)
    assert reply is not None
    assert "cancelada" in reply.text.lower()

    appointments = await AppointmentRepository(session).list_for_customer(customer.id)
    assert appointments == []
