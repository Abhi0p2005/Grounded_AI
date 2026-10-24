.PHONY: help dev test lint ingest eval clean

help:
	@echo "GroundedAI - Available commands:"
	@echo "  make dev          - Start all services with docker compose"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run ruff linting and formatting checks"
	@echo "  make ingest WS=<workspace>  - Ingest documents for a workspace"
	@echo "  make eval WS=<workspace>    - Run evaluation for a workspace"
	@echo "  make clean        - Stop services and clean volumes"

dev:
	docker compose up --build

test:
	cd backend && pytest -q -m "not live"

lint:
	cd backend && ruff check . && ruff format --check .

ingest:
	@if [ -z "$(WS)" ]; then echo "Usage: make ingest WS=workspace-name"; exit 1; fi
	cd backend && python ../scripts/ingest.py --workspace $(WS)

eval:
	@if [ -z "$(WS)" ]; then echo "Usage: make eval WS=workspace-name"; exit 1; fi
	cd backend && python ../scripts/run_eval.py --workspace $(WS)

clean:
	docker compose down -v
