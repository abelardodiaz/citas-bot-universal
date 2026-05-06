"""HMAC signature validation and verify-token check for Meta webhook.

Two functions are exposed for FastAPI to use as dependencies:

- ``verify_token``: used by the GET handshake to compare the token Meta sends
  against the configured one.
- ``verify_signature``: used by the POST handler. Reads the raw request body
  (only consumable once), validates ``X-Hub-Signature-256``, and returns the
  raw bytes for the handler to parse afterwards.

Returning bytes (not a parsed model) is intentional: FastAPI's body consumption
is exclusive, so HMAC must run *before* any JSON parsing. See
``M02-webhook-meta/decision.md`` for rationale.
"""

from __future__ import annotations

import hmac
from hashlib import sha256
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from citas_bot.config import Settings, get_settings
from citas_bot.observability import get_logger

log = get_logger(__name__)


SettingsDep = Annotated[Settings, Depends(get_settings)]


def verify_token(token: str, settings: Settings) -> bool:
    """Constant-time compare for the GET handshake verify_token."""

    expected = settings.meta_verify_token.encode("utf-8")
    received = token.encode("utf-8")
    return hmac.compare_digest(expected, received)


async def verify_signature(
    request: Request,
    settings: SettingsDep,
    x_hub_signature_256: Annotated[str | None, Header(alias="X-Hub-Signature-256")] = None,
) -> bytes:
    """Validate the HMAC-SHA256 signature on a webhook POST.

    Returns the raw request body if valid; raises 401 otherwise.

    Per ``decision.md`` (DeepSeek ticket 1135), missing header and invalid
    signature both return 401: silently accepting either undermines HMAC.
    """

    if x_hub_signature_256 is None:
        log.warning("webhook_missing_signature_header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Hub-Signature-256 header",
        )

    body = await request.body()
    secret = settings.meta_app_secret.encode("utf-8")
    expected_digest = hmac.new(secret, body, sha256).hexdigest()
    expected = f"sha256={expected_digest}"

    if not hmac.compare_digest(expected, x_hub_signature_256):
        log.warning(
            "webhook_invalid_signature",
            body_len=len(body),
            provided_prefix=x_hub_signature_256[:20],
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    return body
