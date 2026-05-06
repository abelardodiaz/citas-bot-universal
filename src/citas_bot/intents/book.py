"""'book' intent: schedules a new appointment via slot filling.

State is implicit in ``conversation.slots_filled``: the next required slot
determines what the bot asks next. Order: date -> time -> name -> confirm
-> persist.

This handler is reentrant: every user turn calls it again until either the
appointment is created or the user cancels.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import dateparser

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
from citas_bot.observability import get_logger

log = get_logger(__name__)

SLOT_ORDER = ["date", "time", "name", "confirm"]
RETRY_KEY = "_retries"
RETRY_MAX = 3


def _business_hours_range(hours_str: str) -> tuple[int, int]:
    """Best-effort parse of a hours string. Defaults to (9, 18)."""

    digits = [int(s) for s in re.findall(r"\d{1,2}", hours_str)]
    if len(digits) < 2:
        return 9, 18
    start, end = digits[0], digits[1]
    if end <= start:
        end = end + 12 if end < 12 else end
    return start, end


def _is_cancel(text: str) -> bool:
    lower = text.strip().lower()
    return any(kw in lower for kw in intl.KEYWORD_CANCEL)


def _starts_with_any(text: str, keywords: tuple[str, ...]) -> bool:
    lower = text.strip().lower()
    return any(lower.startswith(kw) for kw in keywords)


def _parse_date(text: str, business_tz: str) -> datetime | None:
    parsed: datetime | None = dateparser.parse(
        text,
        languages=["es"],
        settings={
            "TIMEZONE": business_tz,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
        },
    )
    return parsed


def _parse_time_on_date(text: str, base_iso: str, business_tz: str) -> datetime | None:
    base = datetime.fromisoformat(base_iso)
    parsed = dateparser.parse(
        text,
        languages=["es"],
        settings={
            "TIMEZONE": business_tz,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
        },
    )
    if parsed is None:
        return None
    return base.replace(
        hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0
    )


def _looks_like_name(text: str) -> bool:
    parts = text.strip().split()
    if not (1 <= len(parts) <= 3):
        return False
    return all(re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ'-]+", p) for p in parts)


def _next_step(slots: dict[str, Any]) -> str:
    for slot in SLOT_ORDER:
        if slot not in slots or slots[slot] is None:
            return slot
    return "done"


def _bump_retry(slots: dict[str, Any]) -> int:
    retries = int(slots.get(RETRY_KEY, 0)) + 1
    slots[RETRY_KEY] = retries
    return retries


def _format_when(scheduled_at: datetime, tz_name: str) -> str:
    return scheduled_at.astimezone(ZoneInfo(tz_name)).strftime("%A %d/%m a las %H:%M")


def _retry_or(text: str, slots: dict[str, Any]) -> IntentResult:
    retries = _bump_retry(slots)
    if retries >= RETRY_MAX:
        return IntentResult(reply=Reply(text=intl.BOOK_RETRY_EXHAUSTED), clear_state=True)
    return IntentResult(reply=Reply(text=text), new_intent="book", new_slots=slots)


async def handle_book(ctx: IntentContext) -> IntentResult:
    settings = get_settings()
    tz = settings.business_timezone

    if _is_cancel(ctx.text):
        return IntentResult(reply=Reply(text=intl.BOOK_CANCEL), clear_state=True)

    slots = dict(ctx.conversation.slots_filled or {})
    step = _next_step(slots)

    if step == "date":
        return _step_date(ctx.text, slots, tz)
    if step == "time":
        return _step_time(ctx.text, slots, tz, settings.business_info.hours)
    if step == "name":
        return _step_name(ctx.text, slots, tz)
    if step == "confirm":
        return await _step_confirm(ctx, slots, tz, settings.appointment_duration_minutes)
    return IntentResult(reply=Reply(text=intl.BOOK_RETRY_EXHAUSTED), clear_state=True)


def _step_date(text: str, slots: dict[str, Any], tz: str) -> IntentResult:
    parsed = _parse_date(text, tz)
    if parsed is None:
        return _retry_or(intl.BOOK_INVALID_DATE, slots)
    if parsed.date() < datetime.now(parsed.tzinfo).date():
        return _retry_or(intl.BOOK_PAST_DATE, slots)

    slots[RETRY_KEY] = 0
    slots["date"] = parsed.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    return IntentResult(reply=Reply(text=intl.BOOK_ASK_TIME), new_intent="book", new_slots=slots)


def _step_time(text: str, slots: dict[str, Any], tz: str, hours_str: str) -> IntentResult:
    base_iso = slots.get("date")
    if not isinstance(base_iso, str):
        return IntentResult(
            reply=Reply(text=intl.BOOK_ASK_DATE), new_intent="book", new_slots={}
        )

    parsed = _parse_time_on_date(text, base_iso, tz)
    if parsed is None:
        return _retry_or(intl.BOOK_INVALID_TIME, slots)

    start_h, end_h = _business_hours_range(hours_str)
    local_hour = parsed.astimezone(ZoneInfo(tz)).hour
    if not (start_h <= local_hour < end_h):
        return _retry_or(intl.BOOK_OUT_OF_HOURS_TPL.format(hours=hours_str), slots)

    slots[RETRY_KEY] = 0
    slots["time"] = parsed.isoformat()
    return IntentResult(reply=Reply(text=intl.BOOK_ASK_NAME), new_intent="book", new_slots=slots)


def _step_name(text: str, slots: dict[str, Any], tz: str) -> IntentResult:
    if not _looks_like_name(text):
        return _retry_or(intl.BOOK_INVALID_NAME, slots)

    slots[RETRY_KEY] = 0
    slots["name"] = text.strip()
    when = datetime.fromisoformat(slots["time"])
    confirm_text = intl.BOOK_CONFIRM_TPL.format(
        when=_format_when(when, tz), name=slots["name"]
    )
    return IntentResult(reply=Reply(text=confirm_text), new_intent="book", new_slots=slots)


async def _step_confirm(
    ctx: IntentContext,
    slots: dict[str, Any],
    tz: str,
    duration: int,
) -> IntentResult:
    text = ctx.text
    if _starts_with_any(text, intl.KEYWORD_NO):
        return IntentResult(reply=Reply(text=intl.BOOK_CANCEL), clear_state=True)
    if not _starts_with_any(text, intl.KEYWORD_YES):
        when = datetime.fromisoformat(slots["time"])
        return IntentResult(
            reply=Reply(
                text=intl.BOOK_CONFIRM_TPL.format(
                    when=_format_when(when, tz), name=slots["name"]
                )
            ),
            new_intent="book",
            new_slots=slots,
        )

    if ctx.session is None:
        log.error("book_confirm_without_session")
        return IntentResult(reply=Reply(text=intl.BOOK_RETRY_EXHAUSTED), clear_state=True)

    when = datetime.fromisoformat(slots["time"])
    repo = AppointmentRepository(ctx.session)
    existing = await repo.list_for_customer(ctx.customer.id)
    if any(a.scheduled_at == when for a in existing):
        return IntentResult(reply=Reply(text=intl.BOOK_DUPLICATE), clear_state=True)

    appointment = Appointment(
        customer_id=ctx.customer.id,
        scheduled_at=when,
        duration_minutes=duration,
        status=AppointmentStatus.SCHEDULED,
        notes=f"name={slots['name']}",
    )
    await repo.add(appointment)
    log.info(
        "appointment_booked",
        appointment_id=appointment.id,
        customer_id=ctx.customer.id,
        scheduled_at=when.isoformat(),
    )
    return IntentResult(
        reply=Reply(
            text=intl.BOOK_DONE_TPL.format(
                when=_format_when(when, tz), name=slots["name"]
            )
        ),
        clear_state=True,
    )


BOOK = Intent(
    name="book",
    description="Agendar una nueva cita (pide fecha, hora y nombre)",
    examples=["quiero agendar una cita", "me das una cita", "agenda para manana"],
    handler=handle_book,
    keywords=list(intl.KEYWORD_BOOK),
)
