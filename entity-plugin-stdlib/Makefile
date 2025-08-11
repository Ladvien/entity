.PHONY: help install test lint format build clean docs

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests with coverage"
	@echo "  make lint       - Run linting checks"
	@echo "  make format     - Format code"
	@echo "  make build      - Build distribution packages"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make docs       - Build documentation"

install:
	poetry install

test:
	poetry run pytest --cov=src --cov-report=term-missing --cov-report=html

lint:
	poetry run ruff check .
	poetry run mypy src

format:
	poetry run black .
	poetry run ruff check --fix .

build:
	poetry build

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

docs:
	cd docs && poetry run sphinx-build -b html . _build/html

test-ci:
	poetry run pytest --cov=src --cov-report=xml --cov-report=term

publish-test:
	poetry publish -r test-pypi

publish:
	poetry publish
