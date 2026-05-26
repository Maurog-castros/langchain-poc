# Benchmarking — local-ai-devops-poc

## Objetivo

Medir y comparar:

1. **Latencia** (time-to-complete-response) por modelo y provider.
2. **Calidad de respuesta** (via personality evaluation o revisión manual).
3. **Estabilidad** bajo múltiples llamadas consecutivas.

## Metodología

### Variables controladas

| Variable | Recomendación |
|---|---|
| Hardware | Mismo equipo para todas las mediciones |
| Modelo en memoria | Hacer warm-up call antes de medir |
| Temperatura | 0.0 para reproducibilidad |
| Max tokens | Igual para todos los modelos |
| Prompts | Mínimo 3 prompts distintos |
| Iteraciones | Mínimo 3 por prompt; descartar primera (cold start) |

### Cómo interpretar `elapsed_ms`

- Es **wall-clock time** desde el envío del request hasta recibir la respuesta completa.
- Incluye: carga del modelo (si estaba frío), generación de tokens, serialización.
- Para modelos locales, la primera llamada puede ser 5-10x más lenta (warm-up).

### Corrección de cold start

```python
# En el script CLI, puedes hacer warm-up antes del benchmark real:
--prompt "warmup" --prompt "test real 1" --prompt "test real 2"
# Descartar el primer resultado en el análisis.
```

## API

```bash
# Benchmark básico
curl -X POST "http://localhost:8000/benchmark?save_report=true" \
  -H "Content-Type: application/json" \
  -d '{
    "prompts": [
      "Explica qué es RAG en 2 oraciones.",
      "Diagnostica latencia alta en una API REST.",
      "¿Qué es un adapter LoRA?"
    ],
    "models": [
      {"provider": "ollama", "model": "llama3.2",   "prompt": "", "temperature": 0.0, "max_tokens": 256},
      {"provider": "ollama", "model": "mistral:7b", "prompt": "", "temperature": 0.0, "max_tokens": 256}
    ]
  }'
```

### Respuesta

```json
{
  "results": [...],
  "summary": {
    "ollama/llama3.2": {
      "total": 3, "success": 3, "success_rate": 1.0,
      "avg_ms": 1423.5, "min_ms": 1201.0, "max_ms": 1784.2
    }
  },
  "report_path": "reports/benchmark_20260526T143000Z.json",
  "s3_uri": "s3://my-bucket/local-ai-devops-poc/reports/benchmark_20260526T143000Z.json"
}
```

## CLI

```powershell
$env:PYTHONPATH = "backend"

python scripts\benchmark_models.py `
  --provider ollama `
  --model llama3.2 `
  --prompt "Diagnostica CPU 100% en servidor LLM" `
  --prompt "Explica diferencia entre RAG y fine-tuning" `
  --prompt "Recomienda arquitectura para inferencia local"
```

Salida JSON en stdout, redirigible a archivo:

```powershell
python scripts\benchmark_models.py ... > reports\mi_benchmark.json
```

## Métricas clave

| Métrica | Descripción | Objetivo típico |
|---|---|---|
| `avg_ms` | Latencia promedio | < 3,000 ms para modelos 7B en GPU |
| `min_ms` | Mejor caso (post warm-up) | Referencia de capacidad máxima |
| `max_ms` | Peor caso | Detecta varianza y throttling |
| `success_rate` | Fracción de requests exitosos | > 0.95 para uso operacional |
| `response_preview` | Primeros 240 chars | Inspección rápida de calidad |

## Comparación de providers

| Provider | Latencia esperada | Notas |
|---|---|---|
| `ollama` (CPU) | 5,000-30,000 ms | Depende del modelo y hardware |
| `ollama` (GPU) | 500-3,000 ms | RTX 3090 con llama3.2:8b ~1,200 ms |
| `local_api` (vLLM) | 300-1,500 ms | Batching y optimizaciones de GPU |
| `openai_compatible` (remoto) | 800-3,000 ms | Depende de la red y cola del provider |

## Análisis de reportes

Los reportes se guardan en `reports/` como JSON.  Para análisis rápido en Python:

```python
import json, pathlib, statistics

report = json.loads(pathlib.Path("reports/benchmark_*.json").read_text())
for model_key, stats in report["summary"].items():
    print(f"{model_key}: avg={stats['avg_ms']:.0f}ms  p0={stats['min_ms']:.0f}ms")
```

Para análisis avanzado, cargar en pandas:

```python
import pandas as pd
df = pd.DataFrame(report["results"])
df[df["ok"]].groupby("model")["elapsed_ms"].describe()
```

## CloudWatch integration

Con `APP_ENV=prod` y logs JSON activos, cada resultado de benchmark emite:

```json
{"level": "INFO", "logger": "local_ai_devops", "message": "benchmark_result",
 "provider": "ollama", "model": "llama3.2", "elapsed_ms": 1423.5, "ok": true}
```

Query de CloudWatch Logs Insights:

```
fields @timestamp, model, elapsed_ms, ok
| filter message = "benchmark_result"
| stats avg(elapsed_ms), count(*) by model
| sort avg_elapsed_ms desc
```
