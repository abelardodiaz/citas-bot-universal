"""Meta WhatsApp Cloud API webhook endpoints (GET handshake + POST receiver)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import ValidationError

from citas_bot.config import Settings, get_settings
from citas_bot.observability import get_logger
from citas_bot.webhooks.schemas import WebhookPayload
from citas_bot.webhooks.security import verify_signature, verify_token

log = get_logger(__name__)

router = APIRouter(tags=["webhook"])


@router.get("/webhook")
async def webhook_verify(
    settings: Annotated[Settings, Depends(get_settings)],
    hub_mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    hub_challenge: Annotated[str | None, Query(alias="hub.challenge")] = None,
    hub_verify_token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
) -> Response:
    """Meta webhook verification handshake.

    Meta sends a GET with hub.mode=subscribe, hub.challenge, hub.verify_token.
    If the token matches the configured one, return the challenge as plain text.
    """

    if hub_mode != "subscribe":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid hub.mode")

    if hub_verify_token is None or not verify_token(hub_verify_token, settings):
        log.warning("webhook_verify_token_mismatch")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid verify token",
        )

    if hub_challenge is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing hub.challenge",
        )

    log.info("webhook_verified")
    return Response(content=hub_challenge, media_type="text/plain")


@router.post("/webhook")
async def webhook_receive(
    body: Annotated[bytes, Depends(verify_signature)],
) -> dict[str, str]:
    """Receive a webhook event from Meta.

    The dependency has already validated the HMAC signature. We log the
    incoming payload and return 200 to acknowledge to Meta.

    Processing of message content is deferred to M05 (intent router).
    """

    try:
        payload = WebhookPayload.model_validate_json(body)
    except ValidationError as exc:
        # We have a valid Meta signature but the payload is unexpected.
        # Return 200 (per Meta contract) but log loud.
        log.warning("webhook_payload_parse_failed", errors=str(exc), body_len=len(body))
        return {"status": "ignored"}

    log.info(
        "webhook_received",
        object=payload.object,
        entries=len(payload.entry),
        total_changes=sum(len(e.changes) for e in payload.entry),
    )
    return {"status": "received"}
