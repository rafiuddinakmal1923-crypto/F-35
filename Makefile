# VoltGuard AI R0. Windows users: use make.ps1 (same targets), or run this from Git Bash/WSL.
# Commands run inside the api container by default; LOCAL=1 runs them with ./.venv instead.

SHELL := /bin/bash
COMPOSE := docker compose
DATASET ?=
ifeq ($(LOCAL),1)
PY := cd backend && ../.venv/bin/python
else
PY := $(COMPOSE) run --rm api python
endif

.PHONY: help setup up down build logs migrate seed simulate train tune simreport pipeline ingest \
        models fetch test demo tunnel tunnel-named snapshot backtest web handoff venv

help:
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

setup: ## Create .env with generated secrets and the DATA_ROOT folders
	python3 scripts/setup_env.py $(if $(filter 1,$(LOCAL)),--local,)

venv: ## LOCAL=1 only: create ./.venv with the backend requirements
	python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt

build: ## Build the containers
	$(COMPOSE) build

up: ## Start the lite profile (db, api, web, ollama, proxy) on http://localhost:8080
	$(COMPOSE) up -d

down: ## Stop everything (data stays in the named volume and DATA_ROOT)
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100 api

migrate: ## Create or update the database schema, roles and row-level security
	$(PY) -m voltguard migrate

seed: ## Demo accounts (passwords into .env), demo simulation, closed cases, RAG documents
	$(PY) -m voltguard seed

simulate: ## Simulate the demo zones into DATA_ROOT/simulated/demo
	$(PY) -m voltguard simulate --run demo

train: ## Train the pattern model and the autoencoder
	$(PY) -m voltguard train-models

tune: ## Tune score weights on the tuning split only (writes config/tuned_weights.yaml)
	$(PY) -m voltguard tune

simreport: ## Write reports/simulation_report.md
	$(PY) -m voltguard simreport

pipeline: ## Load the active sources (config/data_sources.yaml) and run detection (no cases)
	$(PY) -m voltguard pipeline

ingest: ## Validate and load an uploaded dataset: make ingest DATASET=<name>
	@test -n "$(DATASET)" || (echo "usage: make ingest DATASET=<dataset_name>" && exit 1)
	$(PY) -m voltguard ingest $(DATASET)

fetch: ## Try to download the public datasets; prints manual steps when a download fails
	$(PY) /app/scripts/fetch_datasets.py || python3 scripts/fetch_datasets.py

models: ## Pull the language model into OLLAMA_MODELS and the embedding model into HF_HOME
	$(COMPOSE) exec ollama ollama pull $${LLM_MODEL:-qwen2.5:7b-instruct}
	$(PY) -m voltguard fetch-models

test: ## Run the test suite (unit, integration, agent safety)
	$(PY) -m pytest

demo: ## Fresh setup, seed, detection run and the printed 7-step demo script
	$(MAKE) setup
	$(COMPOSE) up -d --build
	$(PY) -m voltguard migrate
	$(PY) -m voltguard demo

tunnel: ## Quick Cloudflare tunnel (random address); writes PUBLIC_BASE_URL into .env
	bash scripts/tunnel.sh quick

tunnel-named: ## Named Cloudflare tunnel with a stable hostname (deploy/cloudflared/config.yml)
	bash scripts/tunnel.sh named

snapshot: ## Export the rpt_ views to CSV for Power BI (powerbi/snapshot/)
	$(PY) -m voltguard snapshot

backtest: ## Day-by-day back-test on simulated history (R1 rehearsal)
	$(PY) /app/scripts/backtest.py

web: ## Build the web app locally (needs Node 20+)
	cd web && npm ci && npm run build

handoff: ## Rebuild the graphify code graph and HANDOFF.md for the next session
	bash scripts/handoff.sh
