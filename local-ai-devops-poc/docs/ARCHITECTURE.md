# Architecture — local-ai-devops-poc

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite, port 5173)                         │
│  Health · Chat · RAG · Benchmark · Models/S3               │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / JSON
┌────────────────────────▼────────────────────────────────────┐
│  FastAPI Backend (port 8000)                                │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ /health  │  │  /chat   │  │  /rag    │  │/benchmark│  │
│  └──────────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│                     │             │               │         │
│  ┌──────────────────▼─────────────▼───────────────▼──────┐ │
│  │                    Services Layer                       │ │
│  │  ModelRouter · RagService · BenchmarkService           │ │
│  │  EmbeddingService · S3Service · PersonalityService     │ │
│  └──────────┬────────────┬───────────────────────────────┘ │
└─────────────┼────────────┼────────────────────────────────-┘
              │            │
   ┌──────────▼──┐   ┌─────▼──────────────────────────────┐
   │   Ollama    │   │  AWS S3                             │
   │  (port 11434│   │  models/ datasets/ reports/ docs/   │
   │   local)    │   │  (boto3, IAM role / env creds)      │
   └─────────────┘   └────────────────────────────────────-┘
         │
   ┌─────▼──────────┐   ┌─────────────────────────────────┐
   │  Local models  │   │  ChromaDB (local, data/chroma/)  │
   │  ~/.ollama/    │   │  sentence-transformers embeddings│
   └────────────────┘   └─────────────────────────────────┘
```

## Component Responsibilities

### FastAPI Backend (`backend/app/`)

| Module                            | Role                                                           |
| --------------------------------- | -------------------------------------------------------------- |
| `main.py`                         | App factory, middleware, lifespan, router mounting             |
| `core/config.py`                  | Pydantic-settings; reads env / .env; cached singleton          |
| `core/logging.py`                 | Text (local) or JSON (prod) structured logging for CloudWatch  |
| `core/security.py`                | Path traversal guard (`ensure_child_path`)                     |
| `models/schemas.py`               | All Pydantic request/response models                           |
| `models/providers.py`             | `ModelProvider` and `ArtifactKind` enums                       |
| `api/deps.py`                     | Module-level service singletons (DI)                           |
| `api/health.py`                   | Probes Ollama, S3, ChromaDB; returns degraded status           |
| `api/chat.py`                     | Chat + personality evaluation routes                           |
| `api/rag.py`                      | Ingest and query routes                                        |
| `api/models.py`                   | Registry + S3 CRUD routes                                      |
| `api/benchmark.py`                | Multi-model benchmark + optional report persistence            |
| `api/fine_tuning.py`              | LoRA command preparation                                       |
| `services/model_router.py`        | Dispatches chat to Ollama / local_api / openai_compatible / S3 |
| `services/rag_service.py`         | Document chunking, embedding, ChromaDB upsert and query        |
| `services/embedding_service.py`   | Lazy-loads sentence-transformers model                         |
| `services/s3_service.py`          | boto3 wrapper; upload, download, paginated list                |
| `services/benchmark_service.py`   | Runs model×prompt matrix, computes stats, persists report      |
| `services/personality_service.py` | Rule-based compliance scoring                                  |
| `services/fine_tuning_service.py` | Generates LoRA CLI command without executing it                |

### Model Routing (`ModelProvider` enum)

| Provider            | Transport                                | When to use                                                             |
| ------------------- | ---------------------------------------- | ----------------------------------------------------------------------- |
| `ollama`            | `POST /api/generate`                     | Local GPU/CPU inference via Ollama                                      |
| `local_api`         | `POST /v1/chat/completions`              | LM Studio, vLLM, llama.cpp server                                       |
| `openai_compatible` | `POST /v1/chat/completions` + Bearer key | Together AI, Anyscale, Azure OpenAI                                     |
| `s3_artifact`       | No inference                             | Reference only; download via `/models/s3/download`, then run via ollama |

## Chat Flow

```
POST /chat
  └── ModelRouter.chat(request)
        ├── OLLAMA → POST {ollama_base_url}/api/generate
        ├── LOCAL_API → POST {local_llm_api_base_url}/v1/chat/completions
        ├── OPENAI_COMPATIBLE → POST {openai_compatible_base_url}/v1/chat/completions
        └── S3_ARTIFACT → Returns note (no inference)
```

## RAG Flow

```
1. PUT documents → data/documents/
2. POST /rag/ingest {path, collection}
     └── RagService.ingest_path()
           ├── Read PDF (PyMuPDF) or TXT/MD
           ├── Chunk text (900 chars, 120 overlap)
           ├── EmbeddingService.embed() → sentence-transformers
           └── ChromaDB.add(ids, documents, embeddings, metadatas)

3. POST /rag/query {question, collection, top_k, chat?}
     └── RagService.query()
           ├── Embed question
           ├── ChromaDB.query(query_embeddings, n_results=top_k)
           └── [if chat] inject context → ModelRouter.chat()
```

## Benchmark Flow

```
POST /benchmark?save_report=true {prompts[], models[]}
  └── BenchmarkService.run()
        ├── For each (model × prompt):
        │     └── ModelRouter.chat() → elapsed_ms, response
        ├── Aggregate: avg/min/max/success_rate per model
        ├── [save_report] write reports/benchmark_<timestamp>.json
        └── [s3_bucket set] upload report to S3
```

## Security Boundaries

```
User input (path) → ensure_child_path(DOCUMENTS_PATH, input)
                         ↓
                   Resolves to absolute path
                         ↓
                   Checks: base in target.parents
                         ↓
                   UnsafePathError if outside base
```

## Deployment Targets

| Target      | Compose service  | Notes                                            |
| ----------- | ---------------- | ------------------------------------------------ |
| Local dev   | `api` + `ollama` | Volume mounts for hot reload                     |
| ECS Fargate | `api`            | ChromaDB on EFS or S3; Ollama on GPU instance    |
| Lambda      | `api`            | Only for stateless providers (openai_compatible) |

## Configuration Matrix

| Env   | `APP_ENV` | Logs | S3                     | Ollama          |
| ----- | --------- | ---- | ---------------------- | --------------- |
| Local | `local`   | Text | Optional               | localhost:11434 |
| Dev   | `dev`     | JSON | Required (dev bucket)  | Docker or EC2   |
| Prod  | `prod`    | JSON | Required (prod bucket) | GPU cluster     |
