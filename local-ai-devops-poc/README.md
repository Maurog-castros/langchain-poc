# local-ai-devops-poc

> **PoC local-first para equipos DevOps**: orquesta modelos LLM descargados localmente, implementa RAG sobre documentos propios, mide latencia entre proveedores y sincroniza artefactos con AWS S3.

[![CI](https://github.com/tu-org/langchain-poc/actions/workflows/ci.yml/badge.svg)](./infra/github-actions-ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue)

---

## Capacidades

| Feature | Descripción |
|---|---|
| 🤖 **Multi-provider chat** | Ollama, API local (LM Studio/vLLM), OpenAI-compatible remoto |
| 📚 **RAG local** | Ingesta PDF/TXT/MD → embeddings → ChromaDB → respuesta con contexto |
| 📊 **Benchmark** | Mide latencia y calidad de respuestas entre modelos y prompts |
| 🎭 **Evaluación de personalidad** | Verifica que agentes sigan perfiles definidos (must_say / must_avoid) |
| ⚗️ **Fine-tuning / LoRA** | Prepara comandos LoRA sin ejecutar (dry_run) |
| ☁️ **S3 sync** | Upload/download/listing de modelos, datasets, documentos y reportes |
| 🐳 **Docker + Compose** | API + Ollama listos en un comando |
| 🔄 **CI/CD** | GitHub Actions pipeline (lint, type check, test, build) |

---

## Setup local rápido

### 1. Backend (Python)

```powershell
cd C:\DEV\langchain-poc\local-ai-devops-poc\backend

# Crear virtual environment
python -m venv .venv
.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt

# Configurar entorno
Copy-Item .env.example .env
# Editar .env con tu S3_BUCKET, OLLAMA_BASE_URL, etc.

# Iniciar API
.\.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Verificar:**
```powershell
Invoke-RestMethod http://localhost:8000/health
# → {"status":"ok","app":"local-ai-devops-poc","environment":"local","integrations":{...}}
```

### 2. Frontend (TypeScript + Vite)

```powershell
cd C:\DEV\langchain-poc\local-ai-devops-poc\frontend
npm install
npm run dev
# → http://localhost:5173
```

### 3. Con Docker Compose (API + Ollama)

```powershell
cd C:\DEV\langchain-poc\local-ai-devops-poc
docker compose -f infra/docker-compose.yml up --build
# Ollama: http://localhost:11434
# API:    http://localhost:8000
```

---

## Requisitos

| Componente | Versión mínima | Notas |
|---|---|---|
| Python | 3.11+ | 3.12 recomendado |
| Node.js | 18+ | Para frontend |
| Docker Desktop | Cualquier reciente | Para compose |
| Ollama | 0.1.x+ | Para inferencia local |
| AWS CLI | 2.x | Solo si usas S3/ECR/SSM |

---

## API Endpoints

| Método | Path | Descripción |
|---|---|---|
| GET | `/health` | Estado de API, Ollama, S3 y ChromaDB |
| POST | `/chat` | Chat con cualquier provider |
| POST | `/chat/personality` | Evalúa respuesta contra perfil de personalidad |
| POST | `/models/register` | Registra modelo en registry in-memory |
| GET | `/models` | Lista modelos registrados |
| POST | `/models/s3/upload` | Sube artefacto local a S3 |
| POST | `/models/s3/download` | Descarga objeto S3 localmente |
| GET | `/models/s3/list` | Lista objetos en prefijo del proyecto |
| POST | `/rag/ingest` | Ingesta documentos en ChromaDB |
| POST | `/rag/query` | Consulta RAG (con o sin LLM) |
| POST | `/benchmark` | Benchmark multi-modelo |
| POST | `/fine-tuning/prepare` | Prepara comando LoRA |

**Swagger UI:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc

---

## CLI Scripts

Ejecutar desde la raíz con `PYTHONPATH=backend`:

```powershell
$env:PYTHONPATH = "backend"

# Benchmark
python scripts\benchmark_models.py `
  --provider ollama --model llama3.2 `
  --prompt "Plan DevOps para RAG local" `
  --prompt "Diagnostica latencia en API"

# Ingestar documentos
python scripts\ingest_documents.py data\documents --collection ops_docs

# Fine-tuning LoRA (dry-run)
python scripts\run_finetune_lora.py `
  --base-model mistral `
  --dataset-path data\datasets\train.jsonl `
  --output-dir artifacts\lora

# Upload a S3
python scripts\upload_model_to_s3.py `
  models\adapter.bin --kind model --key local-ai-devops-poc/models/adapter.bin

# Download desde S3
python scripts\download_model_from_s3.py `
  local-ai-devops-poc/models/adapter.bin --local-path models\adapter.bin
```

---

## Tests

```powershell
cd backend
.\.venv\Scripts\python -m pytest -v
```

Tests incluidos:

- `test_health.py` — health endpoint con integraciones mockeadas
- `test_personality.py` — evaluación de perfil de personalidad
- `test_model_router.py` — routing de providers (mocks HTTP)
- `test_benchmark.py` — estadísticas y manejo de errores
- `test_security.py` — path traversal y seguridad de rutas

---

## Seguridad

- ❌ **No hay secretos en código** — todo por env vars / SSM
- ✅ **.env ignorado por Git** — solo `.env.example` committeado
- ✅ **Mínimo privilegio IAM** — ver `infra/iam-policy-s3-minimal.json`
- ✅ **Path traversal bloqueado** — `ensure_child_path()` en toda operación de archivos
- ✅ **Separación local/dev/prod** — variable `APP_ENV`

---

## Costos AWS estimados (PoC)

| Servicio | Costo aproximado |
|---|---|
| S3 storage | ~$0.023/GB/mes |
| S3 PUT requests | $0.005/1,000 |
| S3 GET requests | $0.0004/1,000 |
| ECR storage | $0.10/GB/mes |
| CloudWatch Logs ingestión | $0.50/GB |
| ECS Fargate (0.25 vCPU / 0.5 GB) | ~$10-15/mes continuo |
| SSM Parameter Store (SecureString) | $0.05/param/mes |

> ⚠️ Para una PoC con uso esporádico, el costo total es **< $5/mes** si Fargate no corre continuamente.

---

## Documentación adicional

| Doc | Contenido |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Diagrama de componentes y flujos |
| [`docs/AWS_SETUP.md`](docs/AWS_SETUP.md) | S3, IAM, ECR, ECS, SSM paso a paso |
| [`docs/RAG.md`](docs/RAG.md) | Diseño del pipeline RAG y tuning |
| [`docs/FINE_TUNING.md`](docs/FINE_TUNING.md) | LoRA, datasets y stack de training |
| [`docs/BENCHMARKING.md`](docs/BENCHMARKING.md) | Metodología y métricas |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | Troubleshooting y operación día 2 |
| [`infra/aws-cli-examples.md`](infra/aws-cli-examples.md) | Comandos AWS CLI de referencia |

---

## Validación de edge cases

```powershell
# S3_BUCKET vacío → debe fallar con mensaje claro
Invoke-RestMethod http://localhost:8000/models/s3/list
# → {"detail":"S3_BUCKET environment variable is required..."}

# Ollama apagado → benchmark marca ok=false
# RAG con PDF sin texto → ingesta 0 chunks
# top_k > 20 → Pydantic rechaza con error de validación
# Frase prohibida en respuesta de personalidad → score bajo 0.75
```
