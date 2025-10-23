.PHONY: help install test lint format clean run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run tests with coverage
	python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

lint: ## Run linting
	flake8 src/ tests/
	mypy src/

format: ## Format code
	black src/ tests/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/

run: ## Run the application
	python src/main.py

setup: ## Initial setup (install dependencies and create directories)
	mkdir -p logs data
	pip install -r requirements.txt

activate: ## Show activation command for virtual environment
	@echo "To activate the virtual environment, run:"
	@echo "source venv/bin/activate"

coverage: ## Generate and open coverage report
	python -m pytest tests/ --cov=src --cov-report=html
	open htmlcov/index.html || xdg-open htmlcov/index.html || echo "Open htmlcov/index.html in your browser"

check-coverage: ## Check if coverage meets 80% requirement
	python -m pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80
