from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from app.models.schemas import FineTuneJobRequest
from app.services.fine_tuning_service import FineTuningService


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare LoRA fine-tuning command")
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--output-dir", default="artifacts/lora")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    result = FineTuningService().prepare_lora(
        FineTuneJobRequest(
            base_model=args.base_model,
            dataset_path=args.dataset_path,
            output_dir=args.output_dir,
            dry_run=not args.run,
        )
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
