# local-ai-devops-poc

PoC local-first para operar modelos LLM, RAG, benchmarking, perfiles de personalidad y artefactos sincronizados con AWS S3.

## Capacidades

- Registro de modelos locales/remotos.
- Chat vía Ollama, API local estilo OpenAI, API remota OpenAI-compatible o referencia S3.
- RAG local con `sentence-transformers` + ChromaDB sobre `.pdf`, `.txt`, `.md`.
- Upload/download de modelos, datasets, documentos y reportes en S3.
- Benchmark básico por modelo y prompt.
- Evaluación simple de personalidad de chatbot.
- Preparación de comando LoRA/fine-tuning en modo dry-run.
- Backend FastAPI, scripts CLI, Docker, Makefile y CI GitHub Actions.

## Requisitos

- Python 3.11+
- Docker Desktop opcional
- Ollama opcional para inferencia local
- AWS CLI configurado si usas S3/ECR/CloudWatch/SSM

## Setup local

```powershell
cd C:\DEV\langchain-poc\local-ai-devops-poc
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\uvicorn app.main:app --reload
```

Health:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Ollama:

```powershell
ollama pull llama3.2
Invoke-RestMethod http://localhost:8000/chat -Method Post -ContentType application/json -Body '{
  "provider":"ollama",
  "model":"llama3.2",
  "prompt":"Resume riesgos de importar carga FCL China a Chile",
  "temperature":0.2
}'
```

## CLI

Ejecutar desde raíz del proyecto con `PYTHONPATH=backend`:

```powershell
$env:PYTHONPATH="backend"
python scripts\benchmark_models.py --provider ollama --model llama3.2 --prompt "Plan DevOps para RAG local"
python scripts\ingest_documents.py data\documents --collection ops_docs
python scripts\run_finetune_lora.py --base-model mistral --dataset-path data\datasets\train.jsonl
python scripts\upload_model_to_s3.py models\adapter.bin --kind model --key local-ai-devops-poc/model/adapter.bin
```

## API principal

- `GET /health`
- `POST /chat`
- `POST /chat/personality`
- `POST /models/register`
- `GET /models`
- `POST /models/s3/upload`
- `POST /models/s3/download`
- `POST /rag/ingest`
- `POST /rag/query`
- `POST /benchmark`
- `POST /fine-tuning/prepare`

## Seguridad

- No secrets en Git.
- `.env` ignorado.
- Modelos/datasets/reportes fuera del repo.
- IAM mínimo en `infra/iam-policy-s3-minimal.json`.
- Variables por ambiente: local/dev/prod.

## Costos AWS

- S3 cobra almacenamiento, requests y transferencia.
- ECR cobra almacenamiento de imágenes.
- CloudWatch cobra ingestión, retención y consultas de logs.
- ECS/Lambda cobra cómputo y red.
- Secrets Manager cobra por secreto; SSM Parameter Store estándar suele ser más barato.

## Validación edge cases

- Probar `S3_BUCKET` vacío: upload debe fallar con error claro.
- Probar Ollama apagado: benchmark marca `ok=false`.
- Probar PDFs sin texto: RAG ingesta `0` chunks.
- Probar `top_k` alto: Pydantic limita a `20`.
- Probar respuesta con frase prohibida: personalidad debe fallar.

Más detalle: `docs/`.
