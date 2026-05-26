# Fine-Tuning / LoRA — local-ai-devops-poc

## Conceptos

### LoRA (Low-Rank Adaptation)

LoRA modifica el modelo base inyectando matrices de bajo rango en las capas de atención.  Ventajas:

- Entrena solo ~0.1-1% de los parámetros del modelo.
- El adapter resultante es pequeño (~10-200 MB vs 4-40 GB del modelo base).
- El modelo base no se modifica; se pueden combinar múltiples adapters.

```
Base model (frozen) + LoRA adapter (trainable) = Fine-tuned behavior
                       ↑
               Solo esto se guarda en S3
```

## Stack de training recomendado

| Opción | Hardware | Velocidad | Notas |
|---|---|---|---|
| `mlx-lm` (Apple Silicon) | M1/M2/M3 Pro+ | Rápido en Metal | Ver `run_finetune_lora.py` |
| `unsloth` + `trl` | NVIDIA GPU | Muy rápido | CUDA 12+, 16GB VRAM |
| `transformers` + `peft` | CPU/GPU | Lento en CPU | Referencia universal |
| `llama.cpp finetune` | CPU | Lento | Portable |

## Estructura del dataset

### Formato JSONL (instruction-following)

```jsonl
{"text": "<|im_start|>system\nEres un asistente DevOps.<|im_end|>\n<|im_start|>user\n¿Cómo diagnostico alta latencia en un API LLM?<|im_end|>\n<|im_start|>assistant\nPara diagnosticar alta latencia...<|im_end|>"}
{"text": "<|im_start|>system\nEres un asistente DevOps.<|im_end|>\n<|im_start|>user\n¿Qué métricas monitorear en producción?<|im_end|>\n<|im_start|>assistant\nLas métricas clave son...<|im_end|>"}
```

### Alternativa: formato ShareGPT

```jsonl
{"conversations": [
  {"from": "system", "value": "Eres un asistente DevOps."},
  {"from": "human", "value": "¿Cómo diagnostico alta latencia?"},
  {"from": "gpt", "value": "Para diagnosticar..."}
]}
```

El script `run_finetune_lora.py` genera el comando para `mlx_lm.lora`.  Para usar `unsloth`, ajusta el script según su API.

## API

```bash
# Preparar comando LoRA (dry_run=true por defecto)
curl -X POST http://localhost:8000/fine-tuning/prepare \
  -H "Content-Type: application/json" \
  -d '{
    "base_model": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    "dataset_path": "data/datasets/devops_qa.jsonl",
    "output_dir": "artifacts/lora/mistral-devops",
    "method": "lora",
    "dry_run": true
  }'
```

Respuesta:

```json
{
  "command": [
    "python", "-m", "mlx_lm.lora",
    "--model", "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    "--train",
    "--data", "data/datasets/devops_qa.jsonl",
    "--adapter-path", "artifacts/lora/mistral-devops"
  ],
  "dry_run": true,
  "notes": [
    "dry_run defaults true; install adapter stack before real run",
    "dataset must be JSONL or framework-specific train/valid folder",
    "upload resulting adapter directory to S3, not Git"
  ]
}
```

## CLI

```powershell
$env:PYTHONPATH = "backend"

python scripts\run_finetune_lora.py `
  --base-model "mlx-community/Mistral-7B-Instruct-v0.3-4bit" `
  --dataset-path "data\datasets\devops_qa.jsonl" `
  --output-dir "artifacts\lora\mistral-devops" `
  --dry-run   # Eliminar para ejecutar real
```

## Flujo completo en producción

```
1. Preparar dataset → data/datasets/train.jsonl
2. POST /fine-tuning/prepare → obtener comando
3. Ejecutar comando en máquina con GPU
4. Verificar adapter: ls artifacts/lora/mistral-devops/
5. Cargar adapter a S3:
   python scripts/upload_model_to_s3.py artifacts/lora/mistral-devops \
     --kind model --key local-ai-devops-poc/models/mistral-devops-adapter
6. Usar adapter via Ollama:
   ollama create devops-assistant -f Modelfile
   # Modelfile: FROM mistral:7b + adapter path
```

## Costos estimados de training

| Escenario | Hardware | Duración | Costo |
|---|---|---|---|
| 1,000 ejemplos, Mistral 7B | M2 Pro (16GB) | ~2 horas | $0 (local) |
| 10,000 ejemplos, Mistral 7B | RTX 4090 | ~1 hora | $0 (local) |
| 10,000 ejemplos, Llama3 70B | A100 80GB | ~8 horas | ~$24 (Lambda Labs) |

> ⚠️ No subir pesos del modelo base ni adapters a Git.  Usar S3 con versionado activado.

## Evaluación del adapter

Después de training, usar el benchmark y la evaluación de personalidad para medir mejora:

```bash
# Antes del adapter
POST /benchmark { models: [{provider: "ollama", model: "mistral:7b", ...}] }

# Después del adapter (via Ollama con modelo custom)
POST /benchmark { models: [{provider: "ollama", model: "devops-assistant", ...}] }
```

Comparar `avg_ms`, `success_rate` y calidad de `response_preview`.
