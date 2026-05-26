# Runbook

## API no inicia

```powershell
cd backend
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\uvicorn app.main:app --reload
```

Validar `.env`.

## Ollama falla

```powershell
ollama list
ollama pull llama3.2
Invoke-RestMethod http://localhost:11434/api/tags
```

## S3 falla

```powershell
aws sts get-caller-identity
aws s3 ls s3://YOUR_BUCKET_NAME/local-ai-devops-poc/
```

Validar `S3_BUCKET`, región e IAM.

## RAG lento

- Revisar tamaño de documentos.
- Reducir `top_k`.
- Persistir `data/chroma` en volumen local.
- Cambiar embedding model si CPU queda saturado.

## Rollback

- Mantener `.env.example` limpio.
- Borrar colección Chroma eliminando `data/chroma`.
- Restaurar artefacto desde versión S3 si bucket versioning activo.
