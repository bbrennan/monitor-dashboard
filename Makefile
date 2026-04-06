.PHONY: install test lint format run clean check

## Install dependencies with uv
install:
	uv sync

## Run pytest (excludes slow tests)
test:
	uv run pytest tests/ -m "not slow" -v

## Run all tests including slow
test-all:
	uv run pytest tests/ -v

## Ruff lint check + format check
lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

## Auto-format with ruff
format:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

## Run lint + tests
check: lint test

## Launch dashboard locally
run:
	uv run streamlit run src/monitor_dashboard/app.py

## Remove build artifacts
clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
