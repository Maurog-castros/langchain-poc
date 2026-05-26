.PHONY: setup test api docker-up docker-down frontend

setup:
	cd backend && python -m venv .venv && .venv\Scripts\pip install -r requirements.txt

test:
	cd backend && .venv\Scripts\python -m pytest

api:
	cd backend && .venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker compose -f infra/docker-compose.yml up --build

docker-down:
	docker compose -f infra/docker-compose.yml down

frontend:
	cd frontend && npm install && npm run dev
