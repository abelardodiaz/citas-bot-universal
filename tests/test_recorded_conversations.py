"""Replay JSON-backed conversation fixtures through the IntentRouter."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
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
from citas_bot.domain import AppointmentStatus, Base, Conversation, Customer
from citas_bot.intents import IntentRouter
from citas_bot.intents.registry import build_default_registry
from citas_bot.llm import ChatResponse, LLMProvider

FIXTURES = Path(__file__).parent / "fixtures" / "conversations"


def _llm_mock() -> LLMProvider:
    mock = AsyncMock(spec=LLMProvider)
    mock.chat = AsyncMock(
        return_value=ChatResponse(
            text="Aceptamos tarjetas y efectivo.",
            model="m",
            tokens_in=1,
            tokens_out=1,
            raw={},
        )
    )
    return mock


@pytest_asyncio.fixture
async def session_setup() -> AsyncIterator[
    tuple[AsyncSession, Customer, Conversation, IntentRouter]
]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        customers = CustomerRepository(session)
        convs = ConversationRepository(session)
        customer = await customers.get_or_create("+5215551112233", name="Test")
        conversation = await convs.get_or_create(customer.id)
        router = IntentRouter(
            registry=build_default_registry(),
            llm=_llm_mock(),
            business_info=BusinessInfo(
                name="Demo",
                hours="9-18",
                address="x",
                phone="",
                description="",
            ),
            conversation_repo=convs,
        )
        yield session, customer, conversation, router
    await engine.dispose()


def _list_fixtures() -> list[Path]:
    return sorted(FIXTURES.glob("*.json"))


@pytest.mark.parametrize("fixture_path", _list_fixtures(), ids=lambda p: p.stem)
@pytest.mark.asyncio
async def test_recorded_conversation(
    fixture_path: Path,
    session_setup: tuple[AsyncSession, Customer, Conversation, IntentRouter],
) -> None:
    session, customer, conversation, router = session_setup
    convs = ConversationRepository(session)
    appts = AppointmentRepository(session)

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    for turn in fixture["turns"]:
        # Refresh conversation from DB so router sees latest state
        latest = await convs.get_active(customer.id)
        assert latest is not None
        reply = await router.route(customer, latest, turn["in"], session=session)
        assert reply is not None, f"router returned None for input: {turn['in']!r}"
        if turn["expect"]:
            assert turn["expect"].lower() in reply.text.lower(), (
                f"fixture {fixture['name']!r} turn {turn['in']!r}: "
                f"expected substring {turn['expect']!r} in reply {reply.text!r}"
            )

    if "expected_appointments" in fixture:
        all_appts = await appts.list_for_customer(customer.id)
        assert len(all_appts) == fixture["expected_appointments"]

    if "expected_cancelled" in fixture:
        cancelled = await appts.list_for_customer(
            customer.id, statuses=[AppointmentStatus.CANCELLED]
        )
        assert len(cancelled) == fixture["expected_cancelled"]

    if fixture.get("expected_handoff"):
        latest = await convs.get_active(customer.id)
        assert latest is not None
        assert latest.handoff_active is True
