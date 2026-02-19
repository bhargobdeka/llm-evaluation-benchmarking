from __future__ import annotations

import os
import time

from llm_eval.providers.base import InferenceRequest, InferenceResponse, ProviderClient


class GroqProvider(ProviderClient):
    provider_name = "groq"

    def __init__(self, model: str, api_key_env: str, timeout_seconds: int = 45):
        self.model = model
        self.api_key_env = api_key_env
        self.timeout_seconds = timeout_seconds

    def _api_key(self) -> str:
        key = os.getenv(self.api_key_env, "").strip()
        if not key:
            raise RuntimeError(f"Missing API key in env var: {self.api_key_env}")
        return key

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        try:
            from groq import Groq
        except ImportError as exc:  # pragma: no cover - runtime environment specific
            raise RuntimeError("groq package is required for GroqProvider. Install with: pip install groq") from exc

        started = time.perf_counter()
        client = Groq(api_key=self._api_key())
        completion = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": request.prompt}],
            temperature=request.temperature,
            max_completion_tokens=request.max_tokens,
            top_p=1,
            stream=False,
        )
        text = completion.choices[0].message.content if completion.choices else ""
        text = text or ""
        latency_ms = int((time.perf_counter() - started) * 1000)
        return InferenceResponse(
            text=text,
            model=str(completion.model or self.model),
            provider=self.provider_name,
            latency_ms=latency_ms,
            usage=completion.usage.model_dump() if completion.usage else None,
        )
