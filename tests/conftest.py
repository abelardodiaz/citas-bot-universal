"""Shared fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from citas_bot.config import Settings, get_settings
from citas_bot.main import app


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        meta_verify_token="test-token-abc",
        meta_app_secret="test-secret-xyz",
        log_level="WARNING",
        log_format="console",
    )


@pytest.fixture
def client(test_settings: Settings) -> Iterator[TestClient]:
    app.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
