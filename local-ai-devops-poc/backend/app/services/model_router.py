from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from app.core.config import Settings
from app.models.providers import ModelProvider
from app.models.schemas import ChatRequest, ChatResponse, ModelDescriptor, ModelRegistrationRequest


class UnsupportedProviderError(ValueError):
    pass


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelDescriptor] = {}

    def register(self, request: ModelRegistrationRequest) -> ModelDescriptor:
        descriptor = ModelDescriptor(
            **request.model_dump(),
            registered_at=datetime.now(timezone.utc),
        )
        self._models[request.name] = descriptor
        return descriptor

    def list(self) -> list[ModelDescriptor]:
        return list(self._models.values())


class ModelRouter:
    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger

    async def chat(self, request: ChatRequest) -> ChatResponse:
        started = time.perf_counter()
        if request.provider == ModelProvider.OLLAMA:
            raw = await self._ollama(request)
            text = raw.get("response", "")
        elif request.provider == ModelProvider.LOCAL_API:
            raw = await self._openai_style(request, self._required(self.settings.local_llm_api_base_url, "LOCAL_LLM_API_BASE_URL"))
            text = raw["choices"][0]["message"]["content"]
        elif request.provider == ModelProvider.OPENAI_COMPATIBLE:
            raw = await self._openai_style(
                request,
                self._required(self.settings.openai_compatible_base_url, "OPENAI_COMPATIBLE_BASE_URL"),
                self.settings.openai_compatible_api_key,
            )
            text = raw["choices"][0]["message"]["content"]
        elif request.provider == ModelProvider.S3_ARTIFACT:
            raw = {"note": "S3 stores artifacts; run downloaded model via ollama/local_api"}
            text = raw["note"]
        else:
            raise UnsupportedProviderError(str(request.provider))

        elapsed_ms = (time.perf_counter() - started) * 1000
        self.logger.info(
            "model_chat_complete",
            extra={"provider": request.provider, "model": request.model, "elapsed_ms": elapsed_ms},
        )
        return ChatResponse(
            provider=request.provider,
            model=request.model,
            response=text,
            elapsed_ms=elapsed_ms,
            raw=raw,
        )

    async def _ollama(self, request: ChatRequest) -> dict[str, object]:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": request.model,
            "prompt": self._prompt(request),
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def _openai_style(self, request: ChatRequest, base_url: str, api_key: str | None = None) -> dict[str, object]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json={
                    "model": request.model,
                    "messages": messages,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                },
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _prompt(request: ChatRequest) -> str:
        if request.system_prompt:
            return f"{request.system_prompt}\n\nUser: {request.prompt}"
        return request.prompt

    @staticmethod
    def _required(value: str | None, name: str) -> str:
        if not value:
            raise ValueError(f"{name} is required")
        return value
