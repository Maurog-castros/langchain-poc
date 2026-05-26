from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.api.deps import rag_service, router as model_router
from app.models.schemas import RagIngestRequest, RagQueryRequest, RagQueryResponse

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ingest")
async def ingest(request: RagIngestRequest) -> dict[str, int | str]:
    chunks = rag_service.ingest_path(Path(request.path), request.collection)
    return {"collection": request.collection, "chunks": chunks}


@router.post("/query", response_model=RagQueryResponse)
async def query(request: RagQueryRequest) -> RagQueryResponse:
    sources = rag_service.query(request.question, request.collection, request.top_k)
    if not request.chat:
        return RagQueryResponse(answer=None, sources=sources)

    context = "\n\n".join(f"[{idx + 1}] {source.text}" for idx, source in enumerate(sources))
    chat_request = request.chat.model_copy(
        update={"prompt": f"Answer using only this context:\n{context}\n\nQuestion: {request.question}"}
    )
    answer = await model_router.chat(chat_request)
    return RagQueryResponse(answer=answer.response, sources=sources)
