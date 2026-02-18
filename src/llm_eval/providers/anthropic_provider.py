from __future__ import annotations

import os
import time
from typing import Any

from llm_eval.providers.base import InferenceRequest, InferenceResponse, ProviderClient
from llm_eval.providers.http import post_json


class AnthropicProvider(ProviderClient):
    provider_name = "anthropic"

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
            "model": self.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        data = post_json(
            url="https://api.anthropic.com/v1/messages",
            payload=payload,
            headers={
                "x-api-key": self._api_key(),
                "anthropic-version": "2023-06-01",
            },
            timeout_seconds=self.timeout_seconds,
        )
        contents = data.get("content", [])
        text_chunks = [item.get("text", "") for item in contents if item.get("type") == "text"]
        latency_ms = int((time.perf_counter() - started) * 1000)
        return InferenceResponse(
            text="\n".join(text_chunks).strip(),
            model=str(data.get("model", self.model)),
            provider=self.provider_name,
            latency_ms=latency_ms,
            usage=data.get("usage"),
        )
