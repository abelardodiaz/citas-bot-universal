"""Pydantic DTO instantiation tests."""

from __future__ import annotations

from datetime import datetime, timezone

from citas_bot.api.schemas import (
    AppointmentCreate,
    AppointmentRead,
    CustomerCreate,
    CustomerRead,
)
from citas_bot.domain import AppointmentStatus


def test_customer_create_minimum() -> None:
    c = CustomerCreate(whatsapp_number="+5215551112233")
    assert c.locale == "es-MX"
    assert c.name is None


def test_customer_read_round_trip() -> None:
    now = datetime.now(timezone.utc)
    c = CustomerRead(
        id="abc",
        whatsapp_number="+5215551112233",
        name="Ana",
        locale="es-MX",
        created_at=now,
        updated_at=now,
    )
    assert c.id == "abc"


def test_appointment_create_defaults() -> None:
    a = AppointmentCreate(
        customer_id="x" * 36,
        scheduled_at=datetime.now(timezone.utc),
    )
    assert a.duration_minutes == 30
    assert a.notes is None


def test_appointment_read_with_status() -> None:
    now = datetime.now(timezone.utc)
    a = AppointmentRead(
        id="x",
        customer_id="y",
        scheduled_at=now,
        duration_minutes=45,
        status=AppointmentStatus.CONFIRMED,
        notes="vip",
        created_at=now,
        updated_at=now,
    )
    assert a.status == AppointmentStatus.CONFIRMED
