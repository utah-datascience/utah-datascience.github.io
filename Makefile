.PHONY: help setup serve build clean talks talks-check import-talks sync-talks sync-talks-dry-run test-talks

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Utah Center for Data Science - Jekyll Site"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

setup: ## Install Ruby dependencies
	bundle install

serve: ## Start the Jekyll development server
	bundle exec jekyll serve

build: ## Build the site for production
	bundle exec jekyll build

clean: ## Remove generated site files
	rm -rf _site .jekyll-cache

talks: ## Generate the talk pages in _talks/ from _data/talks/*.toml
	python3 scripts/generate_talks.py

talks-check: ## Verify the talk pages match _data/talks/*.toml (used by CI)
	python3 scripts/generate_talks.py --check

import-talks: ## Seed new talk records from the seminar Google Calendar (one-off backfill)
	python3 scripts/import_calendar_talks.py

sync-talks: ## Sync in-window talk records from Google Calendar (create/update/delete)
	python3 scripts/import_calendar_talks.py --sync

sync-talks-dry-run: ## Preview what sync-talks would change, without writing anything
	python3 scripts/import_calendar_talks.py --sync --dry-run

test-talks: ## Run the calendar-parsing test fixtures
	python3 scripts/test_calendar_parsing.py
