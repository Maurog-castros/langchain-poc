# RAG

## Ingesta

Soporta:

- `.pdf` con PyMuPDF.
- `.txt`.
- `.md`.

```powershell
$env:PYTHONPATH="backend"
python scripts\ingest_documents.py data\documents --collection ops_docs
```

## Consulta

```json
{
  "question": "Que documentos hablan de costos S3?",
  "collection": "ops_docs",
  "top_k": 4
}
```

Con generación:

```json
{
  "question": "Resume runbook",
  "collection": "ops_docs",
  "top_k": 4,
  "chat": {
    "provider": "ollama",
    "model": "llama3.2",
    "prompt": "placeholder"
  }
}
```

## Edge cases

- PDF escaneado sin OCR produce pocos o cero chunks.
- No usar RAG para secretos.
- Separar colecciones por dominio: `ops_docs`, `logistics_docs`, `customer_docs`.
