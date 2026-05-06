"""Tests for the intent router, info handler, and registry."""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from citas_bot.config import BusinessInfo
from citas_bot.data.repositories import ConversationRepository, CustomerRepository
from citas_bot.domain import Base, Conversation, Customer
from citas_bot.intents import IntentRouter
from citas_bot.intents.base import IntentContext
from citas_bot.intents.info import handle_info
from citas_bot.intents.registry import build_default_registry
from citas_bot.llm import ChatResponse, LLMError, LLMProvider


def _make_llm_response(text: str) -> ChatResponse:
    return ChatResponse(
        text=text, model="test-model", tokens_in=10, tokens_out=5, raw={}
    )


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


@pytest_asyncio.fixture
async def setup_data(
    session: AsyncSession,
) -> tuple[Customer, Conversation, ConversationRepository]:
    customer_repo = CustomerRepository(session)
    conv_repo = ConversationRepository(session)
    customer = await customer_repo.get_or_create("+5215551234567", name="Ana")
    conversation = await conv_repo.get_or_create(customer.id)
    return customer, conversation, conv_repo


@pytest.fixture
def business_info() -> BusinessInfo:
    return BusinessInfo(
        name="Barberia Demo",
        hours="Lun-Vie 9-18",
        address="Av. X 123",
        phone="+5215555555555",
        description="Cortes",
    )


def _make_llm_mock(response_text: str = "ok") -> LLMProvider:
    mock = AsyncMock(spec=LLMProvider)
    mock.chat = AsyncMock(return_value=_make_llm_response(response_text))
    return mock


@pytest.mark.asyncio
async def test_info_handler_uses_llm_when_available(
    business_info: BusinessInfo,
) -> None:
    customer = Customer(whatsapp_number="+5215550000001", name="A")
    conversation = Conversation(customer_id="x", slots_filled={})
    llm = _make_llm_mock("Estamos en Av. X 123, Lun-Vie 9-18.")

    ctx = IntentContext(
        customer=customer,
        conversation=conversation,
        text="?donde estan ubicados?",
        business_info=business_info,
        llm=llm,
    )
    result = await handle_info(ctx)
    assert "Av. X 123" in result.reply.text
    assert result.reply.type == "text"
    llm.chat.assert_awaited_once()


@pytest.mark.asyncio
async def test_info_handler_falls_back_when_llm_errors(
    business_info: BusinessInfo,
) -> None:
    customer = Customer(whatsapp_number="+5215550000002", name="B")
    conversation = Conversation(customer_id="x", slots_filled={})
    failing_llm = AsyncMock(spec=LLMProvider)
    failing_llm.chat = AsyncMock(side_effect=LLMError("boom"))

    ctx = IntentContext(
        customer=customer,
        conversation=conversation,
        text="?cuanto cuestan?",
        business_info=business_info,
        llm=failing_llm,
    )
    result = await handle_info(ctx)
    assert "Barberia Demo" in result.reply.text
    assert business_info.address in result.reply.text


@pytest.mark.asyncio
async def test_router_classifies_via_keyword_without_calling_llm(
    setup_data: tuple[Customer, Conversation, ConversationRepository],
    business_info: BusinessInfo,
) -> None:
    customer, conversation, conv_repo = setup_data
    llm = _make_llm_mock("from_llm")
    router = IntentRouter(
        registry=build_default_registry(),
        llm=llm,
        business_info=business_info,
        conversation_repo=conv_repo,
    )

    reply = await router.route(customer, conversation, "?cual es el horario?")

    assert reply is not None
    # info handler is called; LLM is invoked exactly once (by the handler)
    # not twice (since classification was keyword-based, not LLM)
    assert llm.chat.await_count == 1


@pytest.mark.asyncio
async def test_router_uses_llm_classifier_when_no_keyword_match(
    setup_data: tuple[Customer, Conversation, ConversationRepository],
    business_info: BusinessInfo,
) -> None:
    customer, conversation, conv_repo = setup_data
    llm = AsyncMock(spec=LLMProvider)
    # First call: classifier; second: info handler
    llm.chat = AsyncMock(
        side_effect=[
            _make_llm_response('{"intent_name":"info","confidence":0.9,"reasoning":"x"}'),
            _make_llm_response("Estamos en Av. X 123."),
        ]
    )
    router = IntentRouter(
        registry=build_default_registry(),
        llm=llm,
        business_info=business_info,
        conversation_repo=conv_repo,
    )

    reply = await router.route(
        customer, conversation, "que tipos de servicios brindan al publico"
    )
    assert reply is not None
    assert llm.chat.await_count == 2


@pytest.mark.asyncio
async def test_router_falls_back_to_default_when_classifier_errors(
    setup_data: tuple[Customer, Conversation, ConversationRepository],
    business_info: BusinessInfo,
) -> None:
    customer, conversation, conv_repo = setup_data
    llm = AsyncMock(spec=LLMProvider)
    llm.chat = AsyncMock(side_effect=LLMError("rate limited"))
    router = IntentRouter(
        registry=build_default_registry(),
        llm=llm,
        business_info=business_info,
        conversation_repo=conv_repo,
    )

    reply = await router.route(customer, conversation, "asdf qwerty random text")
    assert reply is not None
    assert "no entiendo" in reply.text.lower()


@pytest.mark.asyncio
async def test_router_dedupes_repeated_message_id(
    setup_data: tuple[Customer, Conversation, ConversationRepository],
    business_info: BusinessInfo,
) -> None:
    customer, conversation, conv_repo = setup_data
    llm = _make_llm_mock("ok")
    router = IntentRouter(
        registry=build_default_registry(),
        llm=llm,
        business_info=business_info,
        conversation_repo=conv_repo,
    )

    first = await router.route(
        customer, conversation, "?horario?", message_id="wamid.1"
    )
    second = await router.route(
        customer, conversation, "?horario?", message_id="wamid.1"
    )
    assert first is not None
    assert second is None  # deduped


@pytest.mark.asyncio
async def test_router_persists_conversation_intent(
    setup_data: tuple[Customer, Conversation, ConversationRepository],
    business_info: BusinessInfo,
) -> None:
    customer, conversation, conv_repo = setup_data
    llm = _make_llm_mock("ok")
    router = IntentRouter(
        registry=build_default_registry(),
        llm=llm,
        business_info=business_info,
        conversation_repo=conv_repo,
    )

    await router.route(customer, conversation, "?donde estan ubicados?")

    refreshed = await conv_repo.get_active(customer.id)
    assert refreshed is not None
    # info handler returns new_intent=None, so router defaults to keeping
    # the dispatched intent name
    assert refreshed.current_intent == "info"
