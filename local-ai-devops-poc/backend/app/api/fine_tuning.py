from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import fine_tuning_service
from app.models.schemas import FineTuneJobRequest, FineTuneJobResponse

router = APIRouter(prefix="/fine-tuning", tags=["fine-tuning"])


@router.post("/prepare", response_model=FineTuneJobResponse)
async def prepare(request: FineTuneJobRequest) -> FineTuneJobResponse:
    return fine_tuning_service.prepare_lora(request)
