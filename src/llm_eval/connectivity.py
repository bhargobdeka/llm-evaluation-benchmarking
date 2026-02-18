from __future__ import annotations

import re
from dataclasses import dataclass

from llm_eval.config import RunConfig, load_env_file
from llm_eval.providers import InferenceRequest, build_provider_client

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{16,}"),
]


@dataclass(frozen=True)
class ConnectivityResult:
    provider: str
    model: str
    ok: bool
    detail: str


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_KEY]", redacted)
    return redacted


def check_connectivity(config: RunConfig, env_path: str = ".env") -> list[ConnectivityResult]:
    load_env_file(env_path)
    results: list[ConnectivityResult] = []
    for provider_cfg in config.providers:
        try:
            client = build_provider_client(
                provider_config=provider_cfg,
                timeout_seconds=config.policy.reliability.request_timeout_seconds,
            )
            response = client.generate(
                InferenceRequest(
                    prompt="Reply with only the letter A.",
                    temperature=0.0,
                    max_tokens=8,
                )
            )
            detail = f"ok ({len(response.text.strip())} chars)"
            results.append(
                ConnectivityResult(
                    provider=provider_cfg.provider,
                    model=provider_cfg.model,
                    ok=True,
                    detail=detail,
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                ConnectivityResult(
                    provider=provider_cfg.provider,
                    model=provider_cfg.model,
                    ok=False,
                    detail=redact_secrets(str(exc))[:220],
                )
            )
    return results
