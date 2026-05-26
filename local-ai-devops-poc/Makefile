# Makefile for local-ai-devops-poc
# Usage: make <target>
# Requires: Python 3.11+, Node 18+, Docker (optional), Ollama (optional)

.PHONY: help setup setup-frontend test lint type-check \
        api frontend docker-up docker-down \
        ingest benchmark clean

# ── Default ───────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  local-ai-devops-poc — available targets"
	@echo ""
	@echo "  setup           Create .venv and install Python deps"
	@echo "  setup-frontend  npm install for frontend"
	@echo "  test            Run Python test suite"
	@echo "  lint            Run ruff linter"
	@echo "  type-check      Run pyright type checker"
	@echo "  api             Start FastAPI backend (with auto-reload)"
	@echo "  frontend        Start Vite dev server"
	@echo "  docker-up       Start API + Ollama via Docker Compose"
	@echo "  docker-down     Stop Docker Compose services"
	@echo "  ingest          Ingest data/documents into ChromaDB"
	@echo "  benchmark       Run quick benchmark against Ollama llama3.2"
	@echo "  clean           Remove .venv, __pycache__, dist, reports"
	@echo ""

# ── Python setup ──────────────────────────────────────────────────────────────
setup:
	cd backend && python -m venv .venv
	cd backend && .venv\Scripts\pip install --upgrade pip
	cd backend && .venv\Scripts\pip install -r requirements.txt
	@echo "✓ Backend ready. Copy .env.example to .env and configure."

# ── Frontend setup ────────────────────────────────────────────────────────────
setup-frontend:
	cd frontend && npm install
	@echo "✓ Frontend ready. Run: make frontend"

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	cd backend && .venv\Scripts\python -m pytest -v --tb=short

# ── Linting ───────────────────────────────────────────────────────────────────
lint:
	cd backend && .venv\Scripts\python -m ruff check app/ scripts/ --select E,W,F,I --ignore E501

# ── Type checking ─────────────────────────────────────────────────────────────
type-check:
	cd backend && .venv\Scripts\python -m pyright app/ --level warning

# ── Dev servers ───────────────────────────────────────────────────────────────
api:
	cd backend && .venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

# ── Docker ────────────────────────────────────────────────────────────────────
docker-up:
	docker compose -f infra/docker-compose.yml up --build

docker-down:
	docker compose -f infra/docker-compose.yml down

# ── Shortcuts ─────────────────────────────────────────────────────────────────
ingest:
	set PYTHONPATH=backend && python scripts\ingest_documents.py data\documents --collection local_documents

benchmark:
	set PYTHONPATH=backend && python scripts\benchmark_models.py \
		--provider ollama --model llama3.2 \
		--prompt "Explica RAG en 2 oraciones" \
		--prompt "Diagnostica latencia alta en API LLM"

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	@if exist backend\.venv rmdir /s /q backend\.venv
	@for /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@if exist frontend\dist rmdir /s /q frontend\dist
	@if exist frontend\node_modules rmdir /s /q frontend\node_modules
	@echo "✓ Cleaned"
