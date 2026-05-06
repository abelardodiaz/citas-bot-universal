"""Tests for the data CLI (init-db / seed)."""

from __future__ import annotations

from pathlib import Path

import pytest

from citas_bot.data import cli
from citas_bot.data.db import reset_engine


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_file}")
    reset_engine()


def test_main_no_args_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    code = cli.main([])
    assert code == 2
    assert "usage" in capsys.readouterr().out.lower()


def test_main_unknown_command_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    code = cli.main(["bogus"])
    assert code == 2
    assert "unknown" in capsys.readouterr().out.lower()


def test_init_db_creates_schema() -> None:
    code = cli.main(["init-db"])
    assert code == 0


def test_seed_inserts_demo_data_after_init() -> None:
    cli.main(["init-db"])
    code = cli.main(["seed"])
    assert code == 0
