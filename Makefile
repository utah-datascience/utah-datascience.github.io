.PHONY: help setup serve build clean

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
