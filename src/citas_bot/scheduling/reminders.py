"""Periodic reminder scanner.

The scanner reads ``Appointment`` rows in the SCHEDULED/CONFIRMED states and,
for each one whose ``scheduled_at`` falls inside the 24h or 2h window
(centered, ``reminder_window_minutes`` either side), sends a WhatsApp
reminder via ``MetaSender`` and persists a flag.

Idempotency: ``reminder_24h_sent`` / ``reminder_2h_sent`` booleans on the
Appointment row mean we never double-send across restarts. Failed sends
remain unflagged so the next tick retries naturally.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from sqlalchemy import select

from citas_bot.config import Settings
from citas_bot.domain import Appointment, AppointmentStatus, Customer
from citas_bot.intents.base import Reply
from citas_bot.observability import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from citas_bot.messaging import MetaSender

log = get_logger(__name__)


REMINDER_24H_TPL = (
    "Hola{name_part}. Te recordamos tu cita en {business_name} manana a las {hora}."
)
REMINDER_2H_TPL = (
    "Recordatorio: tu cita en {business_name} es en aprox. 2 horas (a las {hora})."
)


@dataclass(slots=True)
class ReminderJob:
    """Stateful coordinator for periodic reminder scans."""

    settings: Settings
    sender: MetaSender
    session_factory: async_sessionmaker[AsyncSession]

    async def run_once(self, *, now: datetime | None = None) -> int:
        n = now or datetime.now(UTC)
        window = timedelta(minutes=self.settings.reminder_window_minutes)
        target_24h = n + timedelta(hours=24)
        target_2h = n + timedelta(hours=2)
        sent = 0

        async with self.session_factory() as session:
            stmt = select(Appointment).where(
                Appointment.status.in_(
                    [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
                )
            )
            result = await session.execute(stmt)
            appointments = list(result.scalars().all())

            for appt in appointments:
                customer = await session.get(Customer, appt.customer_id)
                if customer is None:
                    continue

                local = appt.scheduled_at.astimezone(
                    ZoneInfo(self.settings.business_timezone)
                )
                hora = local.strftime("%H:%M")
                business_name = self.settings.business_info.name

                if not appt.reminder_24h_sent and (
                    target_24h - window <= appt.scheduled_at <= target_24h + window
                ):
                    name_part = f", {customer.name}" if customer.name else ""
                    text = REMINDER_24H_TPL.format(
                        name_part=name_part,
                        business_name=business_name,
                        hora=hora,
                    )
                    await self.sender.send(customer.whatsapp_number, Reply(text=text))
                    appt.reminder_24h_sent = True
                    sent += 1

                if not appt.reminder_2h_sent and (
                    target_2h - window <= appt.scheduled_at <= target_2h + window
                ):
                    text = REMINDER_2H_TPL.format(
                        business_name=business_name, hora=hora
                    )
                    await self.sender.send(customer.whatsapp_number, Reply(text=text))
                    appt.reminder_2h_sent = True
                    sent += 1

            await session.commit()

        log.info("reminders_scan_done", sent=sent, now=n.isoformat())
        return sent


async def scan_and_send(
    settings: Settings,
    sender: MetaSender,
    session_factory: async_sessionmaker[AsyncSession],
    *,
    now: datetime | None = None,
) -> int:
    """Run a single scan tick; returns the number of messages sent."""

    job = ReminderJob(settings=settings, sender=sender, session_factory=session_factory)
    return await job.run_once(now=now)
