.PHONY: help setup serve build clean talks talks-check import-talks

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

import-talks: ## Seed new talk records from the seminar Google Calendar
	python3 scripts/import_calendar_talks.py
