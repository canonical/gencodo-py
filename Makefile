# SPDX-License-Identifier: LGPL-3.0-only
# Copyright 2026 Canonical Ltd.

.PHONY: all install test test-coverage lint format typecheck reuse examples build clean release help

UV ?= uv
RUN := $(UV) run

# Default target
all: lint typecheck test

# Install the project and development tools into .venv
install:
	@echo "Syncing development environment..."
	@$(UV) sync --group dev

# Run tests
test:
	@echo "Running tests..."
	@$(RUN) pytest -q

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage..."
	@$(RUN) pytest -q --cov=gencodo --cov-report=term-missing --cov-report=xml --cov-report=html
	@echo "Coverage report generated: htmlcov/index.html"

# Lint with ruff (configuration in pyproject.toml)
lint:
	@echo "Running ruff..."
	@$(RUN) ruff check src tests examples
	@$(RUN) ruff format --check src tests examples

# Format code with ruff
format:
	@echo "Formatting code..."
	@$(RUN) ruff check --fix src tests examples
	@$(RUN) ruff format src tests examples

# Type-check with mypy
typecheck:
	@echo "Running mypy..."
	@$(RUN) mypy

# Check REUSE (license and copyright) compliance
reuse:
	@echo "Running reuse lint..."
	@$(RUN) reuse lint

# Regenerate the demo output committed under examples/demo_cli/docs_output
examples:
	@echo "Regenerating example output..."
	@$(RUN) python examples/demo_cli/generate_docs.py

# Build sdist and wheel into dist/
build:
	@echo "Building..."
	@$(UV) build

# Clean build and test artifacts
clean:
	@echo "Cleaning..."
	@rm -rf dist build htmlcov coverage.xml .coverage .pytest_cache .mypy_cache .ruff_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} +

# Release a new version (requires VERSION=vX.Y.Z matching src/gencodo/__init__.py and a
# CHANGELOG.md section). Pushing the tag triggers .github/workflows/publish.yml, which
# publishes to PyPI and creates the GitHub release with the CHANGELOG section as notes.
release:
ifndef VERSION
	@echo "Error: VERSION is required. Usage: make release VERSION=v0.4.0"
	@exit 1
endif
	@echo "Checking version format..."
	@if ! echo "$(VERSION)" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+$$'; then \
		echo "Error: VERSION must follow format vX.Y.Z (e.g., v0.4.0)"; \
		exit 1; \
	fi
	@echo "Checking __version__ matches $(VERSION)..."
	@if ! grep -qE '^__version__ = "$(VERSION:v%=%)"$$' src/gencodo/__init__.py; then \
		echo "Error: src/gencodo/__init__.py __version__ is not $(VERSION:v%=%)"; \
		exit 1; \
	fi
	@echo "Checking CHANGELOG.md has a section for $(VERSION)..."
	@if ! grep -qE '^## \[$(VERSION:v%=%)\] - [0-9]{4}-[0-9]{2}-[0-9]{2}$$' CHANGELOG.md; then \
		echo "Error: CHANGELOG.md has no '## [$(VERSION:v%=%)] - YYYY-MM-DD' section"; \
		exit 1; \
	fi
	@echo "Checking working tree is clean..."
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: commit or stash your changes before releasing"; \
		exit 1; \
	fi
	@echo "Running checks before release..."
	@$(MAKE) all
	@echo "Creating tag $(VERSION)..."
	@git tag -a $(VERSION) -m "Release $(VERSION)"
	@echo "Pushing tag $(VERSION) to origin..."
	@git push origin $(VERSION)
	@echo "Release $(VERSION) tagged; the publish workflow uploads to PyPI and creates the GitHub release."

# Show help
help:
	@echo "Available targets:"
	@echo "  all            - Lint, type-check, and test (default)"
	@echo "  install        - Sync the development environment (uv)"
	@echo "  test           - Run tests"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  lint           - Run ruff check and format check"
	@echo "  format         - Apply ruff fixes and formatting"
	@echo "  typecheck      - Run mypy"
	@echo "  reuse          - Check REUSE license/copyright compliance"
	@echo "  examples       - Regenerate examples/demo_cli/docs_output"
	@echo "  build          - Build sdist and wheel"
	@echo "  clean          - Remove build and test artifacts"
	@echo "  release        - Tag and push a release (requires VERSION=vX.Y.Z)"
	@echo "  help           - Show this help message"
