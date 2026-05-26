# Benchmarking

Mide latencia por modelo y prompt.

```powershell
$env:PYTHONPATH="backend"
python scripts\benchmark_models.py --provider ollama --model llama3.2 --prompt "Diagnostica RAG lento" --prompt "Plan rollback"
```

API:

```json
{
  "prompts": ["Diagnostica timeout Ollama"],
  "models": [
    {
      "provider": "ollama",
      "model": "llama3.2",
      "prompt": "placeholder"
    }
  ]
}
```

Campos:

- `elapsed_ms`: latencia total desde backend.
- `ok`: fallo controlado por modelo/prompt.
- `response_preview`: preview para no guardar salida completa.
