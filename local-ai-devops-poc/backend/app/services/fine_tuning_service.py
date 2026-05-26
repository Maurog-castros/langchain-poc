from __future__ import annotations

from pathlib import Path

from app.models.schemas import FineTuneJobRequest, FineTuneJobResponse


class FineTuningService:
    def prepare_lora(self, request: FineTuneJobRequest) -> FineTuneJobResponse:
        dataset = Path(request.dataset_path)
        command = [
            "python",
            "-m",
            "mlx_lm.lora",
            "--model",
            request.base_model,
            "--train",
            "--data",
            str(dataset),
            "--adapter-path",
            request.output_dir,
        ]
        notes = [
            "dry_run defaults true; install adapter stack before real run",
            "dataset must be JSONL or framework-specific train/valid folder",
            "upload resulting adapter directory to S3, not Git",
        ]
        return FineTuneJobResponse(command=command, dry_run=request.dry_run, notes=notes)
