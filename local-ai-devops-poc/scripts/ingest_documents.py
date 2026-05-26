from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import get_settings
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RagService


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local documents into ChromaDB")
    parser.add_argument("path", type=Path)
    parser.add_argument("--collection", default="local_documents")
    args = parser.parse_args()

    settings = get_settings()
    service = RagService(settings, EmbeddingService(settings), logging.getLogger("rag_cli"))
    chunks = service.ingest_path(args.path, args.collection)
    print({"collection": args.collection, "chunks": chunks})


if __name__ == "__main__":
    main()
