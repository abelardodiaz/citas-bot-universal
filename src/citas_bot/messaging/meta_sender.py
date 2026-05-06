"""Real Meta WhatsApp Cloud API sender.

POSTs to ``https://graph.facebook.com/{api_version}/{phone_number_id}/messages``
with a Bearer token. Failures are retried with exponential backoff and logged
without raising — the webhook handler should always return 200 to Meta.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from citas_bot.intents.base import Reply
from citas_bot.observability import get_logger

log = get_logger(__name__)

DEFAULT_API_VERSION = "v18.0"
DEFAULT_BASE_URL = "https://graph.facebook.com"


class MetaSender:
    """Send Reply objects to a customer via Meta's WhatsApp Cloud API."""

    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        client: httpx.AsyncClient | None = None,
        api_version: str = DEFAULT_API_VERSION,
        base_url: str = DEFAULT_BASE_URL,
        max_retries: int = 3,
    ) -> None:
        if not phone_number_id or not access_token:
            log.warning("meta_sender_missing_credentials")
        self._phone_number_id = phone_number_id
        self._access_token = access_token
        self._client = client or httpx.AsyncClient(timeout=15.0)
        self._url = f"{base_url}/{api_version}/{phone_number_id}/messages"
        self._max_retries = max_retries

    async def send(self, to: str, reply: Reply) -> None:
        if not self._phone_number_id or not self._access_token:
            log.error("meta_send_skipped_unconfigured", to=to)
            return

        body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": reply.text, "preview_url": False},
        }
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        try:
            await self._post_with_retry(headers, body)
        except Exception as exc:
            log.error("meta_send_failed", to=to, error=str(exc))

    async def _post_with_retry(
        self, headers: Mapping[str, str], body: Mapping[str, Any]
    ) -> None:
        retryer = AsyncRetrying(
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type((httpx.HTTPError,)),
            reraise=True,
        )
        async for attempt in retryer:
            with attempt:
                response = await self._client.post(self._url, headers=headers, json=body)
                response.raise_for_status()
                log.info(
                    "meta_send_ok",
                    status=response.status_code,
                    body_len=len(response.content),
                )
                return

    async def aclose(self) -> None:
        await self._client.aclose()
