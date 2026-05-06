"""'handoff' intent: flag the conversation for human takeover."""

from __future__ import annotations

from citas_bot.intents import intl
from citas_bot.intents.base import (
    Intent,
    IntentContext,
    IntentResult,
    Reply,
)
from citas_bot.observability import get_logger

log = get_logger(__name__)


async def handle_handoff(ctx: IntentContext) -> IntentResult:
    log.info(
        "handoff_requested",
        customer_id=ctx.customer.id,
        whatsapp=ctx.customer.whatsapp_number,
    )
    if ctx.session is not None:
        # Mark the conversation; the router will persist it via the session.
        ctx.conversation.handoff_active = True
    return IntentResult(reply=Reply(text=intl.HANDOFF_DONE), clear_state=True)


HANDOFF = Intent(
    name="handoff",
    description="El usuario quiere hablar con una persona en lugar del bot",
    examples=["quiero hablar con un humano", "pasame con el doctor", "necesito un asesor"],
    handler=handle_handoff,
    keywords=list(intl.KEYWORD_HANDOFF),
)
