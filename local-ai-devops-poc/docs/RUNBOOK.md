# Runbook — local-ai-devops-poc

## Operación diaria

### Iniciar el sistema local

```powershell
# Terminal 1 — API
cd C:\DEV\langchain-poc\local-ai-devops-poc\backend
.\.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd C:\DEV\langchain-poc\local-ai-devops-poc\frontend
npm run dev

# Verificar
Invoke-RestMethod http://localhost:8000/health
```

### Con Docker Compose

```powershell
cd C:\DEV\langchain-poc\local-ai-devops-poc
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml logs -f api
```

---

## Troubleshooting

### `status: degraded` en `/health`

**Causa:** Una o más integraciones no responde.

**Diagnóstico:**
```powershell
$h = Invoke-RestMethod http://localhost:8000/health
$h.integrations | ConvertTo-Json -Depth 5
```

**Integraciones posibles:**

| Integration | Status `unreachable` | Fix |
|---|---|---|
| `ollama` | Ollama no corre | `ollama serve` o iniciar Docker |
| `s3` | Credenciales inválidas o bucket no existe | `aws s3 ls s3://YOUR_BUCKET` |
| `chroma` | Error de permisos en `data/chroma` | `mkdir data\chroma` |

---

### Error `S3_BUCKET environment variable is required`

**Causa:** `S3_BUCKET` no está configurado en `.env`.

**Fix:**
```powershell
# Editar .env
$env:S3_BUCKET = "my-bucket"
# O agregar al .env:
echo "S3_BUCKET=my-bucket" >> backend\.env
# Reiniciar API
```

---

### Ollama: `model not found`

```powershell
ollama pull llama3.2
ollama list  # Verificar que aparece
```

---

### ChromaDB: `Collection already exists` con IDs duplicados

Al reingestar los mismos documentos, Chroma puede rechazar IDs duplicados.

**Fix:** Los IDs usan `source:idx`, lo que significa que si el archivo cambió pero el nombre no, puede haber colisión.  Limpiar y reingestar:

```powershell
Remove-Item -Recurse data\chroma\*
Invoke-RestMethod http://localhost:8000/rag/ingest -Method Post `
  -ContentType "application/json" `
  -Body '{"path":".","collection":"ops_docs"}'
```

---

### Tests fallan: `ModuleNotFoundError: No module named 'app'`

```powershell
cd backend
$env:PYTHONPATH = "."
.\.venv\Scripts\python -m pytest
```

---

### Frontend: `CORS error` en consola

Verificar que `main.py` tiene el origen del frontend en `allow_origins`.  Por defecto incluye `localhost:5173` y `127.0.0.1:5173`.  Si corres en otro puerto:

```python
# app/main.py
allow_origins=["http://localhost:3000", "http://localhost:5173"]
```

---

## Operaciones S3

### Listar todos los artefactos

```powershell
Invoke-RestMethod "http://localhost:8000/models/s3/list"
Invoke-RestMethod "http://localhost:8000/models/s3/list?prefix=models"
Invoke-RestMethod "http://localhost:8000/models/s3/list?prefix=reports"
```

### Upload manual

```powershell
Invoke-RestMethod http://localhost:8000/models/s3/upload -Method Post `
  -ContentType "application/json" `
  -Body '{
    "local_path": "reports/benchmark_20260526T143000Z.json",
    "kind": "report"
  }'
```

---

## Mantenimiento

### Limpiar ChromaDB

```powershell
Remove-Item -Recurse -Force data\chroma
```

### Limpiar reportes locales

```powershell
Remove-Item reports\*.json
```

### Actualizar dependencias

```powershell
cd backend
.\.venv\Scripts\pip install --upgrade -r requirements.txt
```

### Actualizar frontend

```powershell
cd frontend
npm update
npm run build
```

---

## Monitoreo en producción (ECS)

### Logs en CloudWatch

```
Log group: /ecs/local-ai-devops-poc
```

**Query de errores recientes:**
```
fields @timestamp, message, error
| filter level = "ERROR" or level = "WARNING"
| sort @timestamp desc
| limit 50
```

**Query de latencia media:**
```
fields @timestamp, model, elapsed_ms
| filter message = "benchmark_result" and ok = true
| stats avg(elapsed_ms) as avg_ms by model
| sort avg_ms desc
```

### Métricas CloudWatch sugeridas

| Métrica custom | Dimensión | Umbral alerta |
|---|---|---|
| `LLM/ElapsedMs` | model, provider | > 10,000 ms |
| `RAG/ChunksIngested` | collection | 0 (posible error de ingesta) |
| `S3/UploadErrors` | — | > 0 |

Implementación futura: usar `boto3.client("cloudwatch").put_metric_data()` dentro de los servicios.

---

## Rollback rápido

### Volver a versión anterior del backend

```powershell
git log --oneline -10
git checkout <sha> -- backend/
cd backend && .\.venv\Scripts\uvicorn app.main:app --reload
```

### Volver a imagen Docker anterior

```powershell
# Ver tags disponibles en ECR
aws ecr list-images --repository-name local-ai-devops-poc

# Actualizar task definition con tag anterior y hacer deploy
```
