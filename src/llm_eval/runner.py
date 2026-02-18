from __future__ import annotations

import hashlib
import json
import random
import re
import time
from dataclasses import dataclass
from typing import Any

from llm_eval.benchmarks.mmlu_subset import MMLUSubsetDataset
from llm_eval.cache import ResponseCache
from llm_eval.config import RunConfig, build_run_manifest, load_env_file
from llm_eval.policy import merge_policy
from llm_eval.providers import InferenceRequest, build_provider_client
from llm_eval.providers.http import ProviderHTTPError
from llm_eval.storage import ArtifactStore

OPTION_RE = re.compile(r"\b([A-Z])\b")


@dataclass
class ExecutionSummary:
    run_id: str
    total_requests: int
    total_errors: int
    provider_metrics: dict[str, dict[str, Any]]


def _finalize_metrics(provider_metrics: dict[str, dict[str, Any]]) -> None:
    for metrics in provider_metrics.values():
        attempted = metrics["attempted"]
        metrics["accuracy"] = (metrics["correct"] / attempted) if attempted else 0.0


def _request_key(
    *,
    provider: str,
    model: str,
    sample_id: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    payload = {
        "provider": provider,
        "model": model,
        "sample_id": sample_id,
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]


def _extract_option_letter(text: str) -> str | None:
    match = OPTION_RE.search(text.upper())
    return match.group(1) if match else None


def _correct_letter(answer_index: int) -> str:
    return chr(65 + answer_index)


def run_evaluation(
    config: RunConfig,
    policy_path: str = "configs/policy.yaml",
    artifacts_root: str = "artifacts",
    env_path: str = ".env",
) -> ExecutionSummary:
    load_env_file(env_path)
    merged_policy = merge_policy(config, policy_path=policy_path)
    config.policy = merged_policy
    manifest = build_run_manifest(config)

    random.seed(config.seed)
    store = ArtifactStore(artifacts_root=artifacts_root, run_id=manifest.run_id)
    cache = ResponseCache(store.run_dir / "cache")
    store.write_manifest(manifest.model_dump())

    if config.benchmark.name != "mmlu_subset":
        raise NotImplementedError("Phase 2 supports mmlu_subset only.")

    dataset = MMLUSubsetDataset(
        config.benchmark.dataset_path,
        max_samples=config.benchmark.max_samples,
    )
    samples = list(dataset.load())

    completed_keys = store.load_completed_keys()
    provider_metrics: dict[str, dict[str, Any]] = {
        provider.provider: {"requests": 0, "errors": 0, "correct": 0, "attempted": 0}
        for provider in config.providers
    }

    total_requests = 0
    total_errors = 0

    for provider_cfg in config.providers:
        client = build_provider_client(
            provider_config=provider_cfg,
            timeout_seconds=config.policy.reliability.request_timeout_seconds,
        )
        for sample in samples:
            prompt = sample.prompt()
            req_key = _request_key(
                provider=provider_cfg.provider,
                model=provider_cfg.model,
                sample_id=sample.sample_id,
                prompt=prompt,
                temperature=provider_cfg.temperature,
                max_tokens=provider_cfg.max_tokens,
            )
            if req_key in completed_keys:
                continue

            provider_metrics[provider_cfg.provider]["requests"] += 1
            provider_metrics[provider_cfg.provider]["attempted"] += 1
            total_requests += 1

            cached = cache.get(req_key)
            if cached is not None:
                response_text = str(cached["text"])
                latency_ms = int(cached.get("latency_ms") or 0)
                usage = cached.get("usage")
            else:
                attempt = 0
                response_text = ""
                latency_ms = 0
                usage = None
                while True:
                    attempt += 1
                    try:
                        response = client.generate(
                            InferenceRequest(
                                prompt=prompt,
                                temperature=provider_cfg.temperature,
                                max_tokens=provider_cfg.max_tokens,
                            )
                        )
                        response_text = response.text
                        latency_ms = response.latency_ms or 0
                        usage = response.usage
                        cache.set(
                            req_key,
                            {
                                "text": response_text,
                                "latency_ms": latency_ms,
                                "usage": usage,
                            },
                        )
                        break
                    except ProviderHTTPError as exc:
                        retryable = (
                            exc.status_code
                            in config.policy.reliability.retry.retryable_status_codes
                        )
                        if attempt < config.policy.reliability.retry.max_attempts and retryable:
                            backoff = config.policy.reliability.retry.backoff_seconds[
                                min(attempt - 1, len(config.policy.reliability.retry.backoff_seconds) - 1)
                            ]
                            time.sleep(backoff)
                            continue
                        provider_metrics[provider_cfg.provider]["errors"] += 1
                        total_errors += 1
                        store.append_error(
                            {
                                "run_id": manifest.run_id,
                                "provider": provider_cfg.provider,
                                "model": provider_cfg.model,
                                "sample_id": sample.sample_id,
                                "request_key": req_key,
                                "error_type": "ProviderHTTPError",
                                "error": str(exc),
                                "attempt": attempt,
                            }
                        )
                        break
                    except Exception as exc:  # noqa: BLE001
                        provider_metrics[provider_cfg.provider]["errors"] += 1
                        total_errors += 1
                        store.append_error(
                            {
                                "run_id": manifest.run_id,
                                "provider": provider_cfg.provider,
                                "model": provider_cfg.model,
                                "sample_id": sample.sample_id,
                                "request_key": req_key,
                                "error_type": type(exc).__name__,
                                "error": str(exc),
                                "attempt": attempt,
                            }
                        )
                        break

            predicted = _extract_option_letter(response_text or "")
            expected = _correct_letter(sample.answer_index)
            is_correct = predicted == expected
            if is_correct:
                provider_metrics[provider_cfg.provider]["correct"] += 1

            store.append_result(
                {
                    "run_id": manifest.run_id,
                    "provider": provider_cfg.provider,
                    "model": provider_cfg.model,
                    "sample_id": sample.sample_id,
                    "category": sample.category,
                    "request_key": req_key,
                    "predicted": predicted,
                    "expected": expected,
                    "is_correct": is_correct,
                    "latency_ms": latency_ms,
                    "usage": usage,
                    "response_text": response_text,
                }
            )

            requests_for_provider = provider_metrics[provider_cfg.provider]["requests"]
            errors_for_provider = provider_metrics[provider_cfg.provider]["errors"]
            if requests_for_provider > 0:
                error_rate_percent = (errors_for_provider / requests_for_provider) * 100
                if (
                    config.policy.budget.enforce_hard_stop
                    and requests_for_provider
                    >= config.policy.reliability.provider_error_rate_window_size_requests
                    and error_rate_percent
                    > config.policy.reliability.provider_error_rate_hard_stop_percent
                ):
                    _finalize_metrics(provider_metrics)
                    summary = ExecutionSummary(
                        run_id=manifest.run_id,
                        total_requests=total_requests,
                        total_errors=total_errors,
                        provider_metrics=provider_metrics,
                    )
                    store.write_summary(
                        {
                            "run_id": summary.run_id,
                            "status": "stopped_due_to_error_rate",
                            "total_requests": summary.total_requests,
                            "total_errors": summary.total_errors,
                            "provider_metrics": summary.provider_metrics,
                        }
                    )
                    return summary

    _finalize_metrics(provider_metrics)

    summary = ExecutionSummary(
        run_id=manifest.run_id,
        total_requests=total_requests,
        total_errors=total_errors,
        provider_metrics=provider_metrics,
    )
    store.write_summary(
        {
            "run_id": summary.run_id,
            "status": "completed",
            "total_requests": summary.total_requests,
            "total_errors": summary.total_errors,
            "provider_metrics": summary.provider_metrics,
        }
    )
    return summary
