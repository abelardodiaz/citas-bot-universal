.PHONY: install test lint format run clean

install:
	uv sync --all-extras

test:
	uv run pytest

lint:
	uv run ruff check src tests
	uv run mypy src

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

run:
	uv run uvicorn citas_bot.main:app --reload --host 0.0.0.0 --port 8000

clean:
	rm -rf .ruff_cache .mypy_cache .pytest_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
