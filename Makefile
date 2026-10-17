.DEFAULT_GOAL := help

DEMO_PASSWORD ?= $(OTARM_DEMO_PASSWORD)
FRONTEND_HOST ?= 127.0.0.1
FRONTEND_PORT ?= 5173
BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8000

.PHONY: help install frontend-install backend-install dev frontend backend require-demo-password test test-frontend test-backend test-integration typecheck build

help: ## Show the available commands
	@echo "OTARM development commands"
	@echo ""
	@echo "  make install                 Install frontend and backend dependencies"
	@echo "  make dev DEMO_PASSWORD=...   Run frontend and backend together"
	@echo "  make frontend                Run only the Vite frontend"
	@echo "  make backend DEMO_PASSWORD=...  Run only the FastAPI backend"
	@echo "  make test                    Run all frontend and backend tests"
	@echo "  make test-integration        Run isolated Docker Compose integration tests"
	@echo "  make typecheck               Run the frontend TypeScript check"
	@echo "  make build                   Build the frontend and compile the backend"
	@echo ""
	@echo "Optional: FRONTEND_PORT=5173 BACKEND_PORT=8000"

install: frontend-install backend-install ## Install all dependencies

frontend-install: ## Install frontend dependencies
	npm --prefix frontend install

backend-install: ## Create the backend environment and install dependencies
	cd backend && uv sync --dev

dev: require-demo-password ## Run the frontend and backend concurrently
	$(MAKE) --no-print-directory -j2 frontend backend DEMO_PASSWORD="$(DEMO_PASSWORD)"

frontend: ## Run the Vite development server
	npm --prefix frontend run dev -- --host $(FRONTEND_HOST) --port $(FRONTEND_PORT)

backend: require-demo-password ## Run the FastAPI development server
	cd backend && OTARM_DEMO_PASSWORD="$(DEMO_PASSWORD)" uv run python -m uvicorn app.main:app --reload --host $(BACKEND_HOST) --port $(BACKEND_PORT)

require-demo-password:
	@if [ -z "$(DEMO_PASSWORD)" ]; then \
		echo "DEMO_PASSWORD is required. Example: make dev DEMO_PASSWORD='choose-a-local-password'"; \
		exit 1; \
	fi

test: test-frontend test-backend ## Run every test suite

test-frontend: ## Run frontend tests
	npm --prefix frontend test

test-backend: ## Run backend tests
	cd backend && uv run python -m pytest

test-integration: ## Build and test an isolated Docker Compose stack
	cd backend && uv run python -m pytest -m integration

typecheck: ## Type-check the frontend
	npm --prefix frontend run typecheck

build: ## Build frontend assets and compile backend Python modules
	npm --prefix frontend run build
	cd backend && uv run python -m compileall -q app tests
