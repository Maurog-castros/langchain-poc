from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import personality_service, router as model_router
from app.models.schemas import ChatRequest, ChatResponse, PersonalityEvaluationRequest, PersonalityEvaluationResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await model_router.chat(request)


@router.post("/personality", response_model=PersonalityEvaluationResponse)
async def evaluate_personality(request: PersonalityEvaluationRequest) -> PersonalityEvaluationResponse:
    return personality_service.evaluate(request)
