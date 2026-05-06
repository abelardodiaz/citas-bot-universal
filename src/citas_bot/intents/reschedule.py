"""'reschedule' intent: pick an active appointment and move it to a new date+time.

The flow nests 'cancel-style' selection (pick existing) with 'book-style'
slot filling (new date and time). State machine:

    list -> pick -> ask new date -> ask new time -> confirm -> persist
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from citas_bot.config import get_settings
from citas_bot.data.repositories import AppointmentRepository
from citas_bot.domain import Appointment, AppointmentStatus
from citas_bot.intents import intl
from citas_bot.intents.base import (
    Intent,
    IntentContext,
    IntentResult,
    Reply,
)
from citas_bot.intents.book import (
    _business_hours_range,
    _parse_date,
    _parse_time_on_date,
    _retry_or,
)


def _format_when(scheduled_at: datetime, tz_name: str) -> str:
    return scheduled_at.astimezone(ZoneInfo(tz_name)).strftime("%A %d/%m a las %H:%M")


async def _load_active(ctx: IntentContext) -> list[Appointment]:
    if ctx.session is None:
        return []
    repo = AppointmentRepository(ctx.session)
    return await repo.list_for_customer(
        ctx.customer.id,
        statuses=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED],
    )


async def handle_reschedule(ctx: IntentContext) -> IntentResult:
    settings = get_settings()
    tz = settings.business_timezone
    slots = dict(ctx.conversation.slots_filled or {})

    active = await _load_active(ctx)
    if not active:
        return IntentResult(
            reply=Reply(text=intl.RESCHEDULE_NO_APPOINTMENTS), clear_state=True
        )

    if "picked_id" not in slots:
        digit_match = re.fullmatch(r"\s*(\d+)\s*", ctx.text)
        if digit_match and slots.get("listed"):
            choice = int(digit_match.group(1))
            if not (1 <= choice <= len(active)):
                return IntentResult(
                    reply=Reply(text=intl.CANCEL_INVALID_PICK),
                    new_intent="reschedule",
                    new_slots=slots,
                )
            slots["picked_id"] = active[choice - 1].id
            return IntentResult(
                reply=Reply(text=intl.RESCHEDULE_ASK_DATE),
                new_intent="reschedule",
                new_slots=slots,
            )

        listing = "\n".join(
            f"{i + 1}. {_format_when(a.scheduled_at, tz)}"
            for i, a in enumerate(active)
        )
        slots["listed"] = True
        return IntentResult(
            reply=Reply(text=intl.RESCHEDULE_PICK_TPL.format(listing=listing)),
            new_intent="reschedule",
            new_slots=slots,
        )

    if "new_date" not in slots:
        parsed = _parse_date(ctx.text, tz)
        if parsed is None:
            return _retry_or(intl.BOOK_INVALID_DATE, slots)
        if parsed.date() < datetime.now(parsed.tzinfo).date():
            return _retry_or(intl.BOOK_PAST_DATE, slots)
        slots["new_date"] = parsed.replace(hour=0, minute=0, second=0).isoformat()
        return IntentResult(
            reply=Reply(text=intl.BOOK_ASK_TIME),
            new_intent="reschedule",
            new_slots=slots,
        )

    if "new_time" not in slots:
        parsed = _parse_time_on_date(ctx.text, slots["new_date"], tz)
        if parsed is None:
            return _retry_or(intl.BOOK_INVALID_TIME, slots)
        start_h, end_h = _business_hours_range(settings.business_info.hours)
        local_hour = parsed.astimezone(ZoneInfo(tz)).hour
        if not (start_h <= local_hour < end_h):
            return _retry_or(
                intl.BOOK_OUT_OF_HOURS_TPL.format(hours=settings.business_info.hours),
                slots,
            )
        slots["new_time"] = parsed.isoformat()
        return IntentResult(
            reply=Reply(
                text=intl.BOOK_CONFIRM_TPL.format(
                    when=_format_when(parsed, tz),
                    name="(misma cita)",
                )
            ),
            new_intent="reschedule",
            new_slots=slots,
        )

    # Confirm step
    text = ctx.text.strip().lower()
    if text.startswith(intl.KEYWORD_NO):
        return IntentResult(reply=Reply(text=intl.BOOK_CANCEL), clear_state=True)
    if not text.startswith(intl.KEYWORD_YES):
        return IntentResult(
            reply=Reply(
                text=intl.BOOK_CONFIRM_TPL.format(
                    when=_format_when(datetime.fromisoformat(slots["new_time"]), tz),
                    name="(misma cita)",
                )
            ),
            new_intent="reschedule",
            new_slots=slots,
        )

    if ctx.session is None:
        return IntentResult(reply=Reply(text=intl.BOOK_RETRY_EXHAUSTED), clear_state=True)

    repo = AppointmentRepository(ctx.session)
    appt = await repo.get(slots["picked_id"])
    if appt is None:
        return IntentResult(reply=Reply(text=intl.RESCHEDULE_NO_APPOINTMENTS), clear_state=True)
    appt.scheduled_at = datetime.fromisoformat(slots["new_time"])
    return IntentResult(
        reply=Reply(text=intl.RESCHEDULE_DONE_TPL.format(when=_format_when(appt.scheduled_at, tz))),
        clear_state=True,
    )


RESCHEDULE = Intent(
    name="reschedule",
    description="Reprogramar una cita existente a otra fecha y hora",
    examples=["cambiar mi cita", "reagendar", "mover mi cita al viernes"],
    handler=handle_reschedule,
    keywords=list(intl.KEYWORD_RESCHEDULE),
)
