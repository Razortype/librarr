.PHONY: dev test lint format

dev:
	overmind start

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .
