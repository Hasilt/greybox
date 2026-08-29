API ?= http://localhost:8000

.PHONY: up down logs build test ingest query evaluate drift drift-simulate drift-check reindex

up:  ## Build and start the full stack
	docker compose up --build -d
	@echo "backend:  $(API)/docs"
	@echo "dashboard: http://localhost:5173"

down:  ## Stop the stack
	docker compose down

logs:  ## Tail all service logs
	docker compose logs -f

build:  ## Build images only
	docker compose build

test:  ## Run the backend test suite inside the backend image
	docker compose run --rm --no-deps backend pytest -q

ingest:  ## Ingest documents from data/documents
	curl -s -X POST $(API)/api/ingest | python3 -m json.tool

query:  ## Example query (override: make query Q="...")
	curl -s -X POST $(API)/api/query -H 'content-type: application/json' \
		-d '{"query": "$(or $(Q),How does Redis expiration work?)", "top_k": 5}' | python3 -m json.tool

evaluate:  ## Run retrieval evaluation (Hit@5)
	curl -s -X POST $(API)/api/evaluation/run | python3 -m json.tool

drift:  ## Show current drift score
	curl -s $(API)/api/drift | python3 -m json.tool

drift-simulate:  ## Inject an off-topic document to shift the embedding distribution
	curl -s -X POST $(API)/api/drift/simulate | python3 -m json.tool

drift-check:  ## Check drift and auto-reindex if over threshold
	curl -s -X POST $(API)/api/drift/check | python3 -m json.tool

reindex:  ## Re-run ingestion (also recomputes the baseline centroid)
	curl -s -X POST $(API)/api/ingest | python3 -m json.tool

metrics:  ## Show query metrics
	curl -s $(API)/api/metrics | python3 -m json.tool
