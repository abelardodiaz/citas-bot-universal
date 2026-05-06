"""Customer DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreate(BaseModel):
    whatsapp_number: str = Field(min_length=8, max_length=32)
    name: str | None = Field(default=None, max_length=120)
    locale: str = Field(default="es-MX", max_length=10)


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    whatsapp_number: str
    name: str | None
    locale: str
    created_at: datetime
    updated_at: datetime
