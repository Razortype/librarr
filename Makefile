.PHONY: dev test test-network lint format

dev:
	overmind start

test:
	uv run pytest

test-network:
	uv run pytest -m network

lint:
	uv run ruff check .

format:
	uv run ruff format .
