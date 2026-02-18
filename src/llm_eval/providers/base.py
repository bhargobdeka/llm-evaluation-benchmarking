from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InferenceRequest:
    prompt: str
    temperature: float = 0.0
    max_tokens: int = 512


@dataclass(frozen=True)
class InferenceResponse:
    text: str
    model: str
    provider: str
    latency_ms: int | None = None
    usage: dict[str, Any] | None = None


class ProviderClient(ABC):
    provider_name: str

    @abstractmethod
    def generate(self, request: InferenceRequest) -> InferenceResponse:
        raise NotImplementedError
