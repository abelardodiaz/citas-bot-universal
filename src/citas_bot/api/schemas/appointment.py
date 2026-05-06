"""Appointment DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from citas_bot.domain import AppointmentStatus


class AppointmentCreate(BaseModel):
    customer_id: str = Field(min_length=36, max_length=36)
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=5, le=480)
    notes: str | None = Field(default=None, max_length=500)


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    scheduled_at: datetime
    duration_minutes: int
    status: AppointmentStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime
