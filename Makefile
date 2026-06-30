# NHL Fan Insights — monorepo task runner.
# Polyglot stack: FastAPI backend (Python), Next.js frontend, Go prospect-service.
# Run `make help` for the list.

.DEFAULT_GOAL := help
.PHONY: help up down logs build migrate test test-backend test-go test-frontend \
        lint lint-go proto proto-go proto-py proto-lint clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ── Local stack (docker compose) ─────────────────────────────────────────────
up: ## Start the full stack (postgres, redis, backend, frontend, prospect-service)
	docker compose up -d --build

down: ## Stop the stack (keeps volumes)
	docker compose down

logs: ## Tail all service logs
	docker compose logs -f

build: ## Rebuild all images without starting
	docker compose build

migrate: ## Apply backend DB migrations (prospect-service self-migrates on boot)
	docker exec nhl-backend alembic upgrade head

# ── Tests ────────────────────────────────────────────────────────────────────
test: test-backend test-go ## Run all backend + Go tests

test-backend: ## Run backend pytest suite
	cd backend && pytest -v

test-go: ## Run prospect-service Go tests
	cd prospect-service && go test ./...

test-frontend: ## Build the frontend (type-check + compile)
	cd frontend && npm run build

# ── Lint ─────────────────────────────────────────────────────────────────────
lint: lint-go ## Run linters (frontend lint + go vet)
	cd frontend && npm run lint

lint-go: ## go vet the prospect-service
	cd prospect-service && go vet ./...

# ── Protobuf codegen ─────────────────────────────────────────────────────────
proto: proto-go proto-py ## Regenerate Go + Python stubs from proto/

proto-go: ## Generate Go stubs (buf → prospect-service/internal/gen)
	cd proto && buf generate

proto-py: ## Generate Python stubs (grpc_tools → backend/app/grpc_gen)
	cd proto && python -m grpc_tools.protoc -I. \
		--python_out=../backend/app/grpc_gen \
		--grpc_python_out=../backend/app/grpc_gen \
		--pyi_out=../backend/app/grpc_gen \
		prospects/v1/prospects.proto

proto-lint: ## Lint proto definitions
	cd proto && buf lint

clean: ## Remove local build/test caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.pytest_cache frontend/.next
