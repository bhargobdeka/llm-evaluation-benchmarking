from __future__ import annotations

from pathlib import Path

import yaml

from llm_eval.config import BudgetPolicy, ReliabilityPolicy, RunConfig, RuntimePolicy, SecurityPolicy


def load_policy_yaml(path: str | Path) -> dict:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("Policy file must deserialize to an object")
    return raw


def merge_policy(run_config: RunConfig, policy_path: str | Path = "configs/policy.yaml") -> RuntimePolicy:
    raw = load_policy_yaml(policy_path)
    budget_raw = raw.get("budget", {})
    reliability_raw = raw.get("reliability", {})
    security_raw = raw.get("security", {})

    provider_error = reliability_raw.get("provider_error_rate", {})

    merged_budget = BudgetPolicy(
        max_usd_per_run=float(budget_raw.get("max_usd_per_run", run_config.policy.budget.max_usd_per_run)),
        warn_at_percent=int(budget_raw.get("warn_at_percent", run_config.policy.budget.warn_at_percent)),
        enforce_hard_stop=bool(
            budget_raw.get("enforce_hard_stop", run_config.policy.budget.enforce_hard_stop)
        ),
    )
    merged_reliability = ReliabilityPolicy(
        max_parallel_requests=int(
            reliability_raw.get(
                "max_parallel_requests", run_config.policy.reliability.max_parallel_requests
            )
        ),
        request_timeout_seconds=int(
            reliability_raw.get(
                "request_timeout_seconds", run_config.policy.reliability.request_timeout_seconds
            )
        ),
        retry=run_config.policy.reliability.retry,
        provider_error_rate_window_size_requests=int(
            provider_error.get(
                "window_size_requests",
                run_config.policy.reliability.provider_error_rate_window_size_requests,
            )
        ),
        provider_error_rate_hard_stop_percent=int(
            provider_error.get(
                "hard_stop_percent", run_config.policy.reliability.provider_error_rate_hard_stop_percent
            )
        ),
    )
    merged_security = SecurityPolicy(
        byok_only=bool(security_raw.get("byok_only", run_config.policy.security.byok_only)),
        persist_user_api_keys=bool(
            security_raw.get("persist_user_api_keys", run_config.policy.security.persist_user_api_keys)
        ),
        redact_secrets_in_logs=bool(
            security_raw.get("redact_secrets_in_logs", run_config.policy.security.redact_secrets_in_logs)
        ),
        allowed_secret_env_vars=list(
            security_raw.get(
                "allowed_secret_env_vars", run_config.policy.security.allowed_secret_env_vars
            )
        ),
    )
    return RuntimePolicy(budget=merged_budget, reliability=merged_reliability, security=merged_security)
