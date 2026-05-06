"""Top-level Pydantic models for the Meta webhook payload.

Only the outer shell is typed in M02. The `value` of each change is left as a
generic dict and will be fully typed in M05 when the intent router needs to
inspect message content.

Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Change(BaseModel):
    """A single change inside an entry. The `value` shape depends on `field`."""

    model_config = ConfigDict(extra="allow")

    field: str
    value: dict[str, Any] = Field(default_factory=dict)


class Entry(BaseModel):
    """One Meta business account entry. Multiple changes can arrive together."""

    model_config = ConfigDict(extra="allow")

    id: str
    changes: list[Change] = Field(default_factory=list)


class WebhookPayload(BaseModel):
    """Outer envelope of every Meta webhook POST."""

    model_config = ConfigDict(extra="allow")

    object: Literal["whatsapp_business_account"] | str
    entry: list[Entry] = Field(default_factory=list)
