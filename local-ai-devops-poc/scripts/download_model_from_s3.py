from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import get_settings
from app.services.s3_service import S3Service


def main() -> None:
    parser = argparse.ArgumentParser(description="Download model/artifact from S3")
    parser.add_argument("s3_key")
    parser.add_argument("local_path", type=Path)
    args = parser.parse_args()

    service = S3Service(get_settings(), logging.getLogger("s3_cli"))
    result = service.download(args.s3_key, args.local_path)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
