"""'cancel' intent: pick an active appointment and cancel it."""

from __future__ import annotations

import re
from datetime import datetime
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


def _format_when(scheduled_at: datetime, tz_name: str) -> str:
    return scheduled_at.astimezone(ZoneInfo(tz_name)).strftime("%A %d/%m a las %H:%M")


def _is_cancel_keyword(text: str) -> bool:
    lower = text.strip().lower()
    return any(kw in lower for kw in intl.KEYWORD_CANCEL)


def _starts_with_any(text: str, keywords: tuple[str, ...]) -> bool:
    lower = text.strip().lower()
    return any(lower.startswith(kw) for kw in keywords)


async def _load_active(ctx: IntentContext) -> list[Appointment]:
    if ctx.session is None:
        return []
    repo = AppointmentRepository(ctx.session)
    return await repo.list_for_customer(
        ctx.customer.id,
        statuses=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED],
    )


async def handle_cancel(ctx: IntentContext) -> IntentResult:
    settings = get_settings()
    tz = settings.business_timezone
    slots = dict(ctx.conversation.slots_filled or {})

    if _is_cancel_keyword(ctx.text) and slots:
        # User reaffirms cancel inside the cancel flow itself: keep going.
        pass

    active = await _load_active(ctx)
    if not active:
        return IntentResult(
            reply=Reply(text=intl.CANCEL_NO_APPOINTMENTS), clear_state=True
        )

    step = "pick" if "picked_id" not in slots else "confirm"

    if step == "pick":
        # First turn: present list. If user already provided a number, parse it.
        digit_match = re.fullmatch(r"\s*(\d+)\s*", ctx.text)
        if digit_match and slots.get("listed"):
            choice = int(digit_match.group(1))
            if not (1 <= choice <= len(active)):
                return IntentResult(
                    reply=Reply(text=intl.CANCEL_INVALID_PICK),
                    new_intent="cancel",
                    new_slots=slots,
                )
            picked = active[choice - 1]
            slots["picked_id"] = picked.id
            return IntentResult(
                reply=Reply(
                    text=intl.CANCEL_CONFIRM_TPL.format(
                        when=_format_when(picked.scheduled_at, tz)
                    )
                ),
                new_intent="cancel",
                new_slots=slots,
            )

        listing = "\n".join(
            f"{i + 1}. {_format_when(a.scheduled_at, tz)}"
            for i, a in enumerate(active)
        )
        slots["listed"] = True
        return IntentResult(
            reply=Reply(
                text=intl.CANCEL_PICK_TPL.format(listing=listing),
                type="text",
                options=[a.id for a in active],
            ),
            new_intent="cancel",
            new_slots=slots,
        )

    # step == "confirm"
    if _starts_with_any(ctx.text, intl.KEYWORD_NO):
        return IntentResult(reply=Reply(text=intl.BOOK_CANCEL), clear_state=True)
    if not _starts_with_any(ctx.text, intl.KEYWORD_YES):
        # Re-ask
        picked = next((a for a in active if a.id == slots["picked_id"]), None)
        if picked is None:
            return IntentResult(
                reply=Reply(text=intl.CANCEL_NO_APPOINTMENTS), clear_state=True
            )
        return IntentResult(
            reply=Reply(
                text=intl.CANCEL_CONFIRM_TPL.format(
                    when=_format_when(picked.scheduled_at, tz)
                )
            ),
            new_intent="cancel",
            new_slots=slots,
        )

    if ctx.session is None:
        return IntentResult(reply=Reply(text=intl.BOOK_RETRY_EXHAUSTED), clear_state=True)

    repo = AppointmentRepository(ctx.session)
    updated = await repo.update_status(slots["picked_id"], AppointmentStatus.CANCELLED)
    if updated is None:
        return IntentResult(reply=Reply(text=intl.CANCEL_NO_APPOINTMENTS), clear_state=True)
    appt = updated
    return IntentResult(
        reply=Reply(
            text=intl.CANCEL_DONE_TPL.format(when=_format_when(appt.scheduled_at, tz))
        ),
        clear_state=True,
    )


def _cancel_keywords() -> list[str]:
    return list(intl.KEYWORD_CANCEL_INTENT)


CANCEL = Intent(
    name="cancel",
    description="Cancelar una cita existente",
    examples=["cancelar mi cita", "cancela mi cita del lunes"],
    handler=handle_cancel,
    keywords=_cancel_keywords(),
)
