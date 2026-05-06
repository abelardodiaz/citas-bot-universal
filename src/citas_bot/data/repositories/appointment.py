"""AppointmentRepository: queries scoped to the Appointment aggregate."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from citas_bot.domain import Appointment, AppointmentStatus


class AppointmentRepository:
    """Read/write operations for Appointment."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, appointment: Appointment) -> Appointment:
        self._session.add(appointment)
        await self._session.flush()
        return appointment

    async def get(self, appointment_id: str) -> Appointment | None:
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_customer(
        self,
        customer_id: str,
        statuses: list[AppointmentStatus] | None = None,
    ) -> list[Appointment]:
        stmt = select(Appointment).where(Appointment.customer_id == customer_id)
        if statuses:
            stmt = stmt.where(Appointment.status.in_(statuses))
        stmt = stmt.order_by(Appointment.scheduled_at)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_in_window(
        self,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[Appointment]:
        stmt = (
            select(Appointment)
            .where(Appointment.scheduled_at >= start_utc)
            .where(Appointment.scheduled_at < end_utc)
            .order_by(Appointment.scheduled_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        appointment_id: str,
        new_status: AppointmentStatus,
    ) -> Appointment | None:
        appointment = await self.get(appointment_id)
        if appointment is None:
            return None
        appointment.status = new_status
        await self._session.flush()
        return appointment
