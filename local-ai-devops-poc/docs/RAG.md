# RAG Pipeline — local-ai-devops-poc

## Overview

RAG (Retrieval-Augmented Generation) combina búsqueda semántica en documentos propios con generación de texto por un LLM.  Esto permite responder preguntas usando conocimiento privado sin necesitar fine-tuning.

```
Documents (PDF/TXT/MD)
       │
       ▼
  Text extraction (PyMuPDF / built-in)
       │
       ▼
  Chunking (900 chars, 120 overlap)
       │
       ▼
  Embedding (sentence-transformers/all-MiniLM-L6-v2)
       │
       ▼
  ChromaDB (data/chroma/) ──────────────────────┐
                                                 │
  User question → embed → similarity search      │
                                                 ▼
                         Top-K chunks ──→ Context + Prompt
                                                 │
                                                 ▼
                                      LLM (via ModelRouter)
                                                 │
                                                 ▼
                                            Answer + Sources
```

## Chunking Strategy

| Parámetro | Valor | Razonamiento |
|---|---|---|
| `chunk_size` | 900 chars | Cabe en contexto de la mayoría de los modelos |
| `overlap` | 120 chars | Preserva contexto en límites de chunk |
| Separación | whitespace | Normaliza espacios y saltos de línea |

> **Tuning:** Si los chunks son demasiado grandes (respuestas genéricas), reducir a 400-600.  Si son demasiado pequeños (contexto roto), aumentar a 1200.

## Embedding Model

**Modelo por defecto:** `sentence-transformers/all-MiniLM-L6-v2`

- Tamaño: ~80 MB
- Dimensiones: 384
- Velocidad: ~2,000 oraciones/segundo en CPU
- Calidad: buena para inglés y razonablemente buena para español

**Alternativas:**

| Modelo | Dimensiones | Calidad ES | Tamaño |
|---|---|---|---|
| `all-MiniLM-L6-v2` | 384 | Buena | ~80 MB |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | Muy buena | ~115 MB |
| `intfloat/multilingual-e5-large` | 1024 | Excelente | ~560 MB |

Cambiar via `EMBEDDING_MODEL` en `.env`.  El modelo se descarga automáticamente en el primer uso.

## ChromaDB

- **Backend:** SQLite + HNSW index (local, sin servidor)
- **Persistencia:** `data/chroma/` (mapeado a volumen Docker en producción)
- **Colecciones:** separadas por tema (e.g., `ops_docs`, `legal_docs`)
- **Costo:** $0 local; en producción considerar Pinecone o Qdrant para escala

## API Usage

### Ingesta

```bash
# Via API
curl -X POST http://localhost:8000/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{"path": ".", "collection": "ops_docs"}'

# Via CLI
python scripts/ingest_documents.py data/documents --collection ops_docs
```

### Query sin LLM (solo retrieval)

```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cómo configurar el bucket S3?",
    "collection": "ops_docs",
    "top_k": 4
  }'
```

### Query con LLM (RAG completo)

```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cómo configurar el bucket S3?",
    "collection": "ops_docs",
    "top_k": 4,
    "chat": {
      "provider": "ollama",
      "model": "llama3.2",
      "prompt": "",
      "temperature": 0.1,
      "max_tokens": 512
    }
  }'
```

## Formatos de documento soportados

| Formato | Parser | Notas |
|---|---|---|
| `.pdf` | PyMuPDF (fitz) | Extrae texto página a página; metadato de página incluido |
| `.txt` | built-in | UTF-8, errores ignorados |
| `.md` | built-in | Mismo parser que TXT |

> ⚠️ PDFs escaneados (solo imágenes) no tienen texto extraíble.  Usar OCR (Tesseract) como pre-proceso.

## Seguridad

- Los paths de ingesta son validados con `ensure_child_path()`.
- No se pueden ingestar archivos fuera de `DOCUMENTS_PATH`.
- Los documentos sensibles deben estar en la máquina local o en S3 con acceso IAM mínimo.

## Producción

Para producción:
1. Montar `data/chroma/` en un EFS o usar un vector store gestionado.
2. Pre-ingestar documentos en CI/CD (no on-the-fly).
3. Considerar re-ingesta incremental basada en hash de archivos.
4. Usar `paraphrase-multilingual-MiniLM-L12-v2` para documentos en español.
