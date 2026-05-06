"""CustomerRepository: queries scoped to the Customer aggregate."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from citas_bot.domain import Customer


class CustomerRepository:
    """Read/write operations for Customer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_whatsapp(self, whatsapp_number: str) -> Customer | None:
        stmt = select(Customer).where(Customer.whatsapp_number == whatsapp_number)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        whatsapp_number: str,
        name: str | None = None,
        locale: str = "es-MX",
    ) -> Customer:
        existing = await self.get_by_whatsapp(whatsapp_number)
        if existing is not None:
            return existing
        customer = Customer(whatsapp_number=whatsapp_number, name=name, locale=locale)
        self._session.add(customer)
        await self._session.flush()
        return customer

    async def add(self, customer: Customer) -> Customer:
        self._session.add(customer)
        await self._session.flush()
        return customer
