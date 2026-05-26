# Fine Tuning / LoRA

La PoC prepara comando LoRA en dry-run. No ejecuta entrenamiento pesado por defecto.

```powershell
$env:PYTHONPATH="backend"
python scripts\run_finetune_lora.py --base-model mistral --dataset-path data\datasets\train.jsonl
```

## Dataset mínimo

Usar JSONL:

```jsonl
{"messages":[{"role":"system","content":"Eres agente DevOps conciso."},{"role":"user","content":"Que revisar ante latencia alta?"},{"role":"assistant","content":"Revisar p95, errores 5xx, saturación CPU, red y proveedor LLM."}]}
```

## Reglas

- Dataset fuera de Git si contiene datos internos.
- Versionar hash o manifest, no datos sensibles.
- Subir adapters a S3.
- Registrar costo de GPU/CPU.
