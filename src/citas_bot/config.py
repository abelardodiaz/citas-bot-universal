"""Application settings, sourced from environment variables."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Values are read from environment variables (or a .env file) with the
    matching uppercase names. See `.env.example` for the canonical list.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="citas-bot-universal")
    log_level: str = Field(default="INFO")
    log_format: Literal["console", "json"] = Field(default="console")

    meta_verify_token: str = Field(default="change-me", min_length=1)
    meta_app_secret: str = Field(default="change-me", min_length=1)
    meta_phone_number_id: str = Field(default="")
    meta_access_token: str = Field(default="")

    business_name: str = Field(default="Demo Business")
    business_timezone: str = Field(default="America/Mexico_City")
    appointment_duration_minutes: int = Field(default=30, ge=5, le=480)


def get_settings() -> Settings:
    """Return a fresh Settings instance.

    Tests can monkeypatch environment variables and call this to get an
    isolated configuration.
    """

    return Settings()
