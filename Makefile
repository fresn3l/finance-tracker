.PHONY: help install install-dev test lint format type-check clean run

help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make type-check   - Run type checker"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make run          - Run the application"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install pre-commit
	pre-commit install

test:
	pytest

lint:
	ruff check finance_tracker tests
	mypy finance_tracker

format:
	black finance_tracker tests
	ruff check --fix finance_tracker tests

type-check:
	mypy finance_tracker

clean:
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

run:
	python -m finance_tracker.cli

