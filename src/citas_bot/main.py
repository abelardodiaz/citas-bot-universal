"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from citas_bot import __version__
from citas_bot.config import get_settings
from citas_bot.observability import configure_logging, get_logger
from citas_bot.webhooks import router as webhook_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(level=settings.log_level, format=settings.log_format)
    log = get_logger(__name__)
    log.info("app_starting", app=settings.app_name, version=__version__)
    yield
    log.info("app_stopping")


app = FastAPI(
    title="citas-bot-universal",
    version=__version__,
    description="Template Python para asistentes WhatsApp de citas.",
    lifespan=lifespan,
)

app.include_router(webhook_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness probe. Returns ``{"status": "ok"}`` when the app is running."""

    return {"status": "ok"}
