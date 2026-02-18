from __future__ import annotations

import os
import time
from typing import Any

from llm_eval.providers.base import InferenceRequest, InferenceResponse, ProviderClient
from llm_eval.providers.http import post_json


class GeminiProvider(ProviderClient):
    provider_name = "gemini"

    def __init__(self, model: str, api_key_env: str, timeout_seconds: int = 45):
        self.model = model
        self.api_key_env = api_key_env
        self.timeout_seconds = timeout_seconds

    def _api_key(self) -> str:
        key = os.getenv(self.api_key_env, "")
        if not key:
            raise RuntimeError(f"Missing API key in env var: {self.api_key_env}")
        return key

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        started = time.perf_counter()
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": request.prompt}]}],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        key = self._api_key()
        data = post_json(
            url=f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={key}",
            payload=payload,
            headers={},
            timeout_seconds=self.timeout_seconds,
        )
        candidates = data.get("candidates", [])
        content_parts = (
            candidates[0].get("content", {}).get("parts", []) if candidates else []
        )
        text = "\n".join(part.get("text", "") for part in content_parts if "text" in part).strip()
        latency_ms = int((time.perf_counter() - started) * 1000)
        return InferenceResponse(
            text=text,
            model=self.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
            usage=data.get("usageMetadata"),
        )
