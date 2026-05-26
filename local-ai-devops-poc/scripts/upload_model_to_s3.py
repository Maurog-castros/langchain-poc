from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import get_settings
from app.models.providers import ArtifactKind
from app.services.s3_service import S3Service


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload local model/artifact to S3")
    parser.add_argument("path", type=Path)
    parser.add_argument("--kind", choices=[kind.value for kind in ArtifactKind], default=ArtifactKind.MODEL.value)
    parser.add_argument("--key")
    args = parser.parse_args()

    service = S3Service(get_settings(), logging.getLogger("s3_cli"))
    result = service.upload(args.path, ArtifactKind(args.kind), args.key)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
