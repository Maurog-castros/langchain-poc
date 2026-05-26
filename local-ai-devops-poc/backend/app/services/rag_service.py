from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import Settings
from app.core.security import ensure_child_path
from app.models.schemas import RagSource
from app.services.embedding_service import EmbeddingService


class RagService:
    def __init__(self, settings: Settings, embeddings: EmbeddingService, logger: logging.Logger) -> None:
        self.settings = settings
        self.embeddings = embeddings
        self.logger = logger

    def ingest_path(self, path: Path, collection: str) -> int:
        target = ensure_child_path(self.settings.documents_path, path)
        files = [target] if target.is_file() else [p for p in target.rglob("*") if p.suffix.lower() in {".pdf", ".txt", ".md"}]
        chunks: list[str] = []
        metadatas: list[dict[str, object]] = []

        for file_path in files:
            for text, page in self._read_file(file_path):
                for chunk in self._chunk(text):
                    chunks.append(chunk)
                    metadatas.append({"source": str(file_path), "page": page})

        if not chunks:
            return 0

        ids = [f"{metadata['source']}:{idx}" for idx, metadata in enumerate(metadatas)]
        self._collection(collection).add(
            ids=ids,
            documents=chunks,
            embeddings=self.embeddings.embed(chunks),
            metadatas=metadatas,
        )
        self.logger.info("rag_ingest_ok", extra={"collection": collection, "chunks": len(chunks)})
        return len(chunks)

    def query(self, question: str, collection: str, top_k: int) -> list[RagSource]:
        result = self._collection(collection).query(
            query_embeddings=self.embeddings.embed([question]),
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        sources: list[RagSource] = []
        for text, metadata, distance in zip(documents, metadatas, distances, strict=False):
            sources.append(
                RagSource(
                    text=text,
                    source=str(metadata.get("source", "")),
                    page=metadata.get("page"),
                    score=float(distance),
                )
            )
        return sources

    def _collection(self, name: str):
        import chromadb

        client = chromadb.PersistentClient(path=str(self.settings.chroma_path))
        return client.get_or_create_collection(name=name)

    @staticmethod
    def _chunk(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
        clean = " ".join(text.split())
        if not clean:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(clean):
            chunks.append(clean[start : start + chunk_size])
            start += chunk_size - overlap
        return chunks

    @staticmethod
    def _read_file(path: Path) -> list[tuple[str, int | None]]:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            return [(path.read_text(encoding="utf-8", errors="ignore"), None)]
        if suffix == ".pdf":
            import fitz

            doc = fitz.open(path)
            return [(page.get_text(), page.number + 1) for page in doc]
        return []
