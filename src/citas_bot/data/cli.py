"""Tiny CLI for database management without leaving the project."""

from __future__ import annotations

import asyncio
import sys
from datetime import timedelta

from citas_bot.config import get_settings
from citas_bot.data.db import get_engine, get_session_maker, reset_engine
from citas_bot.domain import (
    Appointment,
    AppointmentStatus,
    Base,
    Conversation,
    Customer,
)
from citas_bot.domain.base import utc_now


async def init_db() -> None:
    """Create all tables (skips Alembic, suitable for tests / quick start)."""

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_demo() -> None:
    """Insert a small set of demo records to play with the bot locally."""

    maker = get_session_maker()
    async with maker() as session:
        ana = Customer(whatsapp_number="+5215551234567", name="Ana", locale="es-MX")
        beto = Customer(whatsapp_number="+5215557654321", name="Beto", locale="es-MX")
        session.add_all([ana, beto])
        await session.flush()

        now = utc_now()
        session.add_all(
            [
                Appointment(
                    customer_id=ana.id,
                    scheduled_at=now + timedelta(days=1),
                    duration_minutes=30,
                    status=AppointmentStatus.SCHEDULED,
                ),
                Appointment(
                    customer_id=ana.id,
                    scheduled_at=now + timedelta(days=8),
                    duration_minutes=30,
                    status=AppointmentStatus.CONFIRMED,
                ),
                Appointment(
                    customer_id=beto.id,
                    scheduled_at=now + timedelta(days=2),
                    duration_minutes=45,
                    status=AppointmentStatus.SCHEDULED,
                ),
            ]
        )
        session.add(Conversation(customer_id=ana.id, slots_filled={}))
        await session.commit()


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python -m citas_bot.data.cli {init-db|seed}")
        return 2

    command = args[0]
    settings = get_settings()
    print(f"db: {settings.database_url}")
    reset_engine()

    if command == "init-db":
        asyncio.run(init_db())
        print("schema created")
        return 0
    if command == "seed":
        asyncio.run(seed_demo())
        print("demo data inserted")
        return 0

    print(f"unknown command: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
