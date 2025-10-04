.PHONY: help docs
.DEFAULT_GOAL := help

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: ## Removing cached python compiled files
	find . -name "*.pyc" -type f -delete
	find . -name "*.pyo" -type f -delete
	find . -name "*~" -type f -delete
	find . -name __pycache__  | xargs  rm -rfv
	find . -name .pytest_cache  | xargs  rm -rfv
	find . -name .ruff_cache  | xargs  rm -rfv
	find . -name .mypy_cache  | xargs  rm -rfv

install: ## Install dependencies
	pip install -r requirements.txt
	flit install --symlink

install-full: ## Install dependencies
	make install
	pre-commit install -f

lint:fmt ## Run code linters
	ruff check ellar_sql tests
	mypy ellar_sql

fmt format:clean ## Run code formatters
	ruff format ellar_sql tests samples
	ruff check --fix ellar_sql tests samples

test:clean ## Run tests
	pytest

test-cov:clean ## Run tests with coverage
	pytest --cov=ellar_sql --cov-report term-missing

pre-commit-lint: ## Runs Requires commands during pre-commit
	make clean
	make fmt
	make lint

doc-deploy:clean ## Run Deploy Documentation
	mkdocs gh-deploy --force --ignore-version

doc-serve: ## Launch doc local server
	mkdocs serve
