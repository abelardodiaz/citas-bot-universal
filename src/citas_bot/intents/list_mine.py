"""'list_mine' intent: lists the customer's active appointments."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from citas_bot.config import get_settings
from citas_bot.data.repositories import AppointmentRepository
from citas_bot.domain import AppointmentStatus
from citas_bot.intents import intl
from citas_bot.intents.base import (
    Intent,
    IntentContext,
    IntentResult,
    Reply,
)


def _format_when(scheduled_at: datetime, tz_name: str) -> str:
    return scheduled_at.astimezone(ZoneInfo(tz_name)).strftime("%A %d/%m a las %H:%M")


async def handle_list_mine(ctx: IntentContext) -> IntentResult:
    if ctx.session is None:
        return IntentResult(reply=Reply(text=intl.LIST_NONE), clear_state=True)

    repo = AppointmentRepository(ctx.session)
    active = await repo.list_for_customer(
        ctx.customer.id,
        statuses=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED],
    )
    if not active:
        return IntentResult(reply=Reply(text=intl.LIST_NONE), clear_state=True)

    tz = get_settings().business_timezone
    listing = "\n".join(
        f"{i + 1}. {_format_when(a.scheduled_at, tz)}" for i, a in enumerate(active)
    )
    return IntentResult(
        reply=Reply(text=intl.LIST_HEADER.format(listing=listing)),
        clear_state=True,
    )


LIST_MINE = Intent(
    name="list_mine",
    description="Lista las citas activas del cliente",
    examples=["mis citas", "que citas tengo", "cuales son mis citas"],
    handler=handle_list_mine,
    keywords=list(intl.KEYWORD_LIST),
)
