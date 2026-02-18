from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class RetryPolicy(BaseModel):
    max_attempts: int = 3
    backoff_seconds: list[int] = Field(default_factory=lambda: [1, 2, 4])
    retryable_status_codes: list[int] = Field(
        default_factory=lambda: [408, 429, 500, 502, 503, 504]
    )


class ReliabilityPolicy(BaseModel):
    max_parallel_requests: int = 3
    request_timeout_seconds: int = 45
    retry: RetryPolicy = Field(default_factory=RetryPolicy)
    provider_error_rate_window_size_requests: int = 50
    provider_error_rate_hard_stop_percent: int = 10


class BudgetPolicy(BaseModel):
    max_usd_per_run: float = 5.0
    warn_at_percent: int = 80
    enforce_hard_stop: bool = True


class SecurityPolicy(BaseModel):
    byok_only: bool = True
    persist_user_api_keys: bool = False
    redact_secrets_in_logs: bool = True
    allowed_secret_env_vars: list[str] = Field(
        default_factory=lambda: ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]
    )


class RuntimePolicy(BaseModel):
    budget: BudgetPolicy = Field(default_factory=BudgetPolicy)
    reliability: ReliabilityPolicy = Field(default_factory=ReliabilityPolicy)
    security: SecurityPolicy = Field(default_factory=SecurityPolicy)


class ProviderConfig(BaseModel):
    provider: Literal["anthropic", "openai", "gemini", "groq", "local"]
    model: str
    api_key_env: str | None = None
    temperature: float = 0.0
    max_tokens: int = 512

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, value: float) -> float:
        if not 0 <= value <= 2:
            raise ValueError("temperature must be between 0 and 2")
        return value


class BenchmarkConfig(BaseModel):
    name: str = "mmlu_subset"
    split: str = "dev"
    dataset_path: str = "data/benchmarks/mmlu_subset/dev.jsonl"
    max_samples: int | None = 50


class RunConfig(BaseModel):
    run_name: str = "baseline"
    seed: int = 42
    providers: list[ProviderConfig]
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)
    policy: RuntimePolicy = Field(default_factory=RuntimePolicy)


class RunManifest(BaseModel):
    run_id: str
    run_name: str
    created_at: str
    seed: int
    benchmark: dict[str, Any]
    providers: list[dict[str, Any]]
    policy_snapshot: dict[str, Any]


def load_env_file(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_run_config(path: str | Path) -> RunConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Config file must deserialize into an object")
    return RunConfig.model_validate(data)


def build_run_manifest(config: RunConfig) -> RunManifest:
    created_at = datetime.now(timezone.utc).isoformat()
    fingerprint_payload = {
        "run_name": config.run_name,
        "seed": config.seed,
        "benchmark": config.benchmark.model_dump(),
        "providers": [p.model_dump() for p in config.providers],
    }
    run_id = hashlib.sha256(json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")).hexdigest()[
        :16
    ]
    return RunManifest(
        run_id=run_id,
        run_name=config.run_name,
        created_at=created_at,
        seed=config.seed,
        benchmark=config.benchmark.model_dump(),
        providers=[p.model_dump() for p in config.providers],
        policy_snapshot=config.policy.model_dump(),
    )


def resolve_provider_keys(config: RunConfig, env_path: str | Path = ".env") -> dict[str, bool]:
    load_env_file(env_path)
    resolved: dict[str, bool] = {}
    for provider in config.providers:
        if not provider.api_key_env:
            resolved[provider.provider] = provider.provider == "local"
            continue
        resolved[provider.provider] = bool(os.getenv(provider.api_key_env))
    return resolved
