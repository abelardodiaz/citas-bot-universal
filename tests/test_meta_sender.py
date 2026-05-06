"""MetaSender tests with httpx MockTransport."""

from __future__ import annotations

import httpx
import pytest

from citas_bot.intents.base import Reply
from citas_bot.messaging import MetaSender


def _client(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler, timeout=5.0)


@pytest.mark.asyncio
async def test_send_posts_text_payload() -> None:
    received: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        received.append(
            {
                "url": str(request.url),
                "auth": request.headers.get("authorization", ""),
                "json": request.read().decode(),
            }
        )
        return httpx.Response(200, json={"messages": [{"id": "wamid.123"}]})

    sender = MetaSender(
        phone_number_id="555",
        access_token="EAAtoken",
        client=_client(httpx.MockTransport(handler)),
    )

    await sender.send("+5215551112222", Reply(text="hola", type="text"))
    await sender.aclose()

    assert len(received) == 1
    assert "555/messages" in received[0]["url"]  # type: ignore[arg-type]
    assert received[0]["auth"] == "Bearer EAAtoken"


@pytest.mark.asyncio
async def test_send_retries_on_5xx_then_succeeds() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) < 2:
            return httpx.Response(500, json={"error": "boom"})
        return httpx.Response(200, json={"messages": [{"id": "wamid.x"}]})

    sender = MetaSender(
        phone_number_id="1",
        access_token="t",
        client=_client(httpx.MockTransport(handler)),
        max_retries=3,
    )
    await sender.send("+5215550000000", Reply(text="ping"))
    await sender.aclose()

    assert len(calls) == 2


@pytest.mark.asyncio
async def test_send_skips_when_unconfigured() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not be called")

    sender = MetaSender(
        phone_number_id="",
        access_token="",
        client=_client(httpx.MockTransport(handler)),
    )
    await sender.send("+5215550000000", Reply(text="x"))
    await sender.aclose()
