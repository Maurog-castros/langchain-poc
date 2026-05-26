# Architecture

## Componentes

- FastAPI backend: orquesta requests, validación Pydantic y rutas.
- Services: lógica de negocio para S3, RAG, routing LLM, benchmark, personalidad y fine-tuning.
- ChromaDB: vector store local persistido en `data/chroma`.
- Ollama: runtime local para modelos descargados.
- AWS S3: almacenamiento de modelos, documentos, datasets y reportes.

## Flujo chat

`POST /chat` recibe `provider`, `model`, `prompt`. `ModelRouter` deriva a:

- `ollama`: `POST /api/generate`.
- `local_api`: endpoint OpenAI-style local.
- `openai_compatible`: endpoint remoto con API key por env.
- `s3_artifact`: solo referencia; descargar y ejecutar vía runtime local.

## Flujo RAG

1. Copiar documentos a `data/documents`.
2. `POST /rag/ingest` extrae texto, divide chunks, calcula embeddings y guarda en Chroma.
3. `POST /rag/query` recupera fuentes.
4. Si incluye `chat`, inyecta contexto y responde usando modelo elegido.

## Day 2

- Logs estructurados básicos con `logging`.
- Errores de proveedores quedan visibles en benchmark.
- Artefactos pesados viven en S3, no Git.
- Docker Compose fija API + Ollama para entorno reproducible.
